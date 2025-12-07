#!/usr/bin/env python3
"""
细粒度参数测试脚本
生成17个不同参数组合的音频文件
"""
import requests
import time
import json
from pathlib import Path

API_BASE = "http://localhost:8002"
OUTPUT_DIR = "/tmp/indextts2-outputs/test_optimization"
TEST_TEXT = "今天天气真不错，阳光明媚，微风习习。我们一起去公园散步吧。"

# 测试矩阵
TESTS = [
    # 阶段1: num_beams测试
    {"id": "T01", "num_beams": 3, "top_k": 30, "do_sample": True, "desc": "基准"},
    {"id": "T02", "num_beams": 2, "top_k": 30, "do_sample": True, "desc": "beams=2"},
    {"id": "T03", "num_beams": 1, "top_k": 30, "do_sample": True, "desc": "beams=1"},
    
    # 阶段2: top_k测试
    {"id": "T04", "num_beams": 1, "top_k": 30, "do_sample": True, "desc": "k=30"},
    {"id": "T05", "num_beams": 1, "top_k": 20, "do_sample": True, "desc": "k=20"},
    {"id": "T06", "num_beams": 1, "top_k": 10, "do_sample": True, "desc": "k=10"},
    {"id": "T07", "num_beams": 1, "top_k": 5, "do_sample": True, "desc": "k=5"},
    
    # 阶段3: do_sample测试
    {"id": "T08", "num_beams": 1, "top_k": 20, "do_sample": True, "desc": "sample=True"},
    {"id": "T09", "num_beams": 1, "top_k": 20, "do_sample": False, "desc": "sample=False(贪婪)"},
    
    # 阶段4: 组合测试
    {"id": "T10", "num_beams": 1, "top_k": 20, "do_sample": True, "desc": "保守组合"},
    {"id": "T11", "num_beams": 1, "top_k": 10, "do_sample": True, "desc": "激进组合"},
    {"id": "T12", "num_beams": 1, "top_k": 10, "do_sample": False, "desc": "极限组合"},
]

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

print("="*80)
print("🧪 IndexTTS2 细粒度参数测试")
print("="*80)
print(f"\n测试数量: {len(TESTS)}个")
print(f"输出目录: {OUTPUT_DIR}")
print(f"测试文本: {TEST_TEXT}\n")

results = []

for test in TESTS:
    test_id = test['id']
    desc = test['desc']
    
    print(f"\n[{test_id}] {desc}")
    print(f"  参数: beams={test['num_beams']}, k={test['top_k']}, sample={test['do_sample']}")
    print(f"  ", end="", flush=True)
    
    start = time.time()
    try:
        response = requests.post(
            f"{API_BASE}/tts_tunable",
            json={
                "text": TEST_TEXT,
                "spk_audio_prompt": "/app/examples/voice_01.wav",
                "test_id": test_id,
                **test
            },
            timeout=120
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            filename = f"{test_id}_b{test['num_beams']}_k{test['top_k']}_s{test['do_sample']}.wav"
            filepath = f"{OUTPUT_DIR}/{filename}"
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            size_kb = len(response.content) / 1024
            
            result = {
                **test,
                "time": round(elapsed, 2),
                "size_kb": round(size_kb, 1),
                "file": filepath
            }
            results.append(result)
            
            print(f"✅ {elapsed:.2f}秒 ({size_kb:.1f}KB)")
        else:
            print(f"❌ 失败 ({response.status_code})")
            if response.status_code == 404:
                print("     提示: API端点不存在，需要先添加 /tts_tunable 端点")
                break
    except Exception as e:
        print(f"❌ 错误: {str(e)[:60]}")

# 生成汇总报告
if results:
    print("\n" + "="*80)
    print("📊 测试结果汇总")
    print("="*80)
    
    print("\n┌─────┬──────────────┬────────┬────────┬─────────┬──────────┐")
    print("│ ID  │ 说明         │ beams  │ top_k  │ sample  │ 时间(秒) │")
    print("├─────┼──────────────┼────────┼────────┼─────────┼──────────┤")
    
    baseline_time = results[0]['time']
    for r in results:
        improvement = ((baseline_time - r['time']) / baseline_time * 100) if r['time'] < baseline_time else 0
        sample_str = "T" if r['do_sample'] else "F"
        print(f"│ {r['id']:3s} │ {r['desc']:12s} │ {r['num_beams']:6d} │ {r['top_k']:6d} │ {sample_str:7s} │ {r['time']:6.2f}秒 │")
    
    print("└─────┴──────────────┴────────┴────────┴─────────┴──────────┘")
    
    # 保存JSON报告
    report_file = f"{OUTPUT_DIR}/test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 详细报告已保存: {report_file}")
    print(f"✅ 所有音频文件: {OUTPUT_DIR}/*.wav")
    print("\n📝 下一步:")
    print("1. 播放音频文件，评估音质")
    print("2. 找出音质可接受且速度最快的配置")
    print("3. 部署该配置")
else:
    print("\n⚠️  没有成功的测试结果")
    print("\n需要先添加 /tts_tunable API端点:")
    print("1. 将 add_params_api.py 的内容添加到容器内的 api_server_cached_optimized.py")
    print("2. 重启容器")
    print("3. 重新运行此脚本")
