# IndexTTS2 Docker Deployment Guide

## Overview

This deployment provides both a Web UI and REST API for IndexTTS2 text-to-speech synthesis.

**Ports:**
- UI: `http://localhost:7870`
- API: `http://localhost:8002`

## Quick Start

### 1. Build the Docker Image

```bash
docker build -t indextts2:latest .
```

### 2. Run the Container

```bash
docker run -d --name indextts2 \
  --gpus all \
  -p 7870:7870 \
  -p 8002:8002 \
  -v $(pwd)/checkpoints:/app/checkpoints \
  -v $(pwd)/examples:/app/examples \
  indextts2:latest
```

### 3. Check Container Status

```bash
docker logs indextts2
```

Wait until you see:
```
* Running on http://0.0.0.0:7870
* Running on http://127.0.0.1:8002
```

## Web UI Usage

Access the UI at: `http://localhost:7870`

### Features Available in UI:

1. **Text Input**: Enter the text you want to synthesize
2. **Speaker Audio Prompt**: Upload reference audio for voice cloning
3. **Emotion Audio Prompt**: Optional separate audio for emotion control
4. **Emotion Controls**:
   - Emotion Alpha: Control emotion intensity (0.0-1.0)
   - Emotion Vector: Fine-tune 8 emotions individually:
     - Happy, Angry, Sad, Afraid, Disgusted, Melancholic, Surprised, Calm
   - Use Emotion from Text: Automatically detect emotion from input text
   - Emotion Text: Provide separate text for emotion guidance
   - Use Random Sampling: Add variability to output

## API Usage

### Health Check

```bash
curl http://localhost:8002/health
```

Response:
```json
{"status": "ok"}
```

### Basic TTS Synthesis

```bash
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，这是一个测试。",
    "spk_audio_prompt": "examples/voice_01.wav"
  }' \
  --output output.wav
```

### TTS with Emotion Vector

Control emotions using an 8-float array: `[happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]`

```bash
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "哇塞！这个太棒了！",
    "spk_audio_prompt": "examples/voice_01.wav",
    "emo_vector": [0.8, 0, 0, 0, 0, 0, 0.5, 0],
    "emo_alpha": 0.9
  }' \
  --output output.wav
```

### TTS with Emotion Audio

Use a separate audio file to control emotion:

```bash
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "今天天气真好。",
    "spk_audio_prompt": "examples/voice_01.wav",
    "emo_audio_prompt": "examples/emo_sad.wav",
    "emo_alpha": 0.8
  }' \
  --output output.wav
```

### TTS with Text-Based Emotion

Let the model automatically detect emotion from your text:

```bash
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "快躲起来！他要来了！",
    "spk_audio_prompt": "examples/voice_01.wav",
    "use_emo_text": true,
    "emo_alpha": 0.6
  }' \
  --output output.wav
```

### TTS with Separate Emotion Text

Provide different text for emotion guidance:

```bash
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "今天的会议很重要。",
    "spk_audio_prompt": "examples/voice_01.wav",
    "use_emo_text": true,
    "emo_text": "我很紧张和担心。",
    "emo_alpha": 0.7
  }' \
  --output output.wav
```

## API Parameters

### Required Parameters

- `text` (string): Text to synthesize
- `spk_audio_prompt` (string): Path to speaker reference audio file

### Optional Parameters

- `emo_audio_prompt` (string): Path to emotion reference audio file
- `emo_alpha` (float, 0.0-1.0): Emotion intensity, default: 1.0
- `emo_vector` (array of 8 floats): Manual emotion control `[happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]`
- `use_emo_text` (boolean): Enable text-based emotion detection, default: false
- `emo_text` (string): Separate text for emotion guidance (requires `use_emo_text: true`)
- `use_random` (boolean): Enable random sampling for variety, default: false

## Testing

Run the comprehensive test suite:

```bash
./test_api.sh
```

This will test:
1. Health endpoint
2. Basic TTS synthesis
3. Emotion vector control
4. Text-based emotion
5. Separate emotion audio

## Container Management

### View Logs

```bash
docker logs indextts2
docker logs -f indextts2  # Follow logs
```

### Stop Container

```bash
docker stop indextts2
```

### Start Container

```bash
docker start indextts2
```

### Restart Container

```bash
docker restart indextts2
```

### Remove Container

```bash
docker rm -f indextts2
```

## Using Docker Compose

Alternatively, use docker-compose:

```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

## Troubleshooting

### Container Exits Immediately

Check logs:
```bash
docker logs indextts2
```

Common issues:
- Missing model files in `checkpoints/` directory
- GPU not available (requires NVIDIA GPU with CUDA support)
- Port conflicts (7870 or 8002 already in use)

### Port Already in Use

Check which ports are available:
```bash
ss -tuln | grep LISTEN
```

Modify ports in docker run command:
```bash
docker run -d --name indextts2 \
  --gpus all \
  -p 7871:7870 \  # Changed UI port
  -p 8003:8002 \  # Changed API port
  ...
```

### GPU Not Detected

Ensure NVIDIA Docker runtime is installed:
```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

## Performance Tips

1. **Use FP16**: Already enabled in the Docker deployment for faster inference
2. **Batch Processing**: For multiple requests, consider queuing them
3. **Resource Limits**: Monitor GPU memory usage with `nvidia-smi`

## Security Notes

- The API server is a development server (Flask). For production, use a proper WSGI server
- Consider adding authentication if exposing to the internet
- The container runs as root - consider using a non-root user for production

## Support

For issues and questions:
- GitHub: https://github.com/index-tts/index-tts
- Email: indexspeech@bilibili.com
