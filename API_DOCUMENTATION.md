# IndexTTS2 API 文档

## ✅ 确认信息

**是的，Docker 容器包含完整的 API 和 Swagger 文档！**

## 📡 API 服务

### 端口配置

- **Flask API**: 端口 `8002`
- **Gradio WebUI**: 端口 `7860` (webui_enhanced.py)

### 启动容器

```bash
docker run -d --name indextts2 \
  --gpus all \
  -p 8002:8002 \
  -p 7860:7860 \
  neosun/indextts2:v2.1-turbo
```

## 📚 Swagger 文档

### 访问地址

```
http://localhost:8002/docs/
```

### API 信息

- **标题**: IndexTTS2 API
- **版本**: 2.0.0
- **描述**: IndexTTS2 零样本语音合成 API - 支持声音克隆和情感控制

## 🔌 可用端点

### 1. 健康检查

```
GET /health
```

**响应示例**:
```json
{
  "status": "ok"
}
```

### 2. 语音合成

```
POST /tts
```

**请求参数**:

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `text` | string | ✅ | 要合成的文本内容 |
| `spk_audio_prompt` | string | ✅ | 说话人参考音频路径 |
| `emo_audio_prompt` | string | ❌ | 情感参考音频路径 |
| `emo_alpha` | float | ❌ | 情感强度 (0.0-1.0)，默认 1.0 |
| `emo_vector` | array[8] | ❌ | 8维情感向量 |
| `use_emo_text` | boolean | ❌ | 是否启用文本情感识别 |
| `emo_text` | string | ❌ | 独立的情感文本 |
| `use_random` | boolean | ❌ | 是否启用随机采样 |

**情感向量说明**:
```
[happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]
```

**响应**: 返回 WAV 音频文件

## 📝 使用示例

### 示例 1: 基础合成

```bash
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，这是一个测试。",
    "spk_audio_prompt": "/app/examples/voice_01.wav"
  }' \
  -o output.wav
```

### 示例 2: 情感向量控制

```bash
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "哇塞！这个太棒了！",
    "spk_audio_prompt": "/app/examples/voice_01.wav",
    "emo_vector": [0.8, 0, 0, 0, 0, 0, 0.5, 0],
    "emo_alpha": 0.9
  }' \
  -o output.wav
```

### 示例 3: 情感音频参考

```bash
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "今天天气真好。",
    "spk_audio_prompt": "/app/examples/voice_01.wav",
    "emo_audio_prompt": "/app/examples/emo_sad.wav",
    "emo_alpha": 0.8
  }' \
  -o output.wav
```

### 示例 4: Python 调用

```python
import requests

url = "http://localhost:8002/tts"
payload = {
    "text": "你好，这是IndexTTS2的测试。",
    "spk_audio_prompt": "/app/examples/voice_01.wav"
}

response = requests.post(url, json=payload)
if response.status_code == 200:
    with open("output.wav", "wb") as f:
        f.write(response.content)
    print("✅ 合成成功！")
else:
    print(f"❌ 失败: {response.status_code}")
```

## 🎯 预置示例音频

容器内包含以下示例音频（位于 `/app/examples/`）：

- `voice_01.wav` ~ `voice_12.wav` - 12个不同说话人的参考音频
- `emo_sad.wav` - 悲伤情感参考
- `emo_hate.wav` - 愤怒情感参考

## 🌐 Swagger UI 功能

访问 `http://localhost:8002/docs/` 可以：

1. ✅ 查看完整的 API 文档
2. ✅ 在线测试 API 端点
3. ✅ 查看请求/响应示例
4. ✅ 下载 OpenAPI 规范 (swagger.json)

## 📦 完整服务

每个 Docker 容器包含：

1. **Flask API** (端口 8002) - RESTful API 服务
2. **Swagger UI** (端口 8002/docs/) - 交互式 API 文档
3. **Gradio WebUI** (端口 7860) - 可视化界面

## 🔗 相关链接

- Swagger JSON: `http://localhost:8002/swagger.json`
- API 健康检查: `http://localhost:8002/health`
- Gradio WebUI: `http://localhost:7860/`

---

**所有 Docker 镜像都包含完整的 API 和 Swagger 文档！**
