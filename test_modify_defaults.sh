#!/bin/bash
# 直接修改容器内的默认参数进行测试

echo "🔧 修改IndexTTS2默认参数测试"
echo "================================"
echo ""

# 测试配置
declare -A TESTS=(
    ["T01_baseline"]="3 30"      # beams=3, top_k=30 (原版)
    ["T02_beams1"]="1 30"        # beams=1, top_k=30
    ["T03_k20"]="1 20"           # beams=1, top_k=20
    ["T04_k15"]="1 15"           # beams=1, top_k=15
    ["T05_k10"]="1 10"           # beams=1, top_k=10
)

TEST_TEXT="今天天气真不错，阳光明媚，微风习习。我们一起去公园散步吧。"
OUTPUT_DIR="/tmp/indextts2-outputs/test_optimization"

for test_name in "${!TESTS[@]}"; do
    params=(${TESTS[$test_name]})
    beams=${params[0]}
    topk=${params[1]}
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "测试: $test_name"
    echo "参数: num_beams=$beams, top_k=$topk"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 修改容器内的默认参数
    docker exec indextts2-api-gpu2 bash -c "
        sed -i 's/num_beams = generation_kwargs.pop(\"num_beams\", [0-9]*)/num_beams = generation_kwargs.pop(\"num_beams\", $beams)/' /app/indextts/infer_v2.py
        sed -i 's/top_k = generation_kwargs.pop(\"top_k\", [0-9]*)/top_k = generation_kwargs.pop(\"top_k\", $topk)/' /app/indextts/infer_v2.py
    "
    
    # 重启服务
    echo "  重启服务..."
    docker restart indextts2-api-gpu2 > /dev/null 2>&1
    sleep 90  # 等待服务启动
    
    # 测试
    echo "  生成音频..."
    start_time=$(date +%s.%N)
    
    curl -s -X POST http://localhost:8002/tts \
        -H "Content-Type: application/json" \
        -d "{\"text\": \"$TEST_TEXT\", \"spk_audio_prompt\": \"/app/examples/voice_01.wav\"}" \
        -o "$OUTPUT_DIR/${test_name}_b${beams}_k${topk}.wav"
    
    end_time=$(date +%s.%N)
    elapsed=$(echo "$end_time - $start_time" | bc)
    
    # 获取详细耗时
    gpt_time=$(docker logs indextts2-api-gpu2 2>&1 | grep "gpt_gen_time" | tail -1 | awk '{print $3}')
    
    echo "  ✅ 完成: ${elapsed}秒 (GPT: ${gpt_time}秒)"
    echo "  文件: ${test_name}_b${beams}_k${topk}.wav"
    echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 测试完成！"
echo "音频文件: $OUTPUT_DIR/*.wav"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
