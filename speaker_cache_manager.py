"""
Speaker Embedding Cache Manager
持久化缓存管理，支持音频上传、MD5去重、ID引用
"""
import os
import json
import hashlib
import pickle
from pathlib import Path
from typing import Optional, Dict, Any
import torch


class SpeakerCacheManager:
    def __init__(self, cache_dir: str = "/app/outputs/speaker_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 缓存索引文件
        self.index_file = self.cache_dir / "index.json"
        self.index = self._load_index()
    
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
    
    def upload_speaker(self, audio_path: str, speaker_name: Optional[str] = None) -> Dict[str, str]:
        """
        上传说话人音频并缓存embedding
        
        Args:
            audio_path: 音频文件路径
            speaker_name: 可选的说话人名称
        
        Returns:
            {
                "speaker_id": "spk_abc123",
                "md5": "...",
                "status": "cached" | "new",
                "message": "..."
            }
        """
        # 计算MD5
        md5 = self._compute_md5(audio_path)
        
        # 检查是否已存在
        if md5 in self.index:
            return {
                "speaker_id": self.index[md5]["speaker_id"],
                "md5": md5,
                "status": "cached",
                "message": "Speaker already cached, using existing embedding"
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
            "embedding_cached": False  # 标记embedding尚未提取
        }
        self._save_index()
        
        return {
            "speaker_id": speaker_id,
            "md5": md5,
            "status": "new",
            "message": "New speaker uploaded, will extract embedding on first use"
        }
    
    def get_speaker_audio(self, speaker_id: str) -> Optional[str]:
        """根据speaker_id获取音频路径"""
        for md5, info in self.index.items():
            if info["speaker_id"] == speaker_id:
                return info["audio_path"]
        return None
    
    def cache_embedding(self, speaker_id: str, embeddings: Dict[str, torch.Tensor]):
        """
        缓存speaker embedding到磁盘
        
        Args:
            speaker_id: 说话人ID
            embeddings: {
                "spk_cond": tensor,
                "s2mel_style": tensor,
                "s2mel_prompt": tensor,
                "mel": tensor
            }
        """
        # 找到对应的MD5
        md5 = None
        for m, info in self.index.items():
            if info["speaker_id"] == speaker_id:
                md5 = m
                break
        
        if md5 is None:
            return
        
        # 保存embedding到磁盘
        embedding_path = self.cache_dir / f"{speaker_id}_emb.pkl"
        with open(embedding_path, 'wb') as f:
            pickle.dump(embeddings, f)
        
        # 更新索引
        self.index[md5]["embedding_cached"] = True
        self.index[md5]["embedding_path"] = str(embedding_path)
        self._save_index()
    
    def load_embedding(self, speaker_id: str) -> Optional[Dict[str, torch.Tensor]]:
        """从磁盘加载speaker embedding"""
        for md5, info in self.index.items():
            if info["speaker_id"] == speaker_id and info.get("embedding_cached"):
                embedding_path = info.get("embedding_path")
                if embedding_path and os.path.exists(embedding_path):
                    with open(embedding_path, 'rb') as f:
                        return pickle.load(f)
        return None
    
    def list_speakers(self) -> list:
        """列出所有缓存的说话人"""
        speakers = []
        for md5, info in self.index.items():
            speakers.append({
                "speaker_id": info["speaker_id"],
                "speaker_name": info["speaker_name"],
                "md5": md5,
                "embedding_cached": info.get("embedding_cached", False)
            })
        return speakers
    
    def delete_speaker(self, speaker_id: str) -> bool:
        """删除说话人缓存"""
        md5_to_delete = None
        for md5, info in self.index.items():
            if info["speaker_id"] == speaker_id:
                md5_to_delete = md5
                break
        
        if md5_to_delete is None:
            return False
        
        # 删除文件
        info = self.index[md5_to_delete]
        if os.path.exists(info["audio_path"]):
            os.remove(info["audio_path"])
        
        embedding_path = info.get("embedding_path")
        if embedding_path and os.path.exists(embedding_path):
            os.remove(embedding_path)
        
        # 从索引中删除
        del self.index[md5_to_delete]
        self._save_index()
        
        return True
