#!/usr/bin/env python3
"""
测试缓存API vs 传统API的性能对比
"""
import time
import requests
import statistics

API_BASE = "http://localhost:8002"
TEST_TEXT = "这是一个性能测试，用于对比不同API的速度差异。"
ITERATIONS = 5

def remove_extremes(times):
    if len(times) <= 2:
        return times
    return sorted(times)[1:-1]

print("="*80)
print("🧪 IndexTTS2 缓存API性能对比测试")
print("="*80)
print()

# 步骤1: 上传说话人到缓存
print("📤 步骤1: 上传说话人音频到缓存...")
with open('/tmp/voice_01.wav', 'rb') as f:
    response = requests.post(
        f"{API_BASE}/upload_speaker",
        files={'audio': f},
        data={'speaker_name': 'performance_test_speaker'}
    )
result = response.json()
speaker_id = result['speaker_id']
print(f"   ✅ Speaker ID: {speaker_id}")
print(f"   ✅ Status: {result['status']}")
print()

# 测试1: 传统API（每次都传音频路径）
print("="*80)
print("🧪 测试1: 传统API (/tts) - 每次传音频路径")
print("="*80)

times_traditional = []
for i in range(ITERATIONS):
    print(f"[轮次 {i+1}/{ITERATIONS}]: ", end="", flush=True)
    
    start = time.time()
    response = requests.post(
        f"{API_BASE}/tts",
        json={
            "text": TEST_TEXT,
            "spk_audio_prompt": "/app/examples/voice_01.wav"
        },
        timeout=60
    )
    elapsed = time.time() - start
    
    if response.status_code == 200:
        times_traditional.append(elapsed)
        print(f"✅ {elapsed:.3f}s")
    else:
        print(f"❌ 失败")

avg_traditional = statistics.mean(remove_extremes(times_traditional))
print(f"\n📊 传统API平均时间: {avg_traditional:.3f}s")

# 测试2: 缓存API（使用speaker_id）
print("\n" + "="*80)
print("🧪 测试2: 缓存API (/tts_cached) - 使用speaker_id")
print("="*80)

times_cached = []
for i in range(ITERATIONS):
    print(f"[轮次 {i+1}/{ITERATIONS}]: ", end="", flush=True)
    
    start = time.time()
    response = requests.post(
        f"{API_BASE}/tts_cached",
        json={
            "text": TEST_TEXT,
            "speaker_id": speaker_id
        },
        timeout=60
    )
    elapsed = time.time() - start
    
    if response.status_code == 200:
        times_cached.append(elapsed)
        if i == 0:
            print(f"✅ {elapsed:.3f}s (首次)")
        else:
            print(f"✅ {elapsed:.3f}s")
    else:
        print(f"❌ 失败")

avg_cached = statistics.mean(remove_extremes(times_cached))
first_call = times_cached[0]
subsequent = statistics.mean(remove_extremes(times_cached[1:]))

print(f"\n📊 缓存API统计:")
print(f"   - 首次调用: {first_call:.3f}s")
print(f"   - 后续平均: {subsequent:.3f}s")
print(f"   - 整体平均: {avg_cached:.3f}s")

# 最终对比
print("\n" + "="*80)
print("📊 性能对比结果")
print("="*80)

improvement = (1 - avg_cached / avg_traditional) * 100

print("\n┌─────────────────┬──────────┬──────────┐")
print("│ API类型         │ 平均时间 │ 提升幅度 │")
print("├─────────────────┼──────────┼──────────┤")
print(f"│ 传统API (/tts)  │ {avg_traditional:>6.3f}s │ 基准线   │")
print(f"│ 缓存API (cached)│ {avg_cached:>6.3f}s │ {improvement:>5.1f}%  │")
print("└─────────────────┴──────────┴──────────┘")

print(f"\n📈 关键发现:")
if improvement > 0:
    print(f"   ✅ 缓存API比传统API快 {improvement:.1f}%")
else:
    print(f"   ⚠️  缓存API比传统API慢 {abs(improvement):.1f}%")

print(f"\n💡 结论:")
print(f"   - 传统API: 每次都需要处理音频文件路径")
print(f"   - 缓存API: 直接使用speaker_id，跳过文件处理")
print(f"   - 建议: 对于重复使用的说话人，使用缓存API可以提升性能")
