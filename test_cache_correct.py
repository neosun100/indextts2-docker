#!/usr/bin/env python3
"""
正确的缓存策略测试
对比: 5个说话人在有缓存和无缓存情况下的性能差异
"""
import time
import requests
import statistics
import json

TEST_SPEAKERS = [
    "/app/examples/voice_01.wav",
    "/app/examples/voice_02.wav",
    "/app/examples/voice_03.wav",
    "/app/examples/voice_04.wav",
    "/app/examples/voice_05.wav",
]
TEST_TEXT = "这是一个性能测试，用于对比不同缓存策略的速度差异。"
ITERATIONS = 5

def remove_extremes(times):
    """去掉最快和最慢的值"""
    if len(times) <= 2:
        return times
    sorted_times = sorted(times)
    return sorted_times[1:-1]

results = {}

print("="*80)
print("🧪 IndexTTS2 缓存策略正确测试")
print("="*80)
print(f"📋 场景: 5个不同说话人，每人调用10次")
print(f"📋 对比: 有缓存 vs 无缓存")
print()

# 测试1: 无缓存 - 每次都重新提取
print("\n" + "="*80)
print("🧪 测试1: 无缓存策略")
print("="*80)
print("说明: 每次调用都重新提取embedding（模拟禁用缓存）")
print()

# 先清空缓存
print("🧹 清空IndexTTS2内部缓存...")
requests.post("http://localhost:8002/tts", json={
    "text": "清空缓存",
    "spk_audio_prompt": "/app/examples/voice_12.wav"
})

no_cache_times = {}
for speaker_idx, speaker in enumerate(TEST_SPEAKERS):
    print(f"\n说话人 {speaker_idx+1}: {speaker.split('/')[-1]}")
    times = []
    
    for i in range(ITERATIONS):
        # 每次调用前都切换到不同的说话人，强制重新提取
        dummy_speaker = TEST_SPEAKERS[(speaker_idx + 1) % len(TEST_SPEAKERS)]
        requests.post("http://localhost:8002/tts", json={
            "text": "dummy",
            "spk_audio_prompt": dummy_speaker
        }, timeout=60)
        
        print(f"  轮次 {i+1:2d}: ", end="", flush=True)
        start = time.time()
        
        response = requests.post("http://localhost:8002/tts", json={
            "text": TEST_TEXT,
            "spk_audio_prompt": speaker
        }, timeout=60)
        
        elapsed = time.time() - start
        
        if response.status_code == 200:
            times.append(elapsed)
            print(f"✅ {elapsed:.3f}s")
        else:
            print(f"❌ 失败")
    
    no_cache_times[speaker] = times

# 统计无缓存结果
all_no_cache = []
for times in no_cache_times.values():
    all_no_cache.extend(times)

results["no_cache"] = {
    "all_times": all_no_cache,
    "filtered": remove_extremes(all_no_cache),
    "mean": statistics.mean(remove_extremes(all_no_cache))
}

print(f"\n📊 无缓存统计:")
print(f"   - 总测试: {len(all_no_cache)}次")
print(f"   - 去极值平均: {results['no_cache']['mean']:.3f}s")

# 测试2: 有缓存 - 第一次提取，后续使用缓存
print("\n" + "="*80)
print("🧪 测试2: 有缓存策略")
print("="*80)
print("说明: 每个说话人首次提取embedding，后续直接使用缓存")
print()

# 清空缓存
print("🧹 清空IndexTTS2内部缓存...")
requests.post("http://localhost:8002/tts", json={
    "text": "清空缓存",
    "spk_audio_prompt": "/app/examples/voice_12.wav"
})

cache_times = {}
first_calls = []
subsequent_calls = []

for speaker_idx, speaker in enumerate(TEST_SPEAKERS):
    print(f"\n说话人 {speaker_idx+1}: {speaker.split('/')[-1]}")
    times = []
    
    for i in range(ITERATIONS):
        print(f"  轮次 {i+1:2d}: ", end="", flush=True)
        start = time.time()
        
        response = requests.post("http://localhost:8002/tts", json={
            "text": TEST_TEXT,
            "spk_audio_prompt": speaker
        }, timeout=60)
        
        elapsed = time.time() - start
        
        if response.status_code == 200:
            times.append(elapsed)
            if i == 0:
                first_calls.append(elapsed)
                print(f"✅ {elapsed:.3f}s (首次)")
            else:
                subsequent_calls.append(elapsed)
                print(f"✅ {elapsed:.3f}s (缓存)")
        else:
            print(f"❌ 失败")
    
    cache_times[speaker] = times

# 统计有缓存结果
all_cache = []
for times in cache_times.values():
    all_cache.extend(times)

results["with_cache"] = {
    "all_times": all_cache,
    "filtered": remove_extremes(all_cache),
    "mean": statistics.mean(remove_extremes(all_cache)),
    "first_calls": first_calls,
    "first_mean": statistics.mean(remove_extremes(first_calls)),
    "subsequent": subsequent_calls,
    "subsequent_mean": statistics.mean(remove_extremes(subsequent_calls))
}

print(f"\n📊 有缓存统计:")
print(f"   - 总测试: {len(all_cache)}次")
print(f"   - 首次调用平均: {results['with_cache']['first_mean']:.3f}s")
print(f"   - 后续调用平均: {results['with_cache']['subsequent_mean']:.3f}s")
print(f"   - 整体去极值平均: {results['with_cache']['mean']:.3f}s")

# 最终报告
print("\n" + "="*80)
print("📊 最终测试结果（去除极值后）")
print("="*80)

baseline = results["no_cache"]["mean"]
cache_mean = results["with_cache"]["mean"]
improvement = (1 - cache_mean / baseline) * 100

print("\n┌─────────────────┬──────────┬──────────┬──────────┬──────────┐")
print("│ 策略            │ 平均时间 │ 首次调用 │ 后续调用 │ 提升幅度 │")
print("├─────────────────┼──────────┼──────────┼──────────┼──────────┤")
print(f"│ 无缓存          │ {baseline:>6.3f}s │    -     │    -     │ 基准线   │")
print(f"│ 有缓存          │ {cache_mean:>6.3f}s │ {results['with_cache']['first_mean']:>6.3f}s │ {results['with_cache']['subsequent_mean']:>6.3f}s │ {improvement:>5.1f}%  │")
print("└─────────────────┴──────────┴──────────┴──────────┴──────────┘")

print(f"\n📈 关键指标:")
print(f"   - 首次调用（需提取embedding）: {results['with_cache']['first_mean']:.3f}s")
print(f"   - 后续调用（使用缓存）: {results['with_cache']['subsequent_mean']:.3f}s")
print(f"   - 缓存节省时间: {results['with_cache']['first_mean'] - results['with_cache']['subsequent_mean']:.3f}s")
print(f"   - 整体性能提升: {improvement:.1f}%")

# 保存结果
output_file = "/home/neo/upload/index-tts/cache_test_correct_results.json"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✅ 测试完成！结果已保存到: {output_file}")
