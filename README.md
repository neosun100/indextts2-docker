# IndexTTS2 Docker - Zero-Shot Text-to-Speech

[English](README.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

[![Docker Hub](https://img.shields.io/badge/Docker-Hub-blue?logo=docker)](https://hub.docker.com/r/neosun/indextts2)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/neosun100/indextts2-docker?style=social)](https://github.com/neosun100/indextts2-docker)

Production-ready Docker images for IndexTTS2 - A breakthrough in emotionally expressive and duration-controlled auto-regressive zero-shot text-to-speech.

## ✨ Features

- 🎯 **Zero-Shot Voice Cloning** - Clone any voice with 3-10 seconds of audio
- 🎭 **Emotion Control** - 8-dimensional emotion vectors (happy, angry, sad, afraid, disgusted, melancholic, surprised, calm)
- 🚀 **Multiple Optimizations** - CUDA kernel, DeepSpeed, FP16 support
- 📦 **All-in-One Docker** - Pre-built images with all models included
- 🌐 **Dual Interface** - REST API + Gradio WebUI
- 📚 **Swagger Docs** - Interactive API documentation

## 🏆 Benchmark Results

Tested on NVIDIA L40S GPU with 80 test cases (4 versions × 4 scenarios × 5 runs):

| Version | Chinese Short | Chinese Long | English Short | English Long | Success Rate |
|---------|---------------|--------------|---------------|--------------|--------------|
| v2.0-production | 6.42s | 27.96s | 7.60s | **35.36s** ⭐ | 100% |
| v2.1-cuda | **6.13s** ⭐ | **26.88s** ⭐ | 7.48s | 35.72s | 100% |
| v2.1-deepspeed | 6.62s | 28.58s | 7.51s | 36.46s | 100% |
| v2.1-turbo | 6.41s | 28.34s | 7.70s | 35.48s | 100% |

**Recommendation:**
- **Chinese content**: Use `v2.1-cuda` (fastest)
- **English content**: Use `v2.0-production` (most stable)
- **Mixed content**: Use `v2.1-turbo` (balanced)

## 🛠️ Requirements

### Hardware Requirements
- **GPU**: NVIDIA GPU with 8GB+ VRAM (tested on L40S)
- **RAM**: 16GB+ system memory recommended

### Software Prerequisites

**1. NVIDIA Driver** (Required)
- Minimum version: 525.60.13+
- Check version: `nvidia-smi`
- Download: [NVIDIA Driver Downloads](https://www.nvidia.com/download/index.aspx)

**2. Docker** (Required)
- Minimum version: 20.10+
- Check version: `docker --version`
- Install: [Docker Installation Guide](https://docs.docker.com/engine/install/)

**3. NVIDIA Container Toolkit** (Required)
- Enables GPU support in Docker containers
- Install:
```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

**4. Verify GPU Access**
```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

**Note**: CUDA Toolkit installation on host is **NOT required**. The Docker image includes CUDA 12.1.0.

## 🚀 Quick Start

### Option 1: Docker Run (Recommended)

```bash
# Pull the image (Chinese/English)
docker pull neosun/indextts2:v2.1-cuda

# Run the container
docker run -d \
  --name indextts2 \
  --gpus all \
  -p 8002:8002 \
  -p 7860:7860 \
  -v /tmp/indextts2-outputs:/app/outputs \
  neosun/indextts2:v2.1-cuda

# For Vietnamese
docker run -d \
  --name indextts2-vn \
  --gpus all \
  -p 8002:8002 \
  -p 7860:7860 \
  -v /tmp/indextts2-outputs:/app/outputs \
  neosun/indextts2:v2.1-cuda-vietnamese

# For Japanese
docker run -d \
  --name indextts2-jp \
  --gpus all \
  -p 8002:8002 \
  -p 7860:7860 \
  -v /tmp/indextts2-outputs:/app/outputs \
  neosun/indextts2:v2.1-cuda-japanese

# Wait 2-3 minutes for service to start
# Access Gradio WebUI: http://localhost:7860
# Access API Docs: http://localhost:8002/docs/
```

### Option 2: Docker Compose

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

## 📋 Available Docker Images

| Tag | Features | Performance | Startup | Use Case | Recommended |
|-----|----------|-------------|---------|----------|-------------|
| `v2.2-performance-optimized` ⭐ | **Enhanced API** + Tunable params + Speaker cache + **Health check** | **26.6% faster** | ~180s | **Production (Best)** | ✅ **YES** |
| `latest` | Same as v2.2 | 26.6% faster | ~180s | Production | ✅ **YES** |
| `v2.1-cuda` | CUDA kernel optimization | Baseline | ~180s | Chinese content | ⭐⭐⭐ |
| `v2.0-production` | Stable baseline | Baseline | ~90s | English content | ⭐⭐⭐ |

### 🏆 Recommended: v2.2-performance-optimized

**Why v2.2?**
- ✅ **26.6% faster** with tunable parameters
- ✅ **Enhanced API** with 8 performance parameters
- ✅ **Speaker cache** system (no re-upload needed)
- ✅ **Health check** built-in (Docker status: healthy)
- ✅ **All features** from previous versions
- ✅ **Production ready** and fully tested

**Quick Start (Recommended)**:
```bash
docker pull neosun/indextts2:v2.2-performance-optimized

docker run -d \
  --name indextts2 \
  --gpus all \
  -p 0.0.0.0:8002:8002 \
  -p 0.0.0.0:7860:7860 \
  -v /tmp/indextts2-outputs:/app/outputs \
  --restart unless-stopped \
  neosun/indextts2:v2.2-performance-optimized

# Wait 2-3 minutes for service to start
# Access API: http://your-ip:8002/docs/
# Access WebUI: http://your-ip:7860
```

**Port Explanation**:
- **8002**: REST API endpoint (for programmatic access)
- **7860**: Gradio WebUI (for browser-based interface)

## 🔌 API Usage

### Available Endpoints

**1. Standard TTS** - `/tts` (POST)
```bash
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test.",
    "spk_audio_prompt": "/app/examples/voice_01.wav"
  }' \
  -o output.wav
```

**2. Cached TTS** - `/tts_cached` (POST)
```bash
# First, upload speaker audio
curl -X POST http://localhost:8002/upload_speaker \
  -F "audio=@my_voice.wav" \
  -F "speaker_name=MyVoice"
# Returns: {"speaker_id": "spk_abc123"}

# Then use speaker_id for TTS
curl -X POST http://localhost:8002/tts_cached \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello",
    "speaker_id": "spk_abc123"
  }' \
  -o output.wav
```

**3. Upload Speaker** - `/upload_speaker` (POST)
```bash
curl -X POST http://localhost:8002/upload_speaker \
  -F "audio=@voice.wav" \
  -F "speaker_name=Speaker1"
```

**4. List Speakers** - `/speakers` (GET)
```bash
curl http://localhost:8002/speakers
```

### Performance Parameters

All TTS endpoints support these optional parameters:
- `num_beams` (default: 3): Beam search width
- `do_sample` (default: true): Enable sampling
- `top_k` (default: 30): Top-k sampling
- `top_p` (default: 0.8): Nucleus sampling
- `temperature` (default: 0.8): Sampling temperature
- `max_mel_tokens` (default: 1500): Max output length

**Recommended for speed**:
```json
{
  "num_beams": 1,
  "do_sample": false,
  "top_k": 10
}
```

### REST API

```bash
# Basic synthesis
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test.",
    "spk_audio_prompt": "/app/examples/voice_01.wav"
  }' \
  -o output.wav

# With emotion control
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Wow! This is amazing!",
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
    "text": "Hello, this is IndexTTS2.",
    "spk_audio_prompt": "/app/examples/voice_01.wav"
}

response = requests.post(url, json=payload)
if response.status_code == 200:
    with open("output.wav", "wb") as f:
        f.write(response.content)
```

## 📁 Audio File Management

### File Locations

**Example Audio** (Built-in, read-only):
- Path: `/app/examples/`
- Files: `voice_01.wav` ~ `voice_12.wav` (12 speakers), `emo_sad.wav`, `emo_hate.wav` (2 emotion references)
- Usage: Reference audio for API calls

**User Uploads & Generated Audio** (Mapped to host):
- Container path: `/app/outputs/`
- Host path: `/tmp/indextts2-outputs/`
- Persists after container deletion

### File Naming Convention

**WebUI** (Timestamp-based):
```
upload_spk_20251207_170623.wav  # Uploaded speaker audio
upload_emo_20251207_170623.wav  # Uploaded emotion audio
tts_20251207_170623.wav         # Generated audio
```
Format: `YYYYMMDD_HHMMSS` - Human-readable, easy to sort by time

**REST API** (UUID-based):
```
tts_a1b2c3d4-e5f6-7890-abcd-ef1234567890.wav
```
Format: UUID v4 - Guaranteed unique, suitable for high concurrency

## 🚀 Performance Optimization

### Enhanced API with Tunable Parameters

This Docker image includes **performance optimization API** that allows dynamic parameter tuning:

**Tunable Parameters**:
- `num_beams`: Beam search width (default: 3, recommended: 1)
- `do_sample`: Sampling vs greedy decoding (default: true, fast: false)
- `top_k`: Sampling range (default: 30, recommended: 10)
- `max_mel_tokens`: Max generation length (default: 1500)

**Performance Gains** (tested on L40S GPU):
- Baseline: 7.8s (default parameters)
- Optimized: 5.7s (num_beams=1, do_sample=false, top_k=10)
- **Improvement: 26.6% faster**

**Usage Example**:
```bash
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world",
    "spk_audio_prompt": "/app/examples/voice_01.wav",
    "num_beams": 1,
    "do_sample": false,
    "top_k": 10
  }' \
  -o output.wav
```

### Speaker Cache System

**Two-tier caching** for efficient speaker management:

1. **GPU Memory Cache** (fastest): Automatic, ~13GB fixed allocation
2. **Persistent Disk Cache**: Survives container restarts

**Cache API Workflow**:
```bash
# Step 1: Upload speaker audio once
curl -X POST http://localhost:8002/upload_speaker \
  -F "audio=@my_voice.wav" \
  -F "speaker_name=MyVoice"
# Returns: {"speaker_id": "spk_abc123", ...}

# Step 2: Reuse speaker_id for unlimited generations
curl -X POST http://localhost:8002/tts_cached \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello", "speaker_id": "spk_abc123"}' \
  -o output.wav

# List all cached speakers
curl http://localhost:8002/speakers
```

**Benefits**:
- No need to re-upload audio files
- Faster subsequent calls (cache hit)
- Persistent across container restarts
- Supports unlimited speakers (fixed memory)

## 📚 Documentation

- **API Documentation**: http://localhost:8002/docs/
- **Swagger JSON**: http://localhost:8002/swagger.json
- **Gradio WebUI**: http://localhost:7860/
- **Full Benchmark Report**: [BENCHMARK_FINAL_REPORT.md](BENCHMARK_FINAL_REPORT.md)
- **API Guide**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

## 📊 Emotion Vector Format

```python
[happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]
# Example: [0.8, 0, 0, 0, 0, 0, 0.5, 0] = 80% happy + 50% calm
```

## 🎯 Pre-built Example Audio

Container includes 14 example audio files in `/app/examples/`:
- `voice_01.wav` ~ `voice_12.wav` - Speaker references
- `emo_sad.wav`, `emo_hate.wav` - Emotion references

## 📝 License

MIT License

## 🙏 Credits

Based on [IndexTTS2](https://github.com/index-tts/index-tts) by Bilibili IndexTeam.

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun100/indextts2-docker&type=Date)](https://star-history.com/#neosun100/indextts2-docker)

## 📱 Follow Us

![WeChat](https://img.aws.xin/uPic/扫码_搜索联合传播样式-标准色版.png)
