# 快速对比测试方案

## 问题分析

当前测试结果显示：
- 所有测试的GPT时间都在6-7秒
- 说明**参数没有生效**，都用的默认值
- 默认值: num_beams=3, top_k=30

## 真相

**效果不明显的原因**: 我们的API调用没有传递参数到infer函数！

## 解决方案

需要修改API服务器，让它真正传递参数：

```python
# 在 /app/api_server_cached_optimized.py 的 synthesize() 函数中
tts.infer(
    spk_audio_prompt=spk_audio_prompt,
    text=text,
    output_path=output_path,
    emo_vector=emo_vector,
    emo_alpha=emo_alpha,
    # 添加这些参数
    num_beams=data.get('num_beams', 3),
    top_k=data.get('top_k', 30),
    do_sample=data.get('do_sample', True)
)
```

## 快速验证方案

手动修改默认值，测试3个版本：

### 版本1: 原版（基准）
```python
num_beams = 3
top_k = 30
```

### 版本2: 优化版
```python
num_beams = 1
top_k = 20
```

### 版本3: 激进版
```python
num_beams = 1
top_k = 10
```

每个版本生成一个音频，对比：
1. 生成时间
2. 音质差异

## 预期结果

如果参数真的生效：
- num_beams从3降到1: 应该快50-70%
- 即从8秒降到2.5-4秒

如果还是6-7秒，说明：
1. 参数传递有问题
2. 或者模型内部没有使用这些参数
