#!/usr/bin/env python3
"""
精简参数网格搜索 - 只测试影响速度的参数
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
ITERATIONS = 3

# 影响速度的参数（剔除无关参数）
PARAM_GRID = {
    # 核心参数 - 影响GPT生成速度
    "num_beams": [3, 2, 1],           # Beam search数量，影响最大
    "do_sample": [True, False],        # 采样vs贪婪，影响中等
    "top_k": [30, 10, 1],             # 采样范围，影响较小
    "max_mel_tokens": [1500, 1000],   # 最大生成长度，可能影响
    
    # 固定参数（对速度影响很小或无影响）
    # top_p: 0.8 (固定)
    # temperature: 0.8 (固定)
    # repetition_penalty: 10.0 (固定，只影响质量)
    # length_penalty: 0.0 (固定，只影响质量)
}

all_combinations = list(product(
    PARAM_GRID["num_beams"],
    PARAM_GRID["do_sample"],
    PARAM_GRID["top_k"],
    PARAM_GRID["max_mel_tokens"]
))

print("="*80)
print("🔬 IndexTTS2 精简参数网格搜索")
print("="*80)
print(f"\n测试参数:")
print(f"  ✅ num_beams: {PARAM_GRID['num_beams']} (影响最大)")
print(f"  ✅ do_sample: {PARAM_GRID['do_sample']} (影响中等)")
print(f"  ✅ top_k: {PARAM_GRID['top_k']} (影响较小)")
print(f"  ✅ max_mel_tokens: {PARAM_GRID['max_mel_tokens']} (可能影响)")
print(f"\n固定参数:")
print(f"  ⊗ top_p: 0.8")
print(f"  ⊗ temperature: 0.8")
print(f"  ⊗ repetition_penalty: 10.0")
print(f"  ⊗ length_penalty: 0.0")
print(f"\n总组合数: {len(all_combinations)}")
print(f"每组测试: {ITERATIONS}次")
print(f"总测试数: {len(all_combinations) * ITERATIONS}")
print(f"预计时间: ~{len(all_combinations) * ITERATIONS * 7 / 60:.0f}分钟")
print("="*80)

results = []
test_id = 0

for beams, sample, topk, max_mel in all_combinations:
    test_id += 1
    
    config = {
        "num_beams": beams,
        "do_sample": sample,
        "top_k": topk,
        "max_mel_tokens": max_mel,
        "top_p": 0.8,
        "temperature": 0.8,
        "repetition_penalty": 10.0,
        "length_penalty": 0.0
    }
    
    sample_str = "T" if sample else "F"
    config_name = f"b{beams}_s{sample_str}_k{topk}_m{max_mel}"
    
    print(f"\n[{test_id:2d}/{len(all_combinations)}] {config_name:20s}", end=" ")
    
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
                print(f"{elapsed:.2f} ", end="", flush=True)
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
        
        print(f"→ avg:{avg_time:.2f}s")
    else:
        print("→ FAILED")

# 保存结果
report_file = f"{OUTPUT_DIR}/grid_search_results.json"
with open(report_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

# 排序
sorted_results = sorted(results, key=lambda x: x['avg_time'])

print("\n" + "="*80)
print("📊 Top 15 最快配置")
print("="*80)

baseline = next((r for r in results if r['params']['num_beams']==3 and r['params']['do_sample']==True and r['params']['top_k']==30 and r['params']['max_mel_tokens']==1500), None)
baseline_time = baseline['avg_time'] if baseline else sorted_results[-1]['avg_time']

print(f"\n基准配置: b3_sT_k30_m1500 = {baseline_time:.3f}s\n")

print("┌────┬──────────────────────┬──────────┬──────────┬──────────┐")
print("│ #  │ 配置                 │ 平均(秒) │ 标准差   │ 提升(%)  │")
print("├────┼──────────────────────┼──────────┼──────────┼──────────┤")

for i, r in enumerate(sorted_results[:15], 1):
    improvement = ((baseline_time - r['avg_time']) / baseline_time * 100)
    print(f"│ {i:2d} │ {r['config']:20s} │ {r['avg_time']:8.3f} │ {r['std_time']:8.3f} │ {improvement:7.1f}% │")

print("└────┴──────────────────────┴──────────┴──────────┴──────────┘")

# 参数影响分析
print("\n" + "="*80)
print("📈 单参数影响分析")
print("="*80)

print("\n🔹 num_beams影响:")
for beams in sorted(PARAM_GRID["num_beams"], reverse=True):
    beam_results = [r for r in results if r['params']['num_beams'] == beams]
    if beam_results:
        avg = statistics.mean([r['avg_time'] for r in beam_results])
        improvement = ((baseline_time - avg) / baseline_time * 100)
        print(f"  beams={beams}: {avg:.3f}s (平均, {improvement:+.1f}%)")

print("\n🔹 do_sample影响:")
for sample in [True, False]:
    sample_results = [r for r in results if r['params']['do_sample'] == sample]
    if sample_results:
        avg = statistics.mean([r['avg_time'] for r in sample_results])
        improvement = ((baseline_time - avg) / baseline_time * 100)
        sample_str = "True " if sample else "False"
        print(f"  sample={sample_str}: {avg:.3f}s (平均, {improvement:+.1f}%)")

print("\n🔹 top_k影响:")
for topk in sorted(PARAM_GRID["top_k"], reverse=True):
    topk_results = [r for r in results if r['params']['top_k'] == topk]
    if topk_results:
        avg = statistics.mean([r['avg_time'] for r in topk_results])
        improvement = ((baseline_time - avg) / baseline_time * 100)
        print(f"  top_k={topk:2d}: {avg:.3f}s (平均, {improvement:+.1f}%)")

print("\n🔹 max_mel_tokens影响:")
for max_mel in sorted(PARAM_GRID["max_mel_tokens"], reverse=True):
    mel_results = [r for r in results if r['params']['max_mel_tokens'] == max_mel]
    if mel_results:
        avg = statistics.mean([r['avg_time'] for r in mel_results])
        improvement = ((baseline_time - avg) / baseline_time * 100)
        print(f"  max_mel={max_mel}: {avg:.3f}s (平均, {improvement:+.1f}%)")

# 推荐配置
print("\n" + "="*80)
print("🏆 推荐配置")
print("="*80)

fastest = sorted_results[0]
improvement = ((baseline_time - fastest['avg_time']) / baseline_time * 100)

print(f"\n最快配置: {fastest['config']}")
print(f"平均时间: {fastest['avg_time']:.3f}s (±{fastest['std_time']:.3f}s)")
print(f"性能提升: {improvement:.1f}%")
print(f"测试次数: {len(fastest['times'])}次")
print(f"时间范围: {fastest['min_time']:.3f}s ~ {fastest['max_time']:.3f}s")
print(f"\n参数设置:")
print(f"  num_beams: {fastest['params']['num_beams']}")
print(f"  do_sample: {fastest['params']['do_sample']}")
print(f"  top_k: {fastest['params']['top_k']}")
print(f"  max_mel_tokens: {fastest['params']['max_mel_tokens']}")

print(f"\n✅ 完整报告: {report_file}")
print(f"\n📝 下一步: 生成Top 5配置的音频文件供音质对比")
