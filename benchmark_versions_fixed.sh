#!/bin/bash

echo "=========================================="
echo "IndexTTS2 版本性能测试（修复版）"
echo "=========================================="
echo ""

TEST_TEXT="大家好，我现在正在测试IndexTTS2的不同优化版本的性能表现。这是一段用于性能基准测试的文本，长度适中，可以反映真实的使用场景。"

VERSIONS=("v2.0-production" "v2.1-cuda" "v2.1-deepspeed" "v2.1-turbo")

rm -f /tmp/benchmark-results/results.csv
mkdir -p /tmp/benchmark-results

for VERSION in "${VERSIONS[@]}"; do
    echo "=========================================="
    echo "测试版本: $VERSION"
    echo "=========================================="
    
    docker run -d \
        --name indextts2-test \
        --gpus all \
        -p 7870:7870 \
        -p 8002:8002 \
        -v /tmp/indextts-outputs:/app/outputs \
        neosun/indextts2:$VERSION
    
    # 根据版本调整等待时间
    if [[ "$VERSION" == *"cuda"* ]] || [[ "$VERSION" == *"turbo"* ]]; then
        echo "等待服务启动（需要编译CUDA kernel，180秒）..."
        sleep 180
    else
        echo "等待服务启动（90秒）..."
        sleep 90
    fi
    
    # 检查健康状态（重试3次）
    echo "检查服务健康状态..."
    HEALTH=""
    for i in {1..3}; do
        HEALTH=$(curl -s http://localhost:8002/health 2>/dev/null)
        if [[ "$HEALTH" == *"ok"* ]]; then
            break
        fi
        echo "  重试 $i/3..."
        sleep 30
    done
    
    echo "健康检查: $HEALTH"
    
    if [[ "$HEALTH" != *"ok"* ]]; then
        echo "❌ 服务启动失败"
        echo "查看日志:"
        docker logs indextts2-test 2>&1 | tail -20
        docker stop indextts2-test
        docker rm indextts2-test
        echo "$VERSION,FAILED" >> /tmp/benchmark-results/results.csv
        continue
    fi
    
    # 预热
    echo "预热中..."
    curl -s -X POST http://localhost:8002/tts \
        -H "Content-Type: application/json" \
        -d '{"text":"预热","spk_audio_prompt":"examples/voice_01.wav"}' \
        --output /tmp/benchmark-results/warmup-$VERSION.wav 2>/dev/null
    
    sleep 5
    
    # 性能测试（3次）
    echo "开始性能测试（3次）..."
    TOTAL_TIME=0
    SUCCESS=0
    
    for i in {1..3}; do
        echo "  测试 $i/3..."
        START=$(date +%s.%N)
        
        HTTP_CODE=$(curl -s -w "%{http_code}" -X POST http://localhost:8002/tts \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"$TEST_TEXT\",\"spk_audio_prompt\":\"examples/voice_01.wav\"}" \
            --output /tmp/benchmark-results/test-$VERSION-$i.wav 2>/dev/null)
        
        END=$(date +%s.%N)
        
        if [[ "$HTTP_CODE" == "200" ]]; then
            ELAPSED=$(echo "$END - $START" | bc)
            TOTAL_TIME=$(echo "$TOTAL_TIME + $ELAPSED" | bc)
            SUCCESS=$((SUCCESS + 1))
            echo "  耗时: ${ELAPSED}秒"
        else
            echo "  失败 (HTTP $HTTP_CODE)"
        fi
        
        sleep 2
    done
    
    if [[ $SUCCESS -gt 0 ]]; then
        AVG_TIME=$(echo "scale=2; $TOTAL_TIME / $SUCCESS" | bc)
        echo ""
        echo "✅ $VERSION 平均耗时: ${AVG_TIME}秒 ($SUCCESS/3 成功)"
        echo "$VERSION,$AVG_TIME" >> /tmp/benchmark-results/results.csv
    else
        echo "❌ $VERSION 所有测试失败"
        echo "$VERSION,FAILED" >> /tmp/benchmark-results/results.csv
    fi
    
    echo ""
    docker stop indextts2-test
    docker rm indextts2-test
    sleep 5
done

echo ""
echo "=========================================="
echo "测试完成！结果汇总："
echo "=========================================="
echo ""
echo "版本,平均耗时(秒)"
cat /tmp/benchmark-results/results.csv
echo ""

# 计算加速比
echo "=========================================="
echo "加速比分析："
echo "=========================================="
BASELINE=$(grep "v2.0-production" /tmp/benchmark-results/results.csv | cut -d',' -f2)
if [[ ! -z "$BASELINE" ]] && [[ "$BASELINE" != "FAILED" ]]; then
    echo "基准版本 (v2.0-production): ${BASELINE}秒"
    echo ""
    while IFS=',' read -r version time; do
        if [[ "$version" != "v2.0-production" ]] && [[ "$time" != "FAILED" ]]; then
            speedup=$(echo "scale=2; $BASELINE / $time" | bc)
            improvement=$(echo "scale=1; ($BASELINE - $time) / $BASELINE * 100" | bc)
            echo "$version: ${time}秒 (${speedup}x 加速, 提升 ${improvement}%)"
        fi
    done < /tmp/benchmark-results/results.csv
fi
