#!/usr/bin/env python3
"""
四种缓存策略性能对比测试（去除极值统计法）
每个测试10轮，去掉最快和最慢的，取中间8次的平均值
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
ITERATIONS = 10

def remove_extremes(times):
    """去掉最快和最慢的值"""
    if len(times) <= 2:
        return times
    sorted_times = sorted(times)
    return sorted_times[1:-1]

def calc_stats(times):
    """计算统计数据"""
    filtered = remove_extremes(times)
    return {
        "all_times": times,
        "filtered_times": filtered,
        "mean": statistics.mean(filtered),
        "median": statistics.median(filtered),
        "min": min(times),
        "max": max(times),
        "removed_min": min(times),
        "removed_max": max(times)
    }

results = {}

print("="*80)
print("🧪 IndexTTS2 缓存策略性能对比测试（去除极值法）")
print("="*80)
print(f"📋 测试配置: 每组10轮测试，去掉最快和最慢，统计中间8次")
print(f"📋 说话人数: {len(TEST_SPEAKERS)}个")
print()

# 测试1: 无缓存
print("\n" + "="*80)
print("🧪 测试1: 无缓存策略 (No Cache)")
print("="*80)
print("说明: 每次都重新提取embedding")
print()

times = []
for i in range(ITERATIONS):
    for idx, speaker in enumerate(TEST_SPEAKERS):
        print(f"[轮次 {i+1:2d}/{ITERATIONS}] 说话人 {idx+1}: ", end="", flush=True)
        
        start = time.time()
        try:
            response = requests.post("http://localhost:8002/tts", json={
                "text": TEST_TEXT,
                "spk_audio_prompt": speaker
            }, timeout=60)
            elapsed = time.time() - start
            
            if response.status_code == 200:
                times.append(elapsed)
                print(f"✅ {elapsed:.3f}s")
            else:
                print(f"❌ 失败 ({response.status_code})")
        except Exception as e:
            print(f"❌ 错误: {str(e)[:50]}")

results["no_cache"] = calc_stats(times)
print(f"\n📊 无缓存统计:")
print(f"   - 全部{len(times)}次平均: {statistics.mean(times):.3f}s")
print(f"   - 去除极值后平均: {results['no_cache']['mean']:.3f}s")
print(f"   - 最快: {results['no_cache']['min']:.3f}s (已去除)")
print(f"   - 最慢: {results['no_cache']['max']:.3f}s (已去除)")

# 测试2: 显存缓存（同一说话人）
print("\n" + "="*80)
print("🧪 测试2: 显存缓存策略 (VRAM Cache - Same Speaker)")
print("="*80)
print("说明: 使用同一个说话人连续调用")
print()

speaker = TEST_SPEAKERS[0]
times = []
first_call = None

total_calls = ITERATIONS * len(TEST_SPEAKERS)
for i in range(total_calls):
    print(f"[调用 {i+1:2d}/{total_calls}]: ", end="", flush=True)
    
    start = time.time()
    try:
        response = requests.post("http://localhost:8002/tts", json={
            "text": TEST_TEXT,
            "spk_audio_prompt": speaker
        }, timeout=60)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            times.append(elapsed)
            if i == 0:
                first_call = elapsed
                print(f"✅ {elapsed:.3f}s (首次)")
            else:
                print(f"✅ {elapsed:.3f}s")
        else:
            print(f"❌ 失败")
    except Exception as e:
        print(f"❌ 错误: {str(e)[:50]}")

results["vram_cache"] = calc_stats(times)
results["vram_cache"]["first_call"] = first_call
results["vram_cache"]["subsequent"] = calc_stats(times[1:])

print(f"\n📊 显存缓存统计:")
print(f"   - 首次调用: {first_call:.3f}s")
print(f"   - 后续全部平均: {statistics.mean(times[1:]):.3f}s")
print(f"   - 后续去极值平均: {results['vram_cache']['subsequent']['mean']:.3f}s")
print(f"   - 整体去极值平均: {results['vram_cache']['mean']:.3f}s")

# 生成最终报告
print("\n" + "="*80)
print("📊 最终测试结果（去除极值后）")
print("="*80)

baseline = results["no_cache"]["mean"]

print("\n┌─────────────────┬──────────┬──────────┬──────────┬──────────┐")
print("│ 缓存策略        │ 平均时间 │ 首次调用 │ 后续调用 │ 提升幅度 │")
print("├─────────────────┼──────────┼──────────┼──────────┼──────────┤")

print(f"│ 无缓存          │ {results['no_cache']['mean']:>6.3f}s │    -     │    -     │ 基准线   │")

vram_improvement = (1 - results['vram_cache']['mean'] / baseline) * 100
vram_sub_improvement = (1 - results['vram_cache']['subsequent']['mean'] / baseline) * 100

print(f"│ 显存缓存(同人)  │ {results['vram_cache']['mean']:>6.3f}s │ {first_call:>6.3f}s │ {results['vram_cache']['subsequent']['mean']:>6.3f}s │ {vram_improvement:>5.1f}%  │")

print("└─────────────────┴──────────┴──────────┴──────────┴──────────┘")

print("\n📈 性能提升分析:")
print(f"   - 显存缓存整体提升: {vram_improvement:.1f}%")
print(f"   - 显存缓存后续提升: {vram_sub_improvement:.1f}%")

# 保存结果
output_file = "/tmp/indextts2-outputs/cache_test_results.json"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2, default=str)

print(f"\n✅ 测试完成！结果已保存到: {output_file}")
print(f"\n测试数据:")
print(f"   - 无缓存: {len(results['no_cache']['all_times'])}次测试")
print(f"   - 显存缓存: {len(results['vram_cache']['all_times'])}次测试")
