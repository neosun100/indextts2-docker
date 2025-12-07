#!/usr/bin/env python3
"""
测试不同参数组合的性能和音质
生成音频文件供人工评估
"""
import requests
import time
import os
from pathlib import Path

API_BASE = "http://localhost:8002"
OUTPUT_DIR = "/tmp/indextts2-outputs/test_optimization"

# 测试文本
TEXTS = {
    "short": "你好，这是一个简短的测试。",
    "medium": "今天天气真不错，阳光明媚，微风习习。我们一起去公园散步吧。",
    "long": "人工智能技术正在快速发展，深度学习模型的能力越来越强大。语音合成技术也取得了突破性进展，现在可以生成非常自然流畅的语音。这项技术将会在很多领域得到广泛应用，比如智能客服、有声读物、语音助手等等。"
}

# 参数配置
CONFIGS = {
    "original": {
        "num_beams": 3,
        "top_k": 30,
        "do_sample": True,
        "diffusion_steps": 25,
        "description": "原版（基准）"
    },
    "conservative": {
        "num_beams": 1,
        "top_k": 20,
        "do_sample": True,
        "diffusion_steps": 15,
        "description": "保守方案"
    },
    "aggressive": {
        "num_beams": 1,
        "top_k": 10,
        "do_sample": True,
        "diffusion_steps": 10,
        "description": "激进方案"
    },
    "extreme": {
        "num_beams": 1,
        "top_k": 30,
        "do_sample": False,
        "diffusion_steps": 5,
        "description": "极限方案（贪婪解码）"
    }
}

# 创建输出目录
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

print("="*80)
print("🧪 IndexTTS2 参数优化测试")
print("="*80)
print(f"\n输出目录: {OUTPUT_DIR}")
print(f"测试配置: {len(CONFIGS)}个")
print(f"测试文本: {len(TEXTS)}段")
print(f"总计: {len(CONFIGS) * len(TEXTS)}个音频文件\n")

results = []

for config_name, config in CONFIGS.items():
    print(f"\n{'='*80}")
    print(f"📊 测试配置: {config['description']}")
    print(f"{'='*80}")
    print(f"参数: num_beams={config['num_beams']}, top_k={config['top_k']}, "
          f"do_sample={config['do_sample']}, diffusion_steps={config['diffusion_steps']}")
    print()
    
    for text_name, text in TEXTS.items():
        output_file = f"{OUTPUT_DIR}/{config_name}_{text_name}.wav"
        
        print(f"  [{text_name:8s}] ", end="", flush=True)
        
        start = time.time()
        try:
            # 注意：当前API不支持传递这些参数
            # 需要修改容器内的代码才能生效
            # 这里先用默认参数生成，作为对比基准
            response = requests.post(
                f"{API_BASE}/tts",
                json={
                    "text": text,
                    "spk_audio_prompt": "/app/examples/voice_01.wav"
                },
                timeout=120
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                
                file_size = len(response.content) / 1024
                print(f"✅ {elapsed:.2f}秒 ({file_size:.1f}KB) → {output_file}")
                
                results.append({
                    "config": config_name,
                    "text": text_name,
                    "time": elapsed,
                    "size": file_size,
                    "file": output_file
                })
            else:
                print(f"❌ 失败 ({response.status_code})")
        except Exception as e:
            print(f"❌ 错误: {str(e)[:50]}")

# 生成报告
print("\n" + "="*80)
print("📊 测试结果汇总")
print("="*80)

print("\n⚠️  重要提示:")
print("当前API不支持动态传递参数，所有测试使用相同的默认参数。")
print("要测试不同参数，需要修改容器内的代码。")
print("\n下一步:")
print("1. 我会创建修改参数的脚本")
print("2. 为每个配置重启容器并生成音频")
print("3. 你可以对比音质差异")

print(f"\n✅ 所有音频已保存到: {OUTPUT_DIR}")
print("\n可以使用以下命令播放:")
print(f"  ls -lh {OUTPUT_DIR}/*.wav")
