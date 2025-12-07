# Speaker Cache Management Guide

## 🎯 功能概述

新增的Speaker缓存管理系统，实现了：
- ✅ 音频上传自动MD5去重
- ✅ Speaker embedding持久化缓存
- ✅ Speaker ID引用机制
- ✅ 跳过重复的embedding提取
- ✅ 加速语音合成（节省1.5-2秒）

## 🚀 快速开始

### 1. 启动增强版API服务器

```bash
# 使用新的API服务器
docker run -d \
  --name indextts2-cached \
  --gpus all \
  -p 8002:8002 \
  -p 7860:7860 \
  -v /tmp/indextts2-outputs:/app/outputs \
  neosun/indextts2:v2.1-cuda \
  bash -c "uv run python3 api_server_cached.py & uv run webui_enhanced.py --server_name 0.0.0.0 --server_port 7860 --use_fp16"
```

### 2. 上传说话人音频

```bash
# 上传音频并自动缓存embedding
curl -X POST http://localhost:8002/upload_speaker \
  -F "audio=@my_voice.wav" \
  -F "speaker_name=My Voice"

# 响应示例
{
  "speaker_id": "spk_abc12345",
  "md5": "a1b2c3d4e5f6...",
  "status": "new",
  "message": "Speaker uploaded and embedding cached successfully"
}
```

**重要**：如果上传相同音频（MD5相同），会直接返回已缓存的speaker_id，不会重复提取embedding。

### 3. 使用speaker_id合成语音

```bash
# 使用缓存的speaker进行合成（快速）
curl -X POST http://localhost:8002/tts_cached \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，这是使用缓存speaker的测试。",
    "speaker_id": "spk_abc12345",
    "emo_vector": [0.8, 0, 0, 0, 0, 0, 0.5, 0],
    "emo_alpha": 0.9
  }' \
  -o output.wav
```

### 4. 查看所有缓存的说话人

```bash
curl http://localhost:8002/speakers

# 响应示例
{
  "speakers": [
    {
      "speaker_id": "spk_abc12345",
      "speaker_name": "My Voice",
      "md5": "a1b2c3d4e5f6...",
      "embedding_cached": true
    },
    {
      "speaker_id": "spk_def67890",
      "speaker_name": "Another Voice",
      "md5": "f6e5d4c3b2a1...",
      "embedding_cached": true
    }
  ],
  "count": 2
}
```

### 5. 删除说话人缓存

```bash
curl -X DELETE http://localhost:8002/speakers/spk_abc12345
```

## 📊 性能对比

### 传统方式（每次上传音频）

```bash
# 第一次请求
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "第一句话",
    "spk_audio_prompt": "/app/examples/voice_01.wav"
  }'
# 耗时: ~6秒（提取embedding + 推理）

# 第二次请求（相同音频）
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "第二句话",
    "spk_audio_prompt": "/app/examples/voice_01.wav"
  }'
# 耗时: ~4.5秒（使用内存缓存）
```

### 新方式（使用speaker_id）

```bash
# 上传一次（仅需一次）
curl -X POST http://localhost:8002/upload_speaker \
  -F "audio=@my_voice.wav" \
  -F "speaker_name=My Voice"
# 耗时: ~6秒（提取并持久化embedding）
# 返回: {"speaker_id": "spk_abc12345", ...}

# 后续所有请求（无需上传音频）
curl -X POST http://localhost:8002/tts_cached \
  -H "Content-Type: application/json" \
  -d '{"text": "任意文本", "speaker_id": "spk_abc12345"}'
# 耗时: ~4.5秒（直接加载缓存的embedding）

# 容器重启后仍然有效！
docker restart indextts2-cached
curl -X POST http://localhost:8002/tts_cached \
  -H "Content-Type: application/json" \
  -d '{"text": "重启后的文本", "speaker_id": "spk_abc12345"}'
# 耗时: ~4.5秒（从磁盘加载embedding到GPU）
```

## 🎯 优势总结

| 特性 | 传统方式 | 新方式（Speaker Cache） |
|------|---------|----------------------|
| 首次使用 | 6秒 | 6秒（上传+缓存） |
| 后续使用 | 4.5秒（内存缓存） | 4.5秒（磁盘缓存） |
| 容器重启后 | 6秒（重新提取） | 4.5秒（加载缓存） ✅ |
| 音频上传 | 每次都要 | 仅一次 ✅ |
| MD5去重 | ❌ | ✅ |
| 管理界面 | ❌ | ✅ |

## 💡 使用场景

### 场景1：批量生成（同一说话人）

```bash
# 1. 上传一次
curl -X POST http://localhost:8002/upload_speaker \
  -F "audio=@speaker.wav" \
  -F "speaker_name=Narrator"

# 2. 批量生成（无需重复上传）
for text in "第一句" "第二句" "第三句"; do
  curl -X POST http://localhost:8002/tts_cached \
    -H "Content-Type: application/json" \
    -d "{\"text\": \"$text\", \"speaker_id\": \"spk_abc12345\"}" \
    -o "output_${text}.wav"
done
```

