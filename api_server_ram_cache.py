"""
API Server with RAM Cache Support
支持内存缓存的API服务器
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import torch
import torchaudio
import uuid
from pathlib import Path
from speaker_cache_ram import SpeakerCacheRAM

app = FastAPI(title="IndexTTS2 API with RAM Cache", version="2.1")

# 全局变量
tts = None
cache_manager = None


class TTSRequest(BaseModel):
    text: str
    spk_audio_prompt: Optional[str] = None
    emo_audio_prompt: Optional[str] = None
    emo_vector: Optional[List[float]] = None
    emo_alpha: float = 1.0
    disable_cache: bool = False


class TTSCachedRequest(BaseModel):
    text: str
    speaker_id: str
    emo_vector: Optional[List[float]] = None
    emo_alpha: float = 1.0


class UploadSpeakerRequest(BaseModel):
    audio_path: str
    speaker_name: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    global tts, cache_manager
    
    print("🚀 Initializing IndexTTS2 with RAM Cache...")
    
    from indextts.infer_v2 import IndexTTS2
    tts = IndexTTS2(device="cuda")
    
    cache_manager = SpeakerCacheRAM(cache_dir="/app/outputs/speaker_cache")
    
    print("✅ IndexTTS2 with RAM Cache initialized")
    print(f"📊 Cache stats: {cache_manager.get_cache_stats()}")


@app.post("/tts")
async def synthesize(request: TTSRequest):
    """标准TTS接口（支持禁用缓存）"""
    if not request.spk_audio_prompt:
        raise HTTPException(status_code=400, detail="spk_audio_prompt is required")
    
    # 如果禁用缓存，清空IndexTTS2的内部缓存
    if request.disable_cache:
        tts.cache_spk_cond = None
        tts.cache_s2mel_style = None
        tts.cache_s2mel_prompt = None
        tts.cache_spk_audio_prompt = None
        tts.cache_mel = None
        torch.cuda.empty_cache()
    
    audio = tts.infer(
        text=request.text,
        spk_audio_prompt=request.spk_audio_prompt,
        emo_audio_prompt=request.emo_audio_prompt,
        emo_vector=request.emo_vector,
        emo_alpha=request.emo_alpha
    )
    
    output_path = Path("/app/outputs") / f"tts_{uuid.uuid4()}.wav"
    torchaudio.save(str(output_path), audio.unsqueeze(0).cpu(), 22050)
    
    with open(output_path, "rb") as f:
        audio_data = f.read()
    
    return Response(content=audio_data, media_type="audio/wav")


@app.post("/tts_cached")
async def synthesize_cached(request: TTSCachedRequest):
    """使用内存缓存的TTS接口"""
    # 从内存获取embedding
    cached_emb = cache_manager.get_embedding(request.speaker_id)
    
    if cached_emb:
        # 从内存加载embedding到IndexTTS2
        tts.cache_spk_cond = cached_emb["spk_cond"]
        tts.cache_s2mel_style = cached_emb["s2mel_style"]
        tts.cache_s2mel_prompt = cached_emb["s2mel_prompt"]
        tts.cache_mel = cached_emb["mel"]
        tts.cache_spk_audio_prompt = cached_emb["audio_path"]
        print(f"[RAM Cache] Loaded {request.speaker_id} from memory")
    else:
        # 首次使用，需要提取embedding
        audio_path = cache_manager.get_speaker_audio(request.speaker_id)
        if not audio_path:
            raise HTTPException(status_code=404, detail=f"Speaker {request.speaker_id} not found")
        
        # 提取embedding
        audio, sr = tts._load_and_cut_audio(audio_path, 15, False)
        audio_22k = torchaudio.transforms.Resample(sr, 22050)(audio)
        audio_16k = torchaudio.transforms.Resample(sr, 16000)(audio)
        
        inputs = tts.extract_features(audio_16k, sampling_rate=16000, return_tensors="pt")
        input_features = inputs["input_features"].to(tts.device)
        attention_mask = inputs["attention_mask"].to(tts.device)
        spk_cond_emb = tts.get_emb(input_features, attention_mask)
        
        _, S_ref = tts.semantic_codec.quantize(spk_cond_emb)
        ref_mel = tts.mel_fn(audio_22k.to(spk_cond_emb.device).float())
        ref_target_lengths = torch.LongTensor([ref_mel.size(2)]).to(ref_mel.device)
        feat = torchaudio.compliance.kaldi.fbank(audio_16k.to(ref_mel.device),
                                                 num_mel_bins=80,
                                                 dither=0,
                                                 sample_frequency=16000)
        feat = feat - feat.mean(dim=0, keepdim=True)
        style = tts.campplus_model(feat.unsqueeze(0))
        
        prompt_condition = tts.s2mel.models['length_regulator'](S_ref,
                                                                ylens=ref_target_lengths,
                                                                n_quantizers=3,
                                                                f0=None)[0]
        
        # 缓存到内存
        embedding_dict = {
            "spk_cond": spk_cond_emb,
            "s2mel_style": style,
            "s2mel_prompt": prompt_condition,
            "mel": ref_mel,
            "audio_path": audio_path
        }
        cache_manager.cache_embedding(request.speaker_id, embedding_dict)
        
        # 设置到IndexTTS2
        tts.cache_spk_cond = spk_cond_emb
        tts.cache_s2mel_style = style
        tts.cache_s2mel_prompt = prompt_condition
        tts.cache_mel = ref_mel
        tts.cache_spk_audio_prompt = audio_path
    
    # 合成语音
    audio = tts.infer(
        text=request.text,
        spk_audio_prompt=tts.cache_spk_audio_prompt,
        emo_vector=request.emo_vector,
        emo_alpha=request.emo_alpha
    )
    
    output_path = Path("/app/outputs") / f"tts_{uuid.uuid4()}.wav"
    torchaudio.save(str(output_path), audio.unsqueeze(0).cpu(), 22050)
    
    with open(output_path, "rb") as f:
        audio_data = f.read()
    
    return Response(content=audio_data, media_type="audio/wav")


@app.post("/upload_speaker")
async def upload_speaker(request: UploadSpeakerRequest):
    """上传说话人音频"""
    result = cache_manager.upload_speaker(request.audio_path, request.speaker_name)
    return result


@app.get("/speakers")
async def list_speakers():
    """列出所有缓存的说话人"""
    return cache_manager.list_speakers()


@app.delete("/speakers/{speaker_id}")
async def delete_speaker(speaker_id: str):
    """删除说话人缓存"""
    success = cache_manager.delete_speaker(speaker_id)
    if success:
        return {"message": f"Speaker {speaker_id} deleted"}
    else:
        raise HTTPException(status_code=404, detail=f"Speaker {speaker_id} not found")


@app.get("/cache_stats")
async def get_cache_stats():
    """获取缓存统计信息"""
    return cache_manager.get_cache_stats()


@app.get("/health")
async def health_check():
    return {"status": "healthy", "cache_type": "RAM"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
