#!/usr/bin/env python3
"""
最终版参数测试脚本
文件名格式: T{ID}_{time}s_b{beams}_k{topk}_s{sample}.wav
"""
import requests
import time
import json
from pathlib import Path

API_BASE = "http://localhost:8002"
OUTPUT_DIR = "/tmp/indextts2-outputs/test_optimization"
TEST_TEXT = "今天天气真不错，阳光明媚，微风习习。我们一起去公园散步吧。"

# 细粒度测试矩阵
TESTS = [
    # 阶段1: num_beams测试（最关键）
    {"id": "T01", "num_beams": 3, "top_k": 30, "do_sample": True, "desc": "基准(beams=3)"},
    {"id": "T02", "num_beams": 2, "top_k": 30, "do_sample": True, "desc": "beams=2"},
    {"id": "T03", "num_beams": 1, "top_k": 30, "do_sample": True, "desc": "beams=1"},
    
    # 阶段2: top_k测试（基于beams=1）
    {"id": "T04", "num_beams": 1, "top_k": 30, "do_sample": True, "desc": "k=30"},
    {"id": "T05", "num_beams": 1, "top_k": 20, "do_sample": True, "desc": "k=20"},
    {"id": "T06", "num_beams": 1, "top_k": 15, "do_sample": True, "desc": "k=15"},
    {"id": "T07", "num_beams": 1, "top_k": 10, "do_sample": True, "desc": "k=10"},
    {"id": "T08", "num_beams": 1, "top_k": 5, "do_sample": True, "desc": "k=5"},
    
    # 阶段3: do_sample测试
    {"id": "T09", "num_beams": 1, "top_k": 20, "do_sample": True, "desc": "采样模式"},
    {"id": "T10", "num_beams": 1, "top_k": 20, "do_sample": False, "desc": "贪婪模式"},
    
    # 阶段4: 推荐组合
    {"id": "T11", "num_beams": 1, "top_k": 20, "do_sample": True, "desc": "保守推荐"},
    {"id": "T12", "num_beams": 1, "top_k": 10, "do_sample": True, "desc": "激进推荐"},
    {"id": "T13", "num_beams": 1, "top_k": 10, "do_sample": False, "desc": "极限推荐"},
]

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

print("="*80)
print("🧪 IndexTTS2 参数优化测试（GPU2）")
print("="*80)
print(f"\n测试数量: {len(TESTS)}个")
print(f"输出目录: {OUTPUT_DIR}")
print(f"测试文本: {TEST_TEXT}")
print(f"\n文件命名: T{{ID}}_{{time}}s_b{{beams}}_k{{topk}}_s{{sample}}.wav")
print("="*80)

results = []

for i, test in enumerate(TESTS, 1):
    test_id = test['id']
    desc = test['desc']
    
    print(f"\n[{i}/{len(TESTS)}] {test_id}: {desc}")
    print(f"  参数: beams={test['num_beams']}, k={test['top_k']}, sample={test['do_sample']}")
    print(f"  进度: ", end="", flush=True)
    
    start = time.time()
    try:
        response = requests.post(
            f"{API_BASE}/tts",
            json={
                "text": TEST_TEXT,
                "spk_audio_prompt": "/app/examples/voice_01.wav",
                **{k: v for k, v in test.items() if k not in ['id', 'desc']}
            },
            timeout=120
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            # 文件名包含时间和参数
            sample_str = "T" if test['do_sample'] else "F"
            filename = f"{test_id}_{elapsed:.1f}s_b{test['num_beams']}_k{test['top_k']}_s{sample_str}.wav"
            filepath = f"{OUTPUT_DIR}/{filename}"
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            size_kb = len(response.content) / 1024
            
            result = {
                **test,
                "time": round(elapsed, 2),
                "size_kb": round(size_kb, 1),
                "file": filename,
                "path": filepath
            }
            results.append(result)
            
            print(f"✅ {elapsed:.2f}秒 ({size_kb:.1f}KB)")
            print(f"     文件: {filename}")
        else:
            print(f"❌ 失败 ({response.status_code})")
    except Exception as e:
        print(f"❌ 错误: {str(e)[:60]}")

# 生成详细报告
if results:
    print("\n" + "="*80)
    print("📊 测试结果汇总")
    print("="*80)
    
    print("\n┌──────┬──────────────────┬────────┬────────┬─────────┬──────────┬──────────┐")
    print("│ ID   │ 说明             │ beams  │ top_k  │ sample  │ 时间(秒) │ 提升(%)  │")
    print("├──────┼──────────────────┼────────┼────────┼─────────┼──────────┼──────────┤")
    
    baseline_time = results[0]['time']
    for r in results:
        improvement = ((baseline_time - r['time']) / baseline_time * 100)
        sample_str = "True " if r['do_sample'] else "False"
        print(f"│ {r['id']:4s} │ {r['desc']:16s} │ {r['num_beams']:6d} │ {r['top_k']:6d} │ {sample_str:7s} │ {r['time']:8.2f} │ {improvement:7.1f}% │")
    
    print("└──────┴──────────────────┴────────┴────────┴─────────┴──────────┴──────────┘")
    
    # 找出最优配置
    print("\n🏆 推荐配置:")
    sorted_results = sorted(results[1:], key=lambda x: x['time'])  # 排除基准
    for i, r in enumerate(sorted_results[:3], 1):
        improvement = ((baseline_time - r['time']) / baseline_time * 100)
        print(f"  {i}. {r['id']} ({r['desc']}): {r['time']:.2f}秒 (快{improvement:.0f}%)")
        print(f"     参数: beams={r['num_beams']}, k={r['top_k']}, sample={r['do_sample']}")
        print(f"     文件: {r['file']}")
    
    # 保存JSON报告
    report_file = f"{OUTPUT_DIR}/test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "baseline_time": baseline_time,
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 详细报告: {report_file}")
    print(f"✅ 音频文件: {OUTPUT_DIR}/*.wav")
    
    print("\n📝 下一步:")
    print("1. 播放音频文件，评估音质（文件名已包含参数信息）")
    print("2. 选择音质可接受且速度最快的配置")
    print("3. 部署该配置到生产环境")
else:
    print("\n⚠️  没有成功的测试结果")
    print("请检查服务是否正常运行: curl http://localhost:8002/health")
