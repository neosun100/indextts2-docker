#!/bin/bash

# 性能测试脚本
echo "=========================================="
echo "IndexTTS2 版本性能测试"
echo "=========================================="
echo ""

# 测试文本
TEST_TEXT="大家好，我现在正在测试IndexTTS2的不同优化版本的性能表现。这是一段用于性能基准测试的文本，长度适中，可以反映真实的使用场景。"

# 测试版本列表
VERSIONS=("v2.0-production" "v2.1-cuda" "v2.1-deepspeed" "v2.1-turbo")

# 创建测试输出目录
mkdir -p /tmp/benchmark-results

for VERSION in "${VERSIONS[@]}"; do
    echo "=========================================="
    echo "测试版本: $VERSION"
    echo "=========================================="
    
    # 启动容器
    echo "启动容器..."
    docker run -d \
        --name indextts2-test \
        --gpus all \
        -p 7870:7870 \
        -p 8002:8002 \
        -v /tmp/indextts-outputs:/app/outputs \
        neosun/indextts2:$VERSION
    
    # 等待服务启动
    echo "等待服务启动（60秒）..."
    sleep 60
    
    # 检查健康状态
    echo "检查服务健康状态..."
    HEALTH=$(curl -s http://localhost:8002/health)
    echo "健康检查: $HEALTH"
    
    if [[ "$HEALTH" != *"ok"* ]]; then
        echo "❌ 服务启动失败，跳过此版本"
        docker stop indextts2-test
        docker rm indextts2-test
        continue
    fi
    
    # 预热（第一次调用通常较慢）
    echo "预热中..."
    curl -s -X POST http://localhost:8002/tts \
        -H "Content-Type: application/json" \
        -d "{\"text\":\"预热\",\"spk_audio_prompt\":\"examples/voice_01.wav\"}" \
        --output /tmp/benchmark-results/warmup-$VERSION.wav
    
    sleep 5
    
    # 性能测试（3次取平均）
    echo "开始性能测试（3次）..."
    TOTAL_TIME=0
    
    for i in {1..3}; do
        echo "  测试 $i/3..."
        START=$(date +%s.%N)
        
        curl -s -X POST http://localhost:8002/tts \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"$TEST_TEXT\",\"spk_audio_prompt\":\"examples/voice_01.wav\"}" \
            --output /tmp/benchmark-results/test-$VERSION-$i.wav
        
        END=$(date +%s.%N)
        ELAPSED=$(echo "$END - $START" | bc)
        TOTAL_TIME=$(echo "$TOTAL_TIME + $ELAPSED" | bc)
        
        echo "  耗时: ${ELAPSED}秒"
        sleep 2
    done
    
    # 计算平均时间
    AVG_TIME=$(echo "scale=2; $TOTAL_TIME / 3" | bc)
    echo ""
    echo "✅ $VERSION 平均耗时: ${AVG_TIME}秒"
    echo "$VERSION,$AVG_TIME" >> /tmp/benchmark-results/results.csv
    echo ""
    
    # 停止并删除容器
    echo "清理容器..."
    docker stop indextts2-test
    docker rm indextts2-test
    
    # 等待一下再测试下一个版本
    sleep 5
done

echo ""
echo "=========================================="
echo "测试完成！结果汇总："
echo "=========================================="
echo ""
cat /tmp/benchmark-results/results.csv | column -t -s ','
echo ""
echo "详细结果保存在: /tmp/benchmark-results/"
