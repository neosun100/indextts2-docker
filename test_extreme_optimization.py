#!/usr/bin/env python3
"""
极限优化测试 - 调整所有可能影响速度的参数
"""
import requests
import time

API_BASE = "http://localhost:8002"
TEST_TEXT = "今天天气真不错，阳光明媚，微风习习。我们一起去公园散步吧。"
OUTPUT_DIR = "/tmp/indextts2-outputs/test_optimization"

# 测试配置
tests = [
    {
        "name": "原版基准",
        "params": {
            "num_beams": 3,
            "top_k": 30,
            "top_p": 0.8,
            "temperature": 0.8,
            "do_sample": True,
            "repetition_penalty": 10.0,
            "length_penalty": 0.0,
            "max_mel_tokens": 1500
        }
    },
    {
        "name": "优化版1-降低beams",
        "params": {
            "num_beams": 1,
            "top_k": 30,
            "top_p": 0.8,
            "temperature": 0.8,
            "do_sample": True,
            "repetition_penalty": 10.0,
            "length_penalty": 0.0,
            "max_mel_tokens": 1500
        }
    },
    {
        "name": "优化版2-贪婪解码",
        "params": {
            "num_beams": 1,
            "top_k": 1,
            "top_p": 1.0,
            "temperature": 1.0,
            "do_sample": False,  # 贪婪解码
            "repetition_penalty": 10.0,
            "length_penalty": 0.0,
            "max_mel_tokens": 1500
        }
    },
    {
        "name": "优化版3-降低max_mel",
        "params": {
            "num_beams": 1,
            "top_k": 10,
            "top_p": 0.9,
            "temperature": 1.0,
            "do_sample": True,
            "repetition_penalty": 10.0,
            "length_penalty": 0.0,
            "max_mel_tokens": 1000  # 从1500降到1000
        }
    },
    {
        "name": "极限版-全部最快",
        "params": {
            "num_beams": 1,
            "top_k": 1,
            "top_p": 1.0,
            "temperature": 1.0,
            "do_sample": False,
            "repetition_penalty": 5.0,  # 降低惩罚
            "length_penalty": 0.0,
            "max_mel_tokens": 1000
        }
    }
]

print("="*80)
print("🚀 IndexTTS2 极限优化测试")
print("="*80)
print(f"测试数量: {len(tests)}个")
print(f"测试文本: {TEST_TEXT}\n")

results = []

for i, test in enumerate(tests, 1):
    name = test['name']
    params = test['params']
    
    print(f"\n[{i}/{len(tests)}] {name}")
    print(f"  参数: beams={params['num_beams']}, k={params['top_k']}, "
          f"sample={params['do_sample']}, max_mel={params['max_mel_tokens']}")
    print(f"  ", end="", flush=True)
    
    start = time.time()
    try:
        response = requests.post(
            f"{API_BASE}/tts",
            json={
                "text": TEST_TEXT,
                "spk_audio_prompt": "/app/examples/voice_01.wav",
                **params
            },
            timeout=120
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            filename = f"extreme_{i}_{name.replace(' ', '_')}.wav"
            filepath = f"{OUTPUT_DIR}/{filename}"
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            size_kb = len(response.content) / 1024
            
            result = {
                "name": name,
                "time": round(elapsed, 2),
                "size_kb": round(size_kb, 1),
                "file": filename,
                **params
            }
            results.append(result)
            
            print(f"✅ {elapsed:.2f}秒 ({size_kb:.1f}KB)")
        else:
            print(f"❌ 失败 ({response.status_code})")
    except Exception as e:
        print(f"❌ 错误: {str(e)[:60]}")

# 生成报告
if results:
    print("\n" + "="*80)
    print("📊 测试结果对比")
    print("="*80)
    
    baseline_time = results[0]['time']
    
    print("\n┌────┬─────────────────────┬──────────┬──────────┐")
    print("│ #  │ 配置                │ 时间(秒) │ 提升(%)  │")
    print("├────┼─────────────────────┼──────────┼──────────┤")
    
    for i, r in enumerate(results, 1):
        improvement = ((baseline_time - r['time']) / baseline_time * 100)
        print(f"│ {i}  │ {r['name']:19s} │ {r['time']:8.2f} │ {improvement:7.1f}% │")
    
    print("└────┴─────────────────────┴──────────┴──────────┘")
    
    # 找出最快的
    fastest = min(results[1:], key=lambda x: x['time'])
    improvement = ((baseline_time - fastest['time']) / baseline_time * 100)
    
    print(f"\n🏆 最快配置: {fastest['name']}")
    print(f"   时间: {fastest['time']:.2f}秒 (快{improvement:.0f}%)")
    print(f"   参数:")
    print(f"     - num_beams: {fastest['num_beams']}")
    print(f"     - top_k: {fastest['top_k']}")
    print(f"     - do_sample: {fastest['do_sample']}")
    print(f"     - max_mel_tokens: {fastest['max_mel_tokens']}")
    print(f"   文件: {fastest['file']}")
    
    print(f"\n✅ 所有音频文件: {OUTPUT_DIR}/extreme_*.wav")
    print("\n📝 下一步: 播放音频对比音质，选择可接受的最快配置")
else:
    print("\n⚠️  没有成功的测试结果")
