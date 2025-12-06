#!/bin/bash

echo "=== IndexTTS2 Docker API Tests ==="
echo ""

echo "1. Testing Health Endpoint..."
curl -s http://localhost:8002/health | jq .
echo ""

echo "2. Testing Basic TTS (Chinese)..."
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，这是IndexTTS2的测试。",
    "spk_audio_prompt": "examples/voice_01.wav"
  }' \
  --output /tmp/test_basic.wav \
  -w "\nHTTP Status: %{http_code}\n"
echo "Output saved to: /tmp/test_basic.wav"
echo ""

echo "3. Testing TTS with Emotion Vector..."
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "哇塞！这个太棒了！",
    "spk_audio_prompt": "examples/voice_01.wav",
    "emo_vector": [0.8, 0, 0, 0, 0, 0, 0.5, 0],
    "emo_alpha": 0.9
  }' \
  --output /tmp/test_emotion.wav \
  -w "\nHTTP Status: %{http_code}\n"
echo "Output saved to: /tmp/test_emotion.wav"
echo ""

echo "4. Testing TTS with Emotion Text..."
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "快躲起来！他要来了！",
    "spk_audio_prompt": "examples/voice_01.wav",
    "use_emo_text": true,
    "emo_alpha": 0.6
  }' \
  --output /tmp/test_emo_text.wav \
  -w "\nHTTP Status: %{http_code}\n"
echo "Output saved to: /tmp/test_emo_text.wav"
echo ""

echo "5. Testing TTS with Separate Emotion Audio..."
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "今天天气真好啊。",
    "spk_audio_prompt": "examples/voice_01.wav",
    "emo_audio_prompt": "examples/emo_sad.wav",
    "emo_alpha": 0.8
  }' \
  --output /tmp/test_emo_audio.wav \
  -w "\nHTTP Status: %{http_code}\n" 2>&1 | grep "HTTP Status"
echo "Output saved to: /tmp/test_emo_audio.wav"
echo ""

echo "=== All Tests Complete ==="
echo "UI is available at: http://localhost:7870"
echo "API is available at: http://localhost:8002"
