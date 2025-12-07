# IndexTTS2 Docker - 零样本语音合成

[English](README.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

[![Docker Hub](https://img.shields.io/badge/Docker-Hub-blue?logo=docker)](https://hub.docker.com/r/neosun/indextts2)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/neosun100/indextts2-docker?style=social)](https://github.com/neosun100/indextts2-docker)

生产就绪的 IndexTTS2 Docker 镜像 - 支持情感表达和时长控制的突破性自回归零样本语音合成系统。

## ✨ 功能特性

- 🎯 **零样本声音克隆** - 仅需 3-10 秒音频即可克隆任何声音
- 🎭 **情感控制** - 8 维情感向量（开心、愤怒、悲伤、害怕、厌恶、忧郁、惊讶、平静）
- 🚀 **多种优化** - CUDA 内核、DeepSpeed、FP16 支持
- 📦 **一体化 Docker** - 预构建镜像包含所有模型
- 🌐 **双重界面** - REST API + Gradio WebUI
- 📚 **Swagger 文档** - 交互式 API 文档

## 🏆 性能测试结果

在 NVIDIA L40S GPU 上测试 80 个用例（4 个版本 × 4 个场景 × 5 次运行）：

| 版本 | 中文短文本 | 中文长文本 | 英文短文本 | 英文长文本 | 成功率 |
|------|-----------|-----------|-----------|-----------|--------|
| v2.0-production | 6.42秒 | 27.96秒 | 7.60秒 | **35.36秒** ⭐ | 100% |
| v2.1-cuda | **6.13秒** ⭐ | **26.88秒** ⭐ | 7.48秒 | 35.72秒 | 100% |
| v2.1-deepspeed | 6.62秒 | 28.58秒 | 7.51秒 | 36.46秒 | 100% |
| v2.1-turbo | 6.41秒 | 28.34秒 | 7.70秒 | 35.48秒 | 100% |

**推荐选择：**
- **中文内容**：使用 `v2.1-cuda`（最快）
- **英文内容**：使用 `v2.0-production`（最稳定）
- **混合内容**：使用 `v2.1-turbo`（均衡）

## 🚀 快速开始

### 方式一：Docker Run（推荐）

```bash
# 拉取镜像（中文/英文）
docker pull neosun/indextts2:v2.1-cuda

# 运行容器
docker run -d \
  --name indextts2 \
  --gpus all \
  -p 8002:8002 \
  -p 7860:7860 \
  -v /tmp/indextts2-outputs:/app/outputs \
  neosun/indextts2:v2.1-cuda

# 越南语版本
docker run -d \
  --name indextts2-vn \
  --gpus all \
  -p 8002:8002 \
  -p 7860:7860 \
  -v /tmp/indextts2-outputs:/app/outputs \
  neosun/indextts2:v2.1-cuda-vietnamese

# 日语版本
docker run -d \
  --name indextts2-jp \
  --gpus all \
  -p 8002:8002 \
  -p 7860:7860 \
  -v /tmp/indextts2-outputs:/app/outputs \
  neosun/indextts2:v2.1-cuda-japanese

# 等待 2-3 分钟服务启动
# 访问 Gradio WebUI: http://localhost:7860
# 访问 API 文档: http://localhost:8002/docs/
```

### 方式二：Docker Compose

```yaml
version: '3.8'
services:
  indextts2:
    image: neosun/indextts2:v2.1-cuda
    container_name: indextts2
    ports:
      - "8002:8002"
      - "7860:7860"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

## 📋 可用的 Docker 镜像

| 标签 | 特性 | 启动时间 | 使用场景 |
|-----|------|---------|---------|
| `v2.0-production` | 稳定基线版本 | ~90秒 | 生产环境、英文 |
| `v2.1-cuda` | CUDA 内核优化 | ~180秒 | 中文内容 |
| `v2.1-deepspeed` | DeepSpeed 加速 | ~90秒 | 快速部署 |
| `v2.1-turbo` | FP16 + CUDA 内核 | ~180秒 | 混合内容 |
| `v2.1-cuda-vietnamese` | 越南语版本 | ~180秒 | 越南语 TTS |
| `v2.1-cuda-japanese` | 日语版本 | ~180秒 | 日语 TTS |
| `v2.0-production` | 稳定基线版本 | ~90秒 | 生产环境、英文 |
| `v2.1-cuda` | CUDA 内核优化 | ~180秒 | 中文内容 |
| `v2.1-deepspeed` | DeepSpeed 加速 | ~90秒 | 快速部署 |
| `v2.1-turbo` | FP16 + CUDA 内核 | ~180秒 | 混合内容 |

## 🔌 API 使用

### REST API

```bash
# 基础合成
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，这是一个测试。",
    "spk_audio_prompt": "/app/examples/voice_01.wav"
  }' \
  -o output.wav

# 情感控制
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "哇！太棒了！",
    "spk_audio_prompt": "/app/examples/voice_01.wav",
    "emo_vector": [0.8, 0, 0, 0, 0, 0, 0.5, 0],
    "emo_alpha": 0.9
  }' \
  -o output.wav
```

### Python SDK

```python
import requests

url = "http://localhost:8002/tts"
payload = {
    "text": "你好，这是 IndexTTS2。",
    "spk_audio_prompt": "/app/examples/voice_01.wav"
}

response = requests.post(url, json=payload)
if response.status_code == 200:
    with open("output.wav", "wb") as f:
        f.write(response.content)
```

## 📁 音频文件管理

### 文件位置

**示例音频**（内置，只读）：
- 路径：`/app/examples/`
- 文件：`voice_01.wav` ~ `voice_12.wav`（12个说话人）、`emo_sad.wav`、`emo_hate.wav`（2个情感参考）
- 用途：API调用的参考音频

**用户上传和生成的音频**（映射到宿主机）：
- 容器路径：`/app/outputs/`
- 宿主机路径：`/tmp/indextts2-outputs/`
- 容器删除后文件仍保留

### 文件命名规则

**WebUI**（基于时间戳）：
```
upload_spk_20251207_170623.wav  # 上传的说话人音频
upload_emo_20251207_170623.wav  # 上传的情感音频
tts_20251207_170623.wav         # 生成的音频
```
格式：`年月日_时分秒` - 人类可读，易于按时间排序

**REST API**（基于UUID）：
```
tts_a1b2c3d4-e5f6-7890-abcd-ef1234567890.wav
```
格式：UUID v4 - 保证唯一性，适合高并发场景

## 📚 文档

- **API 文档**: http://localhost:8002/docs/
- **Swagger JSON**: http://localhost:8002/swagger.json
- **Gradio WebUI**: http://localhost:7860/
- **完整测试报告**: [BENCHMARK_FINAL_REPORT.md](BENCHMARK_FINAL_REPORT.md)
- **API 指南**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

## 🛠️ 系统要求

- Docker 20.10+
- NVIDIA GPU（8GB+ 显存）
- NVIDIA Docker Runtime

## 📊 情感向量格式

```python
[开心, 愤怒, 悲伤, 害怕, 厌恶, 忧郁, 惊讶, 平静]
# 示例: [0.8, 0, 0, 0, 0, 0, 0.5, 0] = 80% 开心 + 50% 平静
```

## 🎯 预置示例音频

容器包含 14 个示例音频文件（位于 `/app/examples/`）：
- `voice_01.wav` ~ `voice_12.wav` - 说话人参考音频
- `emo_sad.wav`, `emo_hate.wav` - 情感参考音频

## 📝 许可证

MIT License

## 🙏 致谢

基于 Bilibili IndexTeam 的 [IndexTTS2](https://github.com/index-tts/index-tts)。

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun100/indextts2-docker&type=Date)](https://star-history.com/#neosun100/indextts2-docker)

## 📱 关注我们

![微信公众号](https://img.aws.xin/uPic/扫码_搜索联合传播样式-标准色版.png)
