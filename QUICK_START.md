# IndexTTS2 Docker - Quick Start

## 🚀 Access Points

- **Web UI**: http://localhost:7870
- **API**: http://localhost:8002

## 📋 Quick Commands

### Check Status
```bash
docker ps | grep indextts2
curl http://localhost:8002/health
```

### Run All Tests
```bash
./test_api.sh
```

### Basic API Call
```bash
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好世界",
    "spk_audio_prompt": "examples/voice_01.wav"
  }' \
  --output output.wav
```

### With Emotion
```bash
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "太棒了！",
    "spk_audio_prompt": "examples/voice_01.wav",
    "emo_vector": [0.8, 0, 0, 0, 0, 0, 0.5, 0],
    "emo_alpha": 0.9
  }' \
  --output output.wav
```

## 🎛️ Emotion Vector

`[happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]`

Examples:
- Happy: `[0.8, 0, 0, 0, 0, 0, 0, 0]`
- Sad: `[0, 0, 0.9, 0, 0, 0, 0, 0]`
- Excited: `[0.7, 0, 0, 0, 0, 0, 0.6, 0]`
- Calm: `[0, 0, 0, 0, 0, 0, 0, 1.0]`

## 🔧 Container Management

```bash
docker stop indextts2     # Stop
docker start indextts2    # Start  
docker restart indextts2  # Restart
docker logs -f indextts2  # View logs
```

## 📚 Full Documentation

- `DOCKER_DEPLOYMENT.md` - Complete deployment guide
- `DEPLOYMENT_SUMMARY.md` - Deployment status and results
- `README.md` - Original project documentation

## ✅ Verified Features

- ✅ Web UI with all parameters
- ✅ REST API with full control
- ✅ Voice cloning
- ✅ Emotion control (vector, audio, text)
- ✅ FP16 optimization
- ✅ GPU acceleration

## 🆘 Troubleshooting

**Container not running?**
```bash
docker logs indextts2
```

**Port conflict?**
```bash
ss -tuln | grep -E "7870|8002"
```

**Need to rebuild?**
```bash
docker rm -f indextts2
docker build -t indextts2:latest .
docker run -d --name indextts2 --gpus all -p 7870:7870 -p 8002:8002 \
  -v $(pwd)/checkpoints:/app/checkpoints \
  -v $(pwd)/examples:/app/examples \
  indextts2:latest
```
