#!/usr/bin/env python3
"""
详细分析TTS pipeline的每个环节耗时
"""
import requests
import time

API_BASE = "http://localhost:8002"
TEST_TEXT = "这是一个性能测试，用于分析每个环节的具体耗时。"

print("="*80)
print("🔍 IndexTTS2 Pipeline 详细性能分析")
print("="*80)
print()

# 测试5次取平均
ITERATIONS = 5
print(f"测试次数: {ITERATIONS}次")
print()

for i in range(ITERATIONS):
    print(f"\n{'='*80}")
    print(f"第 {i+1}/{ITERATIONS} 次测试")
    print('='*80)
    
    start = time.time()
    response = requests.post(
        f"{API_BASE}/tts",
        json={
            "text": TEST_TEXT,
            "spk_audio_prompt": "/app/examples/voice_01.wav"
        },
        timeout=60
    )
    total_time = time.time() - start
    
    if response.status_code == 200:
        print(f"✅ 总时间: {total_time:.3f}秒")
        print(f"   音频大小: {len(response.content)/1024:.1f}KB")
    else:
        print(f"❌ 失败: {response.status_code}")

print("\n" + "="*80)
print("📊 请查看容器日志获取详细的各环节耗时")
print("="*80)
print("\n运行以下命令查看日志:")
print("docker logs indextts2-api --tail 100")
