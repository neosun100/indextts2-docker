"""
RAM-based Speaker Embedding Cache Manager
内存缓存管理器 - 将embedding缓存在RAM中以加速访问
"""
import os
import json
import hashlib
import pickle
from pathlib import Path
from typing import Optional, Dict, Any


class SpeakerCacheRAM:
    def __init__(self, cache_dir: str = "/app/outputs/speaker_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存字典
        self.ram_cache = {}  # {speaker_id: embedding_dict}
        
        # 索引文件
        self.index_file = self.cache_dir / "index.json"
        self.index = self._load_index()
        
        # 预加载所有embedding到内存
        self._preload_all_embeddings()
    
    def _load_index(self) -> Dict[str, Any]:
        """加载缓存索引"""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_index(self):
        """保存缓存索引"""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def _compute_md5(self, audio_path: str) -> str:
        """计算音频文件的MD5"""
        md5_hash = hashlib.md5()
        with open(audio_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
    def _preload_all_embeddings(self):
        """预加载所有已缓存的embedding到内存"""
        for md5, info in self.index.items():
            speaker_id = info["speaker_id"]
            embedding_path = self.cache_dir / f"{speaker_id}.pkl"
            
            if embedding_path.exists():
                with open(embedding_path, 'rb') as f:
                    self.ram_cache[speaker_id] = pickle.load(f)
                print(f"[RAM Cache] Preloaded {speaker_id} into memory")
    
    def upload_speaker(self, audio_path: str, speaker_name: Optional[str] = None) -> Dict[str, str]:
        """上传说话人音频并缓存embedding到内存"""
        md5 = self._compute_md5(audio_path)
        
        # 检查是否已存在
        if md5 in self.index:
            speaker_id = self.index[md5]["speaker_id"]
            return {
                "speaker_id": speaker_id,
                "md5": md5,
                "status": "cached",
                "message": "Speaker already in RAM cache"
            }
        
        # 生成新的speaker_id
        speaker_id = f"spk_{md5[:8]}"
        
        # 复制音频文件到缓存目录
        audio_cache_path = self.cache_dir / f"{speaker_id}.wav"
        import shutil
        shutil.copy(audio_path, audio_cache_path)
        
        # 更新索引
        self.index[md5] = {
            "speaker_id": speaker_id,
            "speaker_name": speaker_name or speaker_id,
            "audio_path": str(audio_cache_path),
            "md5": md5,
            "embedding_cached": False
        }
        self._save_index()
        
        return {
            "speaker_id": speaker_id,
            "md5": md5,
            "status": "new",
            "message": "New speaker uploaded, will cache to RAM on first use"
        }
    
    def get_speaker_audio(self, speaker_id: str) -> Optional[str]:
        """根据speaker_id获取音频路径"""
        for md5, info in self.index.items():
            if info["speaker_id"] == speaker_id:
                return info["audio_path"]
        return None
    
    def cache_embedding(self, speaker_id: str, embedding_dict: Dict[str, Any]):
        """缓存embedding到内存和磁盘"""
        # 保存到内存
        self.ram_cache[speaker_id] = embedding_dict
        
        # 同时保存到磁盘（持久化）
        embedding_path = self.cache_dir / f"{speaker_id}.pkl"
        with open(embedding_path, 'wb') as f:
            pickle.dump(embedding_dict, f)
        
        # 更新索引
        for md5, info in self.index.items():
            if info["speaker_id"] == speaker_id:
                info["embedding_cached"] = True
                self._save_index()
                break
        
        print(f"[RAM Cache] Cached {speaker_id} to memory and disk")
    
    def get_embedding(self, speaker_id: str) -> Optional[Dict[str, Any]]:
        """从内存获取embedding（极快）"""
        return self.ram_cache.get(speaker_id)
    
    def list_speakers(self) -> list:
        """列出所有缓存的说话人"""
        speakers = []
        for md5, info in self.index.items():
            speakers.append({
                "speaker_id": info["speaker_id"],
                "speaker_name": info["speaker_name"],
                "cached_in_ram": info["speaker_id"] in self.ram_cache,
                "md5": md5
            })
        return speakers
    
    def delete_speaker(self, speaker_id: str) -> bool:
        """删除说话人缓存"""
        # 从内存删除
        if speaker_id in self.ram_cache:
            del self.ram_cache[speaker_id]
        
        # 从磁盘删除
        audio_path = self.cache_dir / f"{speaker_id}.wav"
        embedding_path = self.cache_dir / f"{speaker_id}.pkl"
        
        if audio_path.exists():
            audio_path.unlink()
        if embedding_path.exists():
            embedding_path.unlink()
        
        # 从索引删除
        md5_to_delete = None
        for md5, info in self.index.items():
            if info["speaker_id"] == speaker_id:
                md5_to_delete = md5
                break
        
        if md5_to_delete:
            del self.index[md5_to_delete]
            self._save_index()
            return True
        
        return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "total_speakers": len(self.index),
            "ram_cached": len(self.ram_cache),
            "cache_dir": str(self.cache_dir)
        }