### 场景2：多说话人管理

```bash
# 上传多个说话人
curl -X POST http://localhost:8002/upload_speaker \
  -F "audio=@narrator.wav" -F "speaker_name=Narrator"
# 返回: spk_abc12345

curl -X POST http://localhost:8002/upload_speaker \
  -F "audio=@character1.wav" -F "speaker_name=Character 1"
# 返回: spk_def67890

curl -X POST http://localhost:8002/upload_speaker \
  -F "audio=@character2.wav" -F "speaker_name=Character 2"
# 返回: spk_ghi11121

# 使用不同说话人生成对话
curl -X POST http://localhost:8002/tts_cached \
  -d '{"text": "旁白：故事开始了", "speaker_id": "spk_abc12345"}'

curl -X POST http://localhost:8002/tts_cached \
  -d '{"text": "角色1：你好！", "speaker_id": "spk_def67890"}'

curl -X POST http://localhost:8002/tts_cached \
  -d '{"text": "角色2：很高兴见到你！", "speaker_id": "spk_ghi11121"}'
```

### 场景3：情感控制

```bash
# 同一说话人，不同情感
curl -X POST http://localhost:8002/tts_cached \
  -d '{
    "text": "太棒了！",
    "speaker_id": "spk_abc12345",
    "emo_vector": [0.9, 0, 0, 0, 0, 0, 0.5, 0],
    "emo_alpha": 0.9
  }'

curl -X POST http://localhost:8002/tts_cached \
  -d '{
    "text": "这太糟糕了...",
    "speaker_id": "spk_abc12345",
    "emo_vector": [0, 0, 0.8, 0, 0, 0.6, 0, 0],
    "emo_alpha": 0.9
  }'
```

## 🔧 技术细节

### 缓存存储结构

```
/app/outputs/speaker_cache/
├── index.json                    # 索引文件
├── spk_abc12345.wav             # 音频文件
├── spk_abc12345_emb.pkl         # Embedding缓存
├── spk_def67890.wav
└── spk_def67890_emb.pkl
```

### index.json 格式

```json
{
  "a1b2c3d4e5f6...": {
    "speaker_id": "spk_abc12345",
    "speaker_name": "My Voice",
    "audio_path": "/app/outputs/speaker_cache/spk_abc12345.wav",
    "md5": "a1b2c3d4e5f6...",
    "embedding_cached": true,
    "embedding_path": "/app/outputs/speaker_cache/spk_abc12345_emb.pkl"
  }
}
```

### Embedding缓存内容

```python
{
  "spk_cond": torch.Tensor,      # [1, seq_len, 1024]
  "s2mel_style": torch.Tensor,   # [1, 192]
  "s2mel_prompt": torch.Tensor,  # [1, seq_len, dim]
  "mel": torch.Tensor            # [1, 80, frames]
}
```

## ⚠️ 注意事项

1. **磁盘空间**：每个说话人约占用 5-10MB（音频+embedding）
2. **首次加载**：容器重启后首次使用需要从磁盘加载到GPU（~0.1秒）
3. **MD5去重**：相同音频文件会自动识别，不会重复缓存
4. **向后兼容**：原有的 `/tts` 接口仍然可用

## 🔄 迁移指南

### 从旧API迁移到新API

**旧方式**：
```bash
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好",
    "spk_audio_prompt": "/app/examples/voice_01.wav"
  }'
```

**新方式**：
```bash
# 1. 首次：上传并获取speaker_id
curl -X POST http://localhost:8002/upload_speaker \
  -F "audio=@voice_01.wav" \
  -F "speaker_name=Voice 01"
# 返回: {"speaker_id": "spk_abc12345"}

# 2. 后续：使用speaker_id
curl -X POST http://localhost:8002/tts_cached \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好",
    "speaker_id": "spk_abc12345"
  }'
```

## 📚 API参考

### POST /upload_speaker
上传说话人音频并缓存embedding

**请求**：
- `audio`: 音频文件（multipart/form-data）
- `speaker_name`: 说话人名称（可选）

**响应**：
```json
{
  "speaker_id": "spk_abc12345",
  "md5": "...",
  "status": "new" | "cached",
  "message": "..."
}
```

### GET /speakers
列出所有缓存的说话人

**响应**：
```json
{
  "speakers": [...],
  "count": 2
}
```

### POST /tts_cached
使用缓存的speaker合成语音

**请求**：
```json
{
  "text": "文本内容",
  "speaker_id": "spk_abc12345",
  "emo_vector": [0.8, 0, 0, 0, 0, 0, 0.5, 0],
  "emo_alpha": 0.9
}
```

**响应**：音频文件（audio/wav）

### DELETE /speakers/{speaker_id}
删除说话人缓存

**响应**：
```json
{
  "message": "Speaker deleted successfully"
}
```
