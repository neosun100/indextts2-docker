# IndexTTS2 API 完整使用指南

## 📚 核心概念

### text (文本)
**要合成的语音内容** - 你想让AI说什么话

示例:
- "你好，欢迎使用IndexTTS2"
- "今天天气真不错"
- "这是一段测试文本"

### speaker_id (说话人ID)
**说话人的声音特征标识** - 决定用谁的声音来说这段话

获取方式: 上传音频文件后系统自动生成

---

## 🔄 完整工作流程

### 步骤1: 上传说话人音频，获取speaker_id

```bash
# 上传音频文件
curl -X POST http://localhost:8002/upload_speaker \
  -F "audio=@/path/to/your/voice.wav" \
  -F "speaker_name=张三"

# 返回结果:
{
  "speaker_id": "spk_20cfdc63",     # ← 这就是speaker_id
  "md5": "20cfdc63ddf83b56...",
  "status": "new",
  "message": "Speaker uploaded and embedding cached"
}
```

**说明**:
- `audio`: 你的音频文件（3-10秒的说话人声音样本）
- `speaker_name`: 可选，给这个声音起个名字
- 返回的 `speaker_id` 就是你需要的ID

### 步骤2: 查看所有已缓存的说话人

```bash
curl http://localhost:8002/speakers

# 返回结果:
{
  "count": 2,
  "speakers": [
    {
      "speaker_id": "spk_20cfdc63",
      "speaker_name": "张三",
      "md5": "20cfdc63ddf83b56...",
      "embedding_cached": true
    },
    {
      "speaker_id": "spk_a1b2c3d4",
      "speaker_name": "李四",
      "md5": "a1b2c3d4e5f6...",
      "embedding_cached": true
    }
  ]
}
```

### 步骤3: 使用speaker_id生成语音

```bash
# 方式A: 使用缓存API（推荐，更快）
curl -X POST http://localhost:8002/tts_cached \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，我是张三",
    "speaker_id": "spk_20cfdc63"
  }' \
  -o output.wav

# 方式B: 传统API（每次都传音频路径）
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，我是张三",
    "spk_audio_prompt": "/app/examples/voice_01.wav"
  }' \
  -o output.wav
```

---

## 🎯 实际使用场景

### 场景1: 第一次使用某个声音

```bash
# 1. 上传音频
curl -X POST http://localhost:8002/upload_speaker \
  -F "audio=@boss_voice.wav" \
  -F "speaker_name=老板"

# 返回: {"speaker_id": "spk_abc123", ...}

# 2. 使用这个声音生成语音
curl -X POST http://localhost:8002/tts_cached \
  -H "Content-Type: application/json" \
  -d '{
    "text": "各位同事大家好，今天开会讨论项目进度",
    "speaker_id": "spk_abc123"
  }' \
  -o meeting.wav
```

### 场景2: 重复使用已上传的声音

```bash
# 不需要再上传，直接用speaker_id
curl -X POST http://localhost:8002/tts_cached \
  -H "Content-Type: application/json" \
  -d '{
    "text": "明天继续开会",
    "speaker_id": "spk_abc123"
  }' \
  -o meeting2.wav
```

### 场景3: 忘记了speaker_id

```bash
# 查看所有已上传的说话人
curl http://localhost:8002/speakers | jq '.'

# 找到你需要的speaker_id，然后使用
```

---

## 🚀 性能优化参数（可选）

```bash
# 使用优化参数，速度提升26%
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "这是一段测试文本",
    "spk_audio_prompt": "/app/examples/voice_01.wav",
    "num_beams": 1,
    "do_sample": false,
    "top_k": 10
  }' \
  -o output_fast.wav
```

**优化参数说明**:
- `num_beams: 1` - 降低beam search（最重要）
- `do_sample: false` - 使用贪婪解码
- `top_k: 10` - 减少采样范围

**效果**: 从7.8秒降到5.7秒（提升26.6%）

---

## 📝 Python 示例

```python
import requests

API_BASE = "http://localhost:8002"

# 1. 上传说话人音频
with open("my_voice.wav", "rb") as f:
    response = requests.post(
        f"{API_BASE}/upload_speaker",
        files={"audio": f},
        data={"speaker_name": "我的声音"}
    )
    result = response.json()
    speaker_id = result["speaker_id"]
    print(f"Speaker ID: {speaker_id}")

# 2. 使用speaker_id生成语音
response = requests.post(
    f"{API_BASE}/tts_cached",
    json={
        "text": "你好，这是用我的声音合成的语音",
        "speaker_id": speaker_id
    }
)

# 3. 保存音频
with open("output.wav", "wb") as f:
    f.write(response.content)
    print("✅ 音频已生成")
```

---

## 🎭 情感控制（高级功能）

```bash
# 添加情感向量
curl -X POST http://localhost:8002/tts_cached \
  -H "Content-Type: application/json" \
  -d '{
    "text": "太棒了！",
    "speaker_id": "spk_abc123",
    "emo_vector": [0.8, 0, 0, 0, 0, 0, 0.5, 0],
    "emo_alpha": 0.9
  }' \
  -o happy.wav
```

**情感向量格式**: `[happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]`

---

## ❓ 常见问题

### Q1: speaker_id是什么？
A: 说话人的唯一标识符，格式如 `spk_20cfdc63`，由系统根据音频的MD5生成。

### Q2: text是什么？
A: 你想要合成的语音内容，就是让AI说的话。

### Q3: 如何获取speaker_id？
A: 通过 `/upload_speaker` 上传音频后，系统返回的 `speaker_id` 字段。

### Q4: 可以重复使用speaker_id吗？
A: 可以！上传一次后，可以无限次使用该speaker_id生成不同的语音。

### Q5: 如何查看所有已上传的说话人？
A: 访问 `GET /speakers` 端点。

### Q6: speaker_id会过期吗？
A: 不会，除非删除容器或清空缓存目录。

---

## 📊 API对比

| 特性 | /tts | /tts_cached |
|------|------|-------------|
| 输入 | 音频文件路径 | speaker_id |
| 首次速度 | 正常 | 正常 |
| 后续速度 | 正常 | 稍快（缓存命中） |
| 使用场景 | 临时使用 | 重复使用同一声音 |
| 推荐度 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🎯 最佳实践

1. **首次使用**: 用 `/upload_speaker` 上传音频，获取speaker_id
2. **后续使用**: 用 `/tts_cached` + speaker_id 生成语音
3. **性能优化**: 添加 `num_beams=1, do_sample=false` 参数
4. **管理声音**: 定期查看 `/speakers` 了解已缓存的说话人

---

## 📁 内置示例音频

容器内已有12个示例说话人，可直接使用：

```bash
# 使用内置音频（不需要上传）
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好",
    "spk_audio_prompt": "/app/examples/voice_01.wav"
  }' \
  -o test.wav

# 可用的内置音频:
# /app/examples/voice_01.wav ~ voice_12.wav
```
