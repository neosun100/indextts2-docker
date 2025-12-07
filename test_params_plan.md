# 参数优化测试方案

## 📋 测试配置

### 版本1: 原版（基准）
```python
num_beams = 3
top_k = 30
do_sample = True
diffusion_steps = 25
```

### 版本2: 保守方案
```python
num_beams = 1        # 从3降到1
top_k = 20           # 从30降到20
do_sample = True     # 保持不变
diffusion_steps = 15 # 从25降到15
```

### 版本3: 激进方案
```python
num_beams = 1        # 从3降到1
top_k = 10           # 从30降到10
do_sample = True     # 保持不变
diffusion_steps = 10 # 从25降到10
```

### 版本4: 极限方案
```python
num_beams = 1        # 从3降到1
top_k = 30           # 保持不变
do_sample = False    # 改为贪婪解码
diffusion_steps = 5  # 从25降到5
```

## 🧪 测试文本

**短文本**:
```
你好，这是一个简短的测试。
```

**中文本**:
```
今天天气真不错，阳光明媚，微风习习。我们一起去公园散步吧。
```

**长文本**:
```
人工智能技术正在快速发展，深度学习模型的能力越来越强大。语音合成技术也取得了突破性进展，现在可以生成非常自然流畅的语音。这项技术将会在很多领域得到广泛应用，比如智能客服、有声读物、语音助手等等。
```

## 📁 输出文件路径

```
/tmp/indextts2-outputs/test_optimization/
├── v1_original_short.wav
├── v1_original_medium.wav
├── v1_original_long.wav
├── v2_conservative_short.wav
├── v2_conservative_medium.wav
├── v2_conservative_long.wav
├── v3_aggressive_short.wav
├── v3_aggressive_medium.wav
├── v3_aggressive_long.wav
├── v4_extreme_short.wav
├── v4_extreme_medium.wav
└── v4_extreme_long.wav
```

## 🔧 实施步骤

### 步骤1: 修改容器内的代码

需要修改文件: `/app/indextts/infer_v2.py`

找到这些行（约580-590行）:
```python
do_sample = generation_kwargs.pop("do_sample", True)
top_p = generation_kwargs.pop("top_p", 0.8)
top_k = generation_kwargs.pop("top_k", 30)
temperature = generation_kwargs.pop("temperature", 0.8)
num_beams = generation_kwargs.pop("num_beams", 3)
```

找到这行（约630行）:
```python
diffusion_steps = 25
```

### 步骤2: 为每个版本生成音频

1. 修改参数为版本1（原版）
2. 重启容器
3. 生成3个音频（短/中/长）
4. 重复步骤1-3，测试版本2、3、4

### 步骤3: 对比音质

听每个版本的音频，评估：
- 清晰度
- 自然度
- 是否有杂音/失真
- 语速是否正常

## ⏱️ 预期时间对比

| 版本 | 短文本 | 中文本 | 长文本 | 说明 |
|------|--------|--------|--------|------|
| 原版 | ~3秒 | ~5秒 | ~10秒 | 基准 |
| 保守 | ~2秒 | ~3秒 | ~6秒 | -40% |
| 激进 | ~1.5秒 | ~2秒 | ~4秒 | -60% |
| 极限 | ~1秒 | ~1.5秒 | ~3秒 | -70% |

## 📊 评估标准

为每个音频打分（1-5分）:
- 5分: 完美，无法区分
- 4分: 很好，轻微差异
- 3分: 可接受，有明显差异
- 2分: 较差，有明显问题
- 1分: 不可用

如果某个版本的平均分≥4分，则可以部署。
