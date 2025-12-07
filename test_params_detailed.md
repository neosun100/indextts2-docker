# 细粒度参数优化测试方案

## 🎯 测试策略

**单变量测试**: 每次只改变一个参数，观察影响
**组合测试**: 测试最优参数的组合

## 📊 测试矩阵

### 阶段1: num_beams测试（最关键）
| 测试ID | num_beams | top_k | do_sample | diffusion_steps | 预期时间 |
|--------|-----------|-------|-----------|-----------------|----------|
| T01    | 3         | 30    | True      | 25              | 5.5秒 (基准) |
| T02    | 2         | 30    | True      | 25              | ~3.7秒 (-33%) |
| T03    | 1         | 30    | True      | 25              | ~2.2秒 (-60%) |

### 阶段2: top_k测试
| 测试ID | num_beams | top_k | do_sample | diffusion_steps | 预期时间 |
|--------|-----------|-------|-----------|-----------------|----------|
| T04    | 1         | 30    | True      | 25              | ~2.2秒 (基准) |
| T05    | 1         | 20    | True      | 25              | ~2.0秒 (-9%) |
| T06    | 1         | 10    | True      | 25              | ~1.8秒 (-18%) |
| T07    | 1         | 5     | True      | 25              | ~1.7秒 (-23%) |

### 阶段3: diffusion_steps测试
| 测试ID | num_beams | top_k | do_sample | diffusion_steps | 预期时间 |
|--------|-----------|-------|-----------|-----------------|----------|
| T08    | 1         | 20    | True      | 25              | ~2.0秒 (基准) |
| T09    | 1         | 20    | True      | 20              | ~1.9秒 (-5%) |
| T10    | 1         | 20    | True      | 15              | ~1.8秒 (-10%) |
| T11    | 1         | 20    | True      | 10              | ~1.7秒 (-15%) |
| T12    | 1         | 20    | True      | 5               | ~1.6秒 (-20%) |

### 阶段4: do_sample测试
| 测试ID | num_beams | top_k | do_sample | diffusion_steps | 预期时间 |
|--------|-----------|-------|-----------|-----------------|----------|
| T13    | 1         | 20    | True      | 15              | ~1.8秒 (基准) |
| T14    | 1         | 20    | False     | 15              | ~1.5秒 (-17%) |

### 阶段5: 最优组合测试
| 测试ID | num_beams | top_k | do_sample | diffusion_steps | 预期时间 | 说明 |
|--------|-----------|-------|-----------|-----------------|----------|------|
| T15    | 1         | 20    | True      | 15              | ~1.8秒 | 保守最优 |
| T16    | 1         | 10    | True      | 10              | ~1.5秒 | 激进最优 |
| T17    | 1         | 10    | False     | 10              | ~1.3秒 | 极限最优 |

## 📁 文件命名规范

```
T{ID}_b{beams}_k{topk}_s{sample}_d{diffusion}.wav

示例:
T01_b3_k30_sTrue_d25.wav   # 原版基准
T03_b1_k30_sTrue_d25.wav   # num_beams=1
T10_b1_k20_sTrue_d15.wav   # 保守组合
```

## 🧪 测试文本

使用单一中等长度文本，便于对比:
```
今天天气真不错，阳光明媚，微风习习。我们一起去公园散步吧。
```

## 📊 输出格式

每个音频文件生成时，同时生成一个JSON元数据文件:

```json
{
  "test_id": "T03",
  "parameters": {
    "num_beams": 1,
    "top_k": 30,
    "do_sample": true,
    "diffusion_steps": 25
  },
  "performance": {
    "total_time": 2.15,
    "gpt_gen_time": 1.68,
    "gpt_forward_time": 0.02,
    "s2mel_time": 0.42,
    "bigvgan_time": 0.06
  },
  "audio": {
    "file": "T03_b1_k30_sTrue_d25.wav",
    "size_kb": 215.3,
    "duration_sec": 5.2
  }
}
```

## 🔧 实施方案

### 方案A: 修改API支持动态参数（推荐）

修改 `/app/api_server_cached_optimized.py`，添加参数支持:

```python
@app.route('/tts_with_params', methods=['POST'])
def tts_with_params():
    data = request.json
    text = data.get('text')
    spk_audio_prompt = data.get('spk_audio_prompt')
    
    # 新增参数
    num_beams = data.get('num_beams', 3)
    top_k = data.get('top_k', 30)
    do_sample = data.get('do_sample', True)
    diffusion_steps = data.get('diffusion_steps', 25)
    
    # 传递给infer函数
    output_path = f"/app/outputs/tts_{uuid.uuid4()}.wav"
    tts.infer(
        spk_audio_prompt=spk_audio_prompt,
        text=text,
        output_path=output_path,
        num_beams=num_beams,
        top_k=top_k,
        do_sample=do_sample,
        # diffusion_steps需要在infer_v2.py中支持
        **{'diffusion_steps': diffusion_steps}
    )
    
    return send_file(output_path, mimetype='audio/wav')
```

### 方案B: 批量生成脚本

创建脚本，自动修改参数、重启容器、生成音频。

## ⏱️ 预期测试时间

- 17个测试 × 3秒/测试 = ~51秒
- 加上参数切换时间 = ~2分钟

## 📈 评估流程

1. 生成所有17个音频文件
2. 按顺序播放，记录评分
3. 找出音质≥4分且速度最快的配置
4. 部署该配置
