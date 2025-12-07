#!/bin/bash

# ==========================================
# IndexTTS2 全面性能测试脚本
# ==========================================
# 测试方案：
# - 4个版本: v2.0-production, v2.1-cuda, v2.1-deepspeed, v2.1-turbo
# - 每个场景测试5次
# - 测试场景: 中文短文本、中文长文本、英文短文本、英文长文本
# ==========================================

set -e

echo "=========================================="
echo "IndexTTS2 全面性能测试"
echo "测试时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""

# 测试文本定义
declare -A TEST_TEXTS

# 中文短文本 (~20字)
TEST_TEXTS["zh_short"]="大家好，欢迎来到测试环节，今天我们将进行性能评估。"

# 中文长文本 (~100字)
TEST_TEXTS["zh_long"]="人工智能技术的发展日新月异，语音合成作为其中重要的一环，正在改变我们与机器交互的方式。从早期的拼接式合成到现在的端到端神经网络模型，技术的进步让合成语音越来越自然流畅。IndexTTS2作为新一代的语音合成系统，采用了最新的深度学习技术，能够生成高质量的语音输出。"

# 英文短文本 (~20 words)
TEST_TEXTS["en_short"]="Hello everyone, welcome to the testing session. Today we will conduct a performance evaluation of the system."

# 英文长文本 (~100 words)
TEST_TEXTS["en_long"]="The development of artificial intelligence technology is advancing rapidly. Speech synthesis, as an important component, is transforming the way we interact with machines. From early concatenative synthesis to current end-to-end neural network models, technological progress has made synthesized speech increasingly natural and fluent. IndexTTS2, as a next-generation speech synthesis system, employs the latest deep learning techniques and is capable of generating high-quality speech output with remarkable clarity and naturalness."

# 版本列表
VERSIONS=("v2.0-production" "v2.1-cuda" "v2.1-deepspeed" "v2.1-turbo")

# 测试场景
SCENARIOS=("zh_short" "zh_long" "en_short" "en_long")

# 创建结果目录
RESULT_DIR="/tmp/benchmark-comprehensive-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RESULT_DIR"
echo "结果目录: $RESULT_DIR"
echo ""

# 结果CSV文件
RESULTS_CSV="$RESULT_DIR/results.csv"
echo "Version,Scenario,Test,Time_Seconds,HTTP_Code" > "$RESULTS_CSV"

