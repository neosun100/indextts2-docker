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

## 🛠️ 系統要求

### 硬體要求
- **GPU**: NVIDIA GPU，顯存 8GB 以上（已在 L40S 上測試）
- **記憶體**: 建議 16GB 以上系統記憶體

### 軟體前置條件

**1. NVIDIA 驅動程式**（必需）
- 最低版本：525.60.13+
- 檢查版本：`nvidia-smi`
- 下載位址：[NVIDIA 驅動程式下載](https://www.nvidia.com/download/index.aspx)

**2. Docker**（必需）
- 最低版本：20.10+
- 檢查版本：`docker --version`
- 安裝指南：[Docker 安裝文件](https://docs.docker.com/engine/install/)

**3. NVIDIA Container Toolkit**（必需）
- 用於在 Docker 容器中啟用 GPU 支援
- 安裝方法：
```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

**4. 驗證 GPU 存取**
```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

**注意**：主機**無需安裝** CUDA Toolkit。Docker 映像已包含 CUDA 12.1.0。

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
  -v /tmp/indextts2-outputs:/app/outputs \
  neosun/indextts2:v2.1-cuda

# 越南語版本
docker run -d \
  --name indextts2-vn \
  --gpus all \
  -p 8002:8002 \
  -p 7860:7860 \
  -v /tmp/indextts2-outputs:/app/outputs \
  neosun/indextts2:v2.1-cuda-vietnamese

# 日語版本
docker run -d \
  --name indextts2-jp \
  --gpus all \
  -p 8002:8002 \
  -p 7860:7860 \
  -v /tmp/indextts2-outputs:/app/outputs \
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
    volumes:
      - /tmp/indextts2-outputs:/app/outputs
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

## 📁 音訊檔案管理

### 檔案位置

**範例音訊**（內建，唯讀）：
- 路徑：`/app/examples/`
- 檔案：`voice_01.wav` ~ `voice_12.wav`（12個說話人）、`emo_sad.wav`、`emo_hate.wav`（2個情感參考）
- 用途：API呼叫的參考音訊

**使用者上傳和生成的音訊**（映射到主機）：
- 容器路徑：`/app/outputs/`
- 主機路徑：`/tmp/indextts2-outputs/`
- 容器刪除後檔案仍保留

### 檔案命名規則

**WebUI**（基於時間戳記）：
```
upload_spk_20251207_170623.wav  # 上傳的說話人音訊
upload_emo_20251207_170623.wav  # 上傳的情感音訊
tts_20251207_170623.wav         # 生成的音訊
```
格式：`年月日_時分秒` - 人類可讀，易於按時間排序

**REST API**（基於UUID）：
```
tts_a1b2c3d4-e5f6-7890-abcd-ef1234567890.wav
```
格式：UUID v4 - 保證唯一性，適合高並發場景

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
