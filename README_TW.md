# IndexTTS2 Docker - 零樣本語音合成

[English](README.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

[![Docker Hub](https://img.shields.io/badge/Docker-Hub-blue?logo=docker)](https://hub.docker.com/r/neosun/indextts2)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/neosun100/indextts2-docker?style=social)](https://github.com/neosun100/indextts2-docker)

生產就緒的 IndexTTS2 Docker 映像 - 支援情感表達和時長控制的突破性自迴歸零樣本語音合成系統。

## ✨ 功能特性

- 🎯 **零樣本聲音克隆** - 僅需 3-10 秒音訊即可克隆任何聲音
- 🎭 **情感控制** - 8 維情感向量（開心、憤怒、悲傷、害怕、厭惡、憂鬱、驚訝、平靜）
- 🚀 **多種優化** - CUDA 核心、DeepSpeed、FP16 支援
- 📦 **一體化 Docker** - 預構建映像包含所有模型
- 🌐 **雙重介面** - REST API + Gradio WebUI
- 📚 **Swagger 文件** - 互動式 API 文件

## 🏆 效能測試結果

在 NVIDIA L40S GPU 上測試 80 個用例（4 個版本 × 4 個場景 × 5 次執行）：

| 版本 | 中文短文本 | 中文長文本 | 英文短文本 | 英文長文本 | 成功率 |
|------|-----------|-----------|-----------|-----------|--------|
| v2.0-production | 6.42秒 | 27.96秒 | 7.60秒 | **35.36秒** ⭐ | 100% |
| v2.1-cuda | **6.13秒** ⭐ | **26.88秒** ⭐ | 7.48秒 | 35.72秒 | 100% |
| v2.1-deepspeed | 6.62秒 | 28.58秒 | 7.51秒 | 36.46秒 | 100% |
| v2.1-turbo | 6.41秒 | 28.34秒 | 7.70秒 | 35.48秒 | 100% |

**推薦選擇：**
- **中文內容**：使用 `v2.1-cuda`（最快）
- **英文內容**：使用 `v2.0-production`（最穩定）
- **混合內容**：使用 `v2.1-turbo`（均衡）

## 🚀 快速開始

### 方式一：Docker Run（推薦）

```bash
# 拉取映像（中文/英文）
docker pull neosun/indextts2:v2.1-cuda

# 執行容器
docker run -d \
  --name indextts2 \
  --gpus all \
  -p 8002:8002 \
  -p 7860:7860 \
  neosun/indextts2:v2.1-cuda

# 越南語版本
docker run -d \
  --name indextts2-vn \
  --gpus all \
  -p 8002:8002 \
  -p 7860:7860 \
  neosun/indextts2:v2.1-cuda-vietnamese

# 日語版本
docker run -d \
  --name indextts2-jp \
  --gpus all \
  -p 8002:8002 \
  -p 7860:7860 \
  neosun/indextts2:v2.1-cuda-japanese

# 等待 2-3 分鐘服務啟動
# 訪問 Gradio WebUI: http://localhost:7860
# 訪問 API 文件: http://localhost:8002/docs/
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

## 📋 可用的 Docker 映像

| 標籤 | 特性 | 啟動時間 | 使用場景 |
|-----|------|---------|---------|
| `v2.0-production` | 穩定基線版本 | ~90秒 | 生產環境、英文 |
| `v2.1-cuda` | CUDA 內核優化 | ~180秒 | 中文內容 |
| `v2.1-deepspeed` | DeepSpeed 加速 | ~90秒 | 快速部署 |
| `v2.1-turbo` | FP16 + CUDA 內核 | ~180秒 | 混合內容 |
| `v2.1-cuda-vietnamese` | 越南語版本 | ~180秒 | 越南語 TTS |
| `v2.1-cuda-japanese` | 日語版本 | ~180秒 | 日語 TTS |
| `v2.0-production` | 穩定基線版本 | ~90秒 | 生產環境、英文 |
| `v2.1-cuda` | CUDA 核心優化 | ~180秒 | 中文內容 |
| `v2.1-deepspeed` | DeepSpeed 加速 | ~90秒 | 快速部署 |
| `v2.1-turbo` | FP16 + CUDA 核心 | ~180秒 | 混合內容 |

## 🔌 API 使用

### REST API

```bash
# 基礎合成
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，這是一個測試。",
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
    "text": "你好，這是 IndexTTS2。",
    "spk_audio_prompt": "/app/examples/voice_01.wav"
}

response = requests.post(url, json=payload)
if response.status_code == 200:
    with open("output.wav", "wb") as f:
        f.write(response.content)
```

## 📚 文件

- **API 文件**: http://localhost:8002/docs/
- **Swagger JSON**: http://localhost:8002/swagger.json
- **Gradio WebUI**: http://localhost:7860/
- **完整測試報告**: [BENCHMARK_FINAL_REPORT.md](BENCHMARK_FINAL_REPORT.md)
- **API 指南**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

## 🛠️ 系統要求

- Docker 20.10+
- NVIDIA GPU（8GB+ 顯存）
- NVIDIA Docker Runtime

## 📊 情感向量格式

```python
[開心, 憤怒, 悲傷, 害怕, 厭惡, 憂鬱, 驚訝, 平靜]
# 示例: [0.8, 0, 0, 0, 0, 0, 0.5, 0] = 80% 開心 + 50% 平靜
```

## 🎯 預置示例音訊

容器包含 14 個示例音訊檔案（位於 `/app/examples/`）：
- `voice_01.wav` ~ `voice_12.wav` - 說話人參考音訊
- `emo_sad.wav`, `emo_hate.wav` - 情感參考音訊

## 📝 許可證

MIT License

## 🙏 致謝

基於 Bilibili IndexTeam 的 [IndexTTS2](https://github.com/index-tts/index-tts)。

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun100/indextts2-docker&type=Date)](https://star-history.com/#neosun100/indextts2-docker)

## 📱 關注我們

![微信公眾號](https://img.aws.xin/uPic/扫码_搜索联合传播样式-标准色版.png)
