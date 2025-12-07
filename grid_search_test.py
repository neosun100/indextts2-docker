#!/usr/bin/env python3
"""
系统化参数网格搜索
每个配置测试3次，取平均值
"""
import requests
import time
import json
import statistics
from itertools import product

API_BASE = "http://localhost:8002"
TEST_TEXT = "今天天气真不错，阳光明媚，微风习习。我们一起去公园散步吧。"
OUTPUT_DIR = "/tmp/indextts2-outputs/test_optimization"
ITERATIONS = 3  # 每个配置测试3次

# 参数网格
PARAM_GRID = {
    "num_beams": [3, 2, 1],
    "top_k": [30, 20, 10, 5, 1],
    "do_sample": [True, False],
    "temperature": [1.0, 0.8],
    "max_mel_tokens": [1500, 1000]
}

# 生成所有组合
all_combinations = list(product(
    PARAM_GRID["num_beams"],
    PARAM_GRID["top_k"],
    PARAM_GRID["do_sample"],
    PARAM_GRID["temperature"],
    PARAM_GRID["max_mel_tokens"]
))

print("="*80)
print("🔬 IndexTTS2 参数网格搜索")
print("="*80)
print(f"参数空间:")
print(f"  - num_beams: {PARAM_GRID['num_beams']}")
print(f"  - top_k: {PARAM_GRID['top_k']}")
print(f"  - do_sample: {PARAM_GRID['do_sample']}")
print(f"  - temperature: {PARAM_GRID['temperature']}")
print(f"  - max_mel_tokens: {PARAM_GRID['max_mel_tokens']}")
print(f"\n总组合数: {len(all_combinations)}")
print(f"每组测试: {ITERATIONS}次")
print(f"总测试数: {len(all_combinations) * ITERATIONS}")
print(f"预计时间: ~{len(all_combinations) * ITERATIONS * 7 / 60:.0f}分钟")
print("="*80)

results = []
test_id = 0

for beams, topk, sample, temp, max_mel in all_combinations:
    test_id += 1
    
    config = {
        "num_beams": beams,
        "top_k": topk,
        "do_sample": sample,
        "temperature": temp,
        "max_mel_tokens": max_mel,
        "top_p": 0.8,
        "repetition_penalty": 10.0,
        "length_penalty": 0.0
    }
    
    sample_str = "T" if sample else "F"
    config_name = f"b{beams}_k{topk}_s{sample_str}_t{temp}_m{max_mel}"
    
    print(f"\n[{test_id}/{len(all_combinations)}] {config_name}")
    print(f"  ", end="", flush=True)
    
    times = []
    for i in range(ITERATIONS):
        try:
            start = time.time()
            response = requests.post(
                f"{API_BASE}/tts",
                json={
                    "text": TEST_TEXT,
                    "spk_audio_prompt": "/app/examples/voice_01.wav",
                    **config
                },
                timeout=120
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                times.append(elapsed)
                print(f"{elapsed:.2f}s ", end="", flush=True)
            else:
                print(f"ERR ", end="", flush=True)
        except Exception as e:
            print(f"FAIL ", end="", flush=True)
    
    if times:
        avg_time = statistics.mean(times)
        std_time = statistics.stdev(times) if len(times) > 1 else 0
        
        result = {
            "id": test_id,
            "config": config_name,
            "params": config,
            "times": times,
            "avg_time": round(avg_time, 3),
            "std_time": round(std_time, 3),
            "min_time": round(min(times), 3),
            "max_time": round(max(times), 3)
        }
        results.append(result)
        
        print(f"→ 平均: {avg_time:.2f}s (±{std_time:.2f}s)")
    else:
        print("→ 全部失败")

# 保存完整结果
report_file = f"{OUTPUT_DIR}/grid_search_results.json"
with open(report_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

# 按速度排序
sorted_results = sorted(results, key=lambda x: x['avg_time'])

print("\n" + "="*80)
print("📊 Top 10 最快配置")
print("="*80)

print("\n┌────┬─────────────────────────────┬──────────┬──────────┬──────────┐")
print("│ #  │ 配置                        │ 平均时间 │ 标准差   │ 提升(%)  │")
print("├────┼─────────────────────────────┼──────────┼──────────┼──────────┤")

baseline_time = next((r['avg_time'] for r in results if r['params']['num_beams'] == 3 and r['params']['top_k'] == 30), None)

for i, r in enumerate(sorted_results[:10], 1):
    improvement = ((baseline_time - r['avg_time']) / baseline_time * 100) if baseline_time else 0
    print(f"│ {i:2d} │ {r['config']:27s} │ {r['avg_time']:8.3f} │ {r['std_time']:8.3f} │ {improvement:7.1f}% │")

print("└────┴─────────────────────────────┴──────────┴──────────┴──────────┘")

# 参数影响分析
print("\n" + "="*80)
print("📈 参数影响分析")
print("="*80)

# 按num_beams分组
print("\n🔹 num_beams影响:")
for beams in PARAM_GRID["num_beams"]:
    beam_results = [r for r in results if r['params']['num_beams'] == beams]
    if beam_results:
        avg = statistics.mean([r['avg_time'] for r in beam_results])
        print(f"  beams={beams}: {avg:.3f}s (平均)")

# 按top_k分组
print("\n🔹 top_k影响:")
for topk in PARAM_GRID["top_k"]:
    topk_results = [r for r in results if r['params']['top_k'] == topk]
    if topk_results:
        avg = statistics.mean([r['avg_time'] for r in topk_results])
        print(f"  top_k={topk:2d}: {avg:.3f}s (平均)")

# 按do_sample分组
print("\n🔹 do_sample影响:")
for sample in PARAM_GRID["do_sample"]:
    sample_results = [r for r in results if r['params']['do_sample'] == sample]
    if sample_results:
        avg = statistics.mean([r['avg_time'] for r in sample_results])
        sample_str = "True " if sample else "False"
        print(f"  sample={sample_str}: {avg:.3f}s (平均)")

# 推荐配置
print("\n" + "="*80)
print("🏆 推荐配置")
print("="*80)

fastest = sorted_results[0]
improvement = ((baseline_time - fastest['avg_time']) / baseline_time * 100) if baseline_time else 0

print(f"\n最快配置: {fastest['config']}")
print(f"平均时间: {fastest['avg_time']:.3f}s (±{fastest['std_time']:.3f}s)")
print(f"性能提升: {improvement:.1f}%")
print(f"\n参数设置:")
for key, value in fastest['params'].items():
    print(f"  {key}: {value}")

print(f"\n✅ 完整报告: {report_file}")
print(f"\n📝 下一步: 生成Top 10配置的音频文件供音质对比")
