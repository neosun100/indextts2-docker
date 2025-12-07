# IndexTTS2 Docker - ゼロショット音声合成

[English](README.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

[![Docker Hub](https://img.shields.io/badge/Docker-Hub-blue?logo=docker)](https://hub.docker.com/r/neosun/indextts2)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/neosun100/indextts2-docker?style=social)](https://github.com/neosun100/indextts2-docker)

本番環境対応の IndexTTS2 Docker イメージ - 感情表現と持続時間制御をサポートする画期的な自己回帰型ゼロショット音声合成システム。

## ✨ 機能

- 🎯 **ゼロショット音声クローニング** - 3-10秒の音声で任意の声をクローン
- 🎭 **感情制御** - 8次元感情ベクトル（喜び、怒り、悲しみ、恐れ、嫌悪、憂鬱、驚き、平静）
- 🚀 **複数の最適化** - CUDAカーネル、DeepSpeed、FP16サポート
- 📦 **オールインワン Docker** - すべてのモデルを含む事前構築イメージ
- 🌐 **デュアルインターフェース** - REST API + Gradio WebUI
- 📚 **Swagger ドキュメント** - インタラクティブな API ドキュメント

## 🏆 ベンチマーク結果

NVIDIA L40S GPU で 80 テストケース（4バージョン × 4シナリオ × 5回実行）をテスト：

| バージョン | 中国語短文 | 中国語長文 | 英語短文 | 英語長文 | 成功率 |
|-----------|----------|----------|---------|---------|--------|
| v2.0-production | 6.42秒 | 27.96秒 | 7.60秒 | **35.36秒** ⭐ | 100% |
| v2.1-cuda | **6.13秒** ⭐ | **26.88秒** ⭐ | 7.48秒 | 35.72秒 | 100% |
| v2.1-deepspeed | 6.62秒 | 28.58秒 | 7.51秒 | 36.46秒 | 100% |
| v2.1-turbo | 6.41秒 | 28.34秒 | 7.70秒 | 35.48秒 | 100% |

**推奨：**
- **中国語コンテンツ**：`v2.1-cuda` を使用（最速）
- **英語コンテンツ**：`v2.0-production` を使用（最も安定）
- **混合コンテンツ**：`v2.1-turbo` を使用（バランス型）

## 🚀 クイックスタート

### 方法1：Docker Run（推奨）

```bash
# イメージをプル（中国語/英語）
docker pull neosun/indextts2:v2.1-cuda

# コンテナを実行
docker run -d \
  --name indextts2 \
  --gpus all \
  -p 8002:8002 \
  -p 7860:7860 \
  -v /tmp/indextts2-outputs:/app/outputs \
  neosun/indextts2:v2.1-cuda

# ベトナム語版
docker run -d \
  --name indextts2-vn \
  --gpus all \
  -p 8002:8002 \
  -p 7860:7860 \
  -v /tmp/indextts2-outputs:/app/outputs \
  neosun/indextts2:v2.1-cuda-vietnamese

# 日本語版
docker run -d \
  --name indextts2-jp \
  --gpus all \
  -p 8002:8002 \
  -p 7860:7860 \
  -v /tmp/indextts2-outputs:/app/outputs \
  neosun/indextts2:v2.1-cuda-japanese

# サービス起動まで 2-3 分待機
# Gradio WebUI にアクセス: http://localhost:7860
# API ドキュメントにアクセス: http://localhost:8002/docs/
```

### 方法2：Docker Compose

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

## 📋 利用可能な Docker イメージ

| タグ | 特徴 | 起動時間 | 使用例 |
|-----|------|---------|--------|
| `v2.0-production` | 安定版ベースライン | ~90秒 | 本番環境、英語 |
| `v2.1-cuda` | CUDA カーネル最適化 | ~180秒 | 中国語コンテンツ |
| `v2.1-deepspeed` | DeepSpeed 高速化 | ~90秒 | 迅速なデプロイ |
| `v2.1-turbo` | FP16 + CUDA カーネル | ~180秒 | 混合コンテンツ |
| `v2.1-cuda-vietnamese` | ベトナム語版 | ~180秒 | ベトナム語 TTS |
| `v2.1-cuda-japanese` | 日本語版 | ~180秒 | 日本語 TTS |
| `v2.0-production` | 安定版ベースライン | ~90秒 | 本番環境、英語 |
| `v2.1-cuda` | CUDA カーネル最適化 | ~180秒 | 中国語コンテンツ |
| `v2.1-deepspeed` | DeepSpeed 高速化 | ~90秒 | 迅速なデプロイ |
| `v2.1-turbo` | FP16 + CUDA カーネル | ~180秒 | 混合コンテンツ |

## 🔌 API 使用方法

### REST API

```bash
# 基本的な合成
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "こんにちは、これはテストです。",
    "spk_audio_prompt": "/app/examples/voice_01.wav"
  }' \
  -o output.wav

# 感情制御
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "わあ！素晴らしい！",
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
    "text": "こんにちは、これは IndexTTS2 です。",
    "spk_audio_prompt": "/app/examples/voice_01.wav"
}

response = requests.post(url, json=payload)
if response.status_code == 200:
    with open("output.wav", "wb") as f:
        f.write(response.content)
```

## 📚 ドキュメント

- **API ドキュメント**: http://localhost:8002/docs/
- **Swagger JSON**: http://localhost:8002/swagger.json
- **Gradio WebUI**: http://localhost:7860/
- **完全なベンチマークレポート**: [BENCHMARK_FINAL_REPORT.md](BENCHMARK_FINAL_REPORT.md)
- **API ガイド**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

## 🛠️ システム要件

- Docker 20.10+
- NVIDIA GPU（8GB+ VRAM）
- NVIDIA Docker Runtime

## 📊 感情ベクトル形式

```python
[喜び, 怒り, 悲しみ, 恐れ, 嫌悪, 憂鬱, 驚き, 平静]
# 例: [0.8, 0, 0, 0, 0, 0, 0.5, 0] = 80% 喜び + 50% 平静
```

## 🎯 プリセット音声サンプル

コンテナには 14 個の音声サンプルファイルが含まれています（`/app/examples/` に配置）：
- `voice_01.wav` ~ `voice_12.wav` - 話者参照音声
- `emo_sad.wav`, `emo_hate.wav` - 感情参照音声

## 📝 ライセンス

MIT License

## 🙏 クレジット

Bilibili IndexTeam の [IndexTTS2](https://github.com/index-tts/index-tts) に基づいています。

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun100/indextts2-docker&type=Date)](https://star-history.com/#neosun100/indextts2-docker)

## 📱 フォローする

![WeChat](https://img.aws.xin/uPic/扫码_搜索联合传播样式-标准色版.png)
