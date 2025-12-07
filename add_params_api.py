"""
添加到 api_server_cached_optimized.py 的新端点
支持动态调整生成参数
"""

# 在文件末尾、if __name__ == '__main__': 之前添加:

@app.route('/tts_tunable', methods=['POST'])
def tts_tunable():
    """
    可调参数的TTS接口
    支持动态调整num_beams, top_k, do_sample等参数
    """
    data = request.json
    text = data.get('text')
    spk_audio_prompt = data.get('spk_audio_prompt')
    
    # 可调参数
    num_beams = data.get('num_beams', 3)
    top_k = data.get('top_k', 30)
    top_p = data.get('top_p', 0.8)
    temperature = data.get('temperature', 0.8)
    do_sample = data.get('do_sample', True)
    
    # 情感参数
    emo_vector = data.get('emo_vector')
    emo_alpha = data.get('emo_alpha', 1.0)
    
    # 测试ID（用于文件命名）
    test_id = data.get('test_id', 'custom')
    
    if not text or not spk_audio_prompt:
        return jsonify({"error": "text and spk_audio_prompt required"}), 400
    
    os.makedirs("/app/outputs/test_optimization", exist_ok=True)
    
    # 文件名包含参数信息
    filename = f"{test_id}_b{num_beams}_k{top_k}_s{do_sample}.wav"
    output_path = f"/app/outputs/test_optimization/{filename}"
    
    import time
    start_time = time.time()
    
    # 调用infer，传递generation_kwargs
    tts.infer(
        spk_audio_prompt=spk_audio_prompt,
        text=text,
        output_path=output_path,
        emo_vector=emo_vector,
        emo_alpha=emo_alpha,
        num_beams=num_beams,
        top_k=top_k,
        top_p=top_p,
        temperature=temperature,
        do_sample=do_sample
    )
    
    total_time = time.time() - start_time
    
    # 返回性能数据
    import json
    metadata = {
        "test_id": test_id,
        "parameters": {
            "num_beams": num_beams,
            "top_k": top_k,
            "top_p": top_p,
            "temperature": temperature,
            "do_sample": do_sample
        },
        "performance": {
            "total_time": round(total_time, 3)
        },
        "audio": {
            "file": filename,
            "path": output_path
        }
    }
    
    # 保存元数据
    meta_path = output_path.replace('.wav', '.json')
    with open(meta_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return send_file(output_path, mimetype='audio/wav')