# 测试函数
test_version() {
    local VERSION=$1
    echo ""
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

    # 根据版本调整等待时间
    if [[ "$VERSION" == *"cuda"* ]] || [[ "$VERSION" == *"turbo"* ]]; then
        echo "等待服务启动（需要编译，预计180秒）..."
        sleep 180
    else
        echo "等待服务启动（预计90秒）..."
        sleep 90
    fi

    # 健康检查
    echo "检查服务健康状态..."
    local HEALTH_RETRIES=5
    local HEALTH_OK=false

    for i in $(seq 1 $HEALTH_RETRIES); do
        HEALTH=$(curl -s http://localhost:8002/health 2>/dev/null || echo "")
        if [[ "$HEALTH" == *"ok"* ]]; then
            echo "✅ 服务已就绪"
            HEALTH_OK=true
            break
        fi
        echo "  重试 $i/$HEALTH_RETRIES..."
        sleep 30
    done

    if [[ "$HEALTH_OK" == "false" ]]; then
        echo "❌ 服务启动失败"
        echo "容器日志:"
        docker logs indextts2-test 2>&1 | tail -30
        docker stop indextts2-test 2>/dev/null || true
        docker rm indextts2-test 2>/dev/null || true
        return 1
    fi

    # 预热
    echo "预热中..."
    curl -s -X POST http://localhost:8002/tts \
        -H "Content-Type: application/json" \
        -d '{"text":"Warmup test","spk_audio_prompt":"examples/voice_01.wav"}' \
        --output "$RESULT_DIR/warmup-$VERSION.wav" 2>/dev/null || true

    sleep 5

    # 测试各个场景
    for SCENARIO in "${SCENARIOS[@]}"; do
        echo ""
        echo "----------------------------------------"
        echo "场景: $SCENARIO"
        echo "文本: ${TEST_TEXTS[$SCENARIO]}"
        echo "----------------------------------------"

        # 测试5次
        for TEST_NUM in {1..5}; do
            echo -n "  测试 $TEST_NUM/5... "

            START=$(date +%s.%N)

            HTTP_CODE=$(curl -s -w "%{http_code}" -X POST http://localhost:8002/tts \
                -H "Content-Type: application/json" \
                -d "{\"text\":\"${TEST_TEXTS[$SCENARIO]}\",\"spk_audio_prompt\":\"examples/voice_01.wav\"}" \
                --output "$RESULT_DIR/test-$VERSION-$SCENARIO-$TEST_NUM.wav" \
                2>/dev/null)

            END=$(date +%s.%N)

            if [[ "$HTTP_CODE" == "200" ]]; then
                ELAPSED=$(echo "$END - $START" | bc)
                echo "✅ ${ELAPSED}秒"
                echo "$VERSION,$SCENARIO,$TEST_NUM,$ELAPSED,$HTTP_CODE" >> "$RESULTS_CSV"
            else
                echo "❌ HTTP $HTTP_CODE"
                echo "$VERSION,$SCENARIO,$TEST_NUM,FAILED,$HTTP_CODE" >> "$RESULTS_CSV"
            fi

            sleep 2
        done
    done

    # 清理容器
    echo ""
    echo "清理容器..."
    docker stop indextts2-test 2>/dev/null || true
    docker rm indextts2-test 2>/dev/null || true

    sleep 5
}

# 执行测试
for VERSION in "${VERSIONS[@]}"; do
    test_version "$VERSION"
done

echo ""
echo "=========================================="
echo "测试完成！"
echo "=========================================="
echo "结果文件: $RESULTS_CSV"
echo ""

# 生成统计报告
echo "生成统计报告..."
python3 << 'PYTHON_SCRIPT'
import csv
import statistics
import sys
from collections import defaultdict

# 读取结果
results = defaultdict(lambda: defaultdict(list))

with open('RESULTS_CSV_PLACEHOLDER', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        version = row['Version']
        scenario = row['Scenario']
        time_str = row['Time_Seconds']

        if time_str != 'FAILED':
            try:
                time_val = float(time_str)
                results[version][scenario].append(time_val)
            except:
                pass

# 生成报告
print("\n" + "="*60)
print("详细统计报告")
print("="*60 + "\n")

scenario_names = {
    'zh_short': '中文短文本(~20字)',
    'zh_long': '中文长文本(~100字)',
    'en_short': '英文短文本(~20词)',
    'en_long': '英文长文本(~100词)'
}

for scenario in ['zh_short', 'zh_long', 'en_short', 'en_long']:
    print(f"\n📊 {scenario_names[scenario]}")
    print("-" * 60)
    print(f"{'版本':<20} {'平均':<10} {'最小':<10} {'最大':<10} {'标准差':<10}")
    print("-" * 60)

    version_stats = {}
    for version in ['v2.0-production', 'v2.1-cuda', 'v2.1-deepspeed', 'v2.1-turbo']:
        times = results[version][scenario]
        if times:
            avg = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            std = statistics.stdev(times) if len(times) > 1 else 0
            version_stats[version] = avg
            print(f"{version:<20} {avg:>8.2f}秒 {min_time:>8.2f}秒 {max_time:>8.2f}秒 {std:>8.2f}秒")
        else:
            print(f"{version:<20} {'FAILED':<10}")

    # 计算加速比
    if 'v2.0-production' in version_stats:
        baseline = version_stats['v2.0-production']
        print("\n加速比 (相对v2.0-production):")
        for version in ['v2.1-cuda', 'v2.1-deepspeed', 'v2.1-turbo']:
            if version in version_stats:
                speedup = baseline / version_stats[version]
                improvement = (baseline - version_stats[version]) / baseline * 100
                print(f"  {version}: {speedup:.2f}x (提升 {improvement:+.1f}%)")

print("\n" + "="*60)
PYTHON_SCRIPT

# 替换占位符
sed -i "s|RESULTS_CSV_PLACEHOLDER|$RESULTS_CSV|g" /tmp/benchmark_report.py 2>/dev/null || true

# 执行Python脚本
python3 -c "
import csv
import statistics
from collections import defaultdict

results = defaultdict(lambda: defaultdict(list))

with open('$RESULTS_CSV', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        version = row['Version']
        scenario = row['Scenario']
        time_str = row['Time_Seconds']

        if time_str != 'FAILED':
            try:
                time_val = float(time_str)
                results[version][scenario].append(time_val)
            except:
                pass

print('\n' + '='*60)
print('详细统计报告')
print('='*60 + '\n')

scenario_names = {
    'zh_short': '中文短文本(~20字)',
    'zh_long': '中文长文本(~100字)',
    'en_short': '英文短文本(~20词)',
    'en_long': '英文长文本(~100词)'
}

for scenario in ['zh_short', 'zh_long', 'en_short', 'en_long']:
    print(f'\n📊 {scenario_names[scenario]}')
    print('-' * 60)
    print(f\"{'版本':<20} {'平均':<10} {'最小':<10} {'最大':<10} {'标准差':<10}\")
    print('-' * 60)

    version_stats = {}
    for version in ['v2.0-production', 'v2.1-cuda', 'v2.1-deepspeed', 'v2.1-turbo']:
        times = results[version][scenario]
        if times:
            avg = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            std = statistics.stdev(times) if len(times) > 1 else 0
            version_stats[version] = avg
            print(f'{version:<20} {avg:>8.2f}秒 {min_time:>8.2f}秒 {max_time:>8.2f}秒 {std:>8.2f}秒')
        else:
            print(f'{version:<20} FAILED')

    if 'v2.0-production' in version_stats:
        baseline = version_stats['v2.0-production']
        print('\n加速比 (相对v2.0-production):')
        for version in ['v2.1-cuda', 'v2.1-deepspeed', 'v2.1-turbo']:
            if version in version_stats:
                speedup = baseline / version_stats[version]
                improvement = (baseline - version_stats[version]) / baseline * 100
                print(f'  {version}: {speedup:.2f}x (提升 {improvement:+.1f}%)')

print('\n' + '='*60)
"

echo ""
echo "✅ 全部测试完成！"
echo "详细数据: $RESULTS_CSV"
echo "音频文件: $RESULT_DIR/"
