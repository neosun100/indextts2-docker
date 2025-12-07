"""
Enhanced API Server with Speaker Cache Management
支持音频上传、缓存管理、speaker_id引用
"""
import os
import uuid
from flask import Flask, request, jsonify, send_file
from flask_swagger_ui import get_swaggerui_blueprint
from indextts.infer_v2 import IndexTTS2
from speaker_cache_manager import SpeakerCacheManager

app = Flask(__name__)

# 初始化TTS模型
print(">> Loading IndexTTS2 model...")
tts = IndexTTS2(
    cfg_path='checkpoints/config.yaml',
    model_dir='checkpoints',
    use_fp16=True,
    use_cuda_kernel=True
)
print(">> Model loaded successfully")

# 初始化缓存管理器
cache_manager = SpeakerCacheManager()
print(f">> Speaker cache initialized: {len(cache_manager.list_speakers())} speakers cached")

# Swagger UI配置
SWAGGER_URL = '/docs'
API_URL = '/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "IndexTTS2 API with Cache"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


@app.route('/swagger.json')
def swagger_spec():
    """Swagger API规范"""
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "IndexTTS2 API with Speaker Cache",
            "version": "2.1.0",
            "description": "Enhanced TTS API with speaker embedding cache management"
        },
        "servers": [{"url": "http://localhost:8002"}],
        "paths": {
            "/upload_speaker": {
                "post": {
                    "summary": "Upload speaker audio and cache embedding",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "audio": {"type": "string", "format": "binary"},
                                        "speaker_name": {"type": "string"}
                                    },
                                    "required": ["audio"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Speaker uploaded successfully",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "speaker_id": "spk_abc12345",
                                        "md5": "...",
                                        "status": "new",
                                        "message": "..."
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/speakers": {
                "get": {
                    "summary": "List all cached speakers",
                    "responses": {
                        "200": {
                            "description": "List of speakers",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "speakers": [
                                            {
                                                "speaker_id": "spk_abc12345",
                                                "speaker_name": "My Voice",
                                                "md5": "...",
                                                "embedding_cached": True
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/tts_cached": {
                "post": {
                    "summary": "Synthesize speech using cached speaker",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "text": {"type": "string"},
                                        "speaker_id": {"type": "string"},
                                        "emo_vector": {"type": "array", "items": {"type": "number"}},
                                        "emo_alpha": {"type": "number"}
                                    },
                                    "required": ["text", "speaker_id"]
                                },
                                "example": {
                                    "text": "你好，这是测试。",
                                    "speaker_id": "spk_abc12345",
                                    "emo_vector": [0.8, 0, 0, 0, 0, 0, 0.5, 0],
                                    "emo_alpha": 0.9
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Audio file",
                            "content": {"audio/wav": {}}
                        }
                    }
                }
            },
            "/tts": {
                "post": {
                    "summary": "Original TTS endpoint (backward compatible)",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "text": {"type": "string"},
                                        "spk_audio_prompt": {"type": "string"}
                                    },
                                    "required": ["text", "spk_audio_prompt"]
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    return jsonify(spec)


@app.route('/upload_speaker', methods=['POST'])
def upload_speaker():
    """上传说话人音频"""
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    audio_file = request.files['audio']
    speaker_name = request.form.get('speaker_name')
    
    # 保存临时文件
    temp_path = f"/tmp/upload_{uuid.uuid4()}.wav"
    audio_file.save(temp_path)
    
    try:
        # 上传到缓存管理器
        result = cache_manager.upload_speaker(temp_path, speaker_name)
        
        # 如果是新上传，提取embedding
        if result["status"] == "new":
            speaker_id = result["speaker_id"]
            audio_path = cache_manager.get_speaker_audio(speaker_id)
            
            # 调用TTS提取embedding（不生成音频）
            _ = tts.infer(
                text="预热",  # 短文本预热
                spk_audio_prompt=audio_path,
                output_path=None  # 不保存音频
            )
            
            # 缓存embedding到磁盘
            embeddings = {
                "spk_cond": tts.cache_spk_cond,
                "s2mel_style": tts.cache_s2mel_style,
                "s2mel_prompt": tts.cache_s2mel_prompt,
                "mel": tts.cache_mel
            }
            cache_manager.cache_embedding(speaker_id, embeddings)
            result["message"] = "Speaker uploaded and embedding cached successfully"
        
        return jsonify(result)
    
    finally:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.route('/speakers', methods=['GET'])
def list_speakers():
    """列出所有缓存的说话人"""
    speakers = cache_manager.list_speakers()
    return jsonify({"speakers": speakers, "count": len(speakers)})


@app.route('/speakers/<speaker_id>', methods=['DELETE'])
def delete_speaker(speaker_id):
    """删除说话人缓存"""
    success = cache_manager.delete_speaker(speaker_id)
    if success:
        return jsonify({"message": f"Speaker {speaker_id} deleted successfully"})
    else:
        return jsonify({"error": "Speaker not found"}), 404


@app.route('/tts_cached', methods=['POST'])
def synthesize_cached():
    """使用缓存的speaker进行语音合成"""
    data = request.json
    text = data.get('text')
    speaker_id = data.get('speaker_id')
    emo_vector = data.get('emo_vector')
    emo_alpha = data.get('emo_alpha', 1.0)
    
    if not text or not speaker_id:
        return jsonify({"error": "text and speaker_id required"}), 400
    
    # 从磁盘加载embedding
    embeddings = cache_manager.load_embedding(speaker_id)
    if embeddings is None:
        return jsonify({"error": f"Speaker {speaker_id} not found or embedding not cached"}), 404
    
    # 将embedding加载到GPU
    device = tts.device
    tts.cache_spk_cond = embeddings["spk_cond"].to(device)
    tts.cache_s2mel_style = embeddings["s2mel_style"].to(device)
    tts.cache_s2mel_prompt = embeddings["s2mel_prompt"].to(device)
    tts.cache_mel = embeddings["mel"].to(device)
    
    # 获取音频路径（用于标记缓存有效）
    audio_path = cache_manager.get_speaker_audio(speaker_id)
    tts.cache_spk_audio_prompt = audio_path
    
    # 生成音频
    os.makedirs("/app/outputs", exist_ok=True)
    output_path = f"/app/outputs/tts_{uuid.uuid4()}.wav"
    
    tts.infer(
        text=text,
        spk_audio_prompt=audio_path,  # 会直接使用缓存
        output_path=output_path,
        emo_vector=emo_vector,
        emo_alpha=emo_alpha
    )
    
    return send_file(output_path, mimetype='audio/wav')


@app.route('/tts', methods=['POST'])
def synthesize():
    """原始TTS接口（向后兼容）"""
    data = request.json
    text = data.get('text')
    spk_audio_prompt = data.get('spk_audio_prompt')
    emo_vector = data.get('emo_vector')
    emo_alpha = data.get('emo_alpha', 1.0)
    
    if not text or not spk_audio_prompt:
        return jsonify({"error": "text and spk_audio_prompt required"}), 400
    
    os.makedirs("/app/outputs", exist_ok=True)
    output_path = f"/app/outputs/tts_{uuid.uuid4()}.wav"
    
    tts.infer(
        spk_audio_prompt=spk_audio_prompt,
        text=text,
        output_path=output_path,
        emo_vector=emo_vector,
        emo_alpha=emo_alpha
    )
    
    return send_file(output_path, mimetype='audio/wav')


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "cached_speakers": len(cache_manager.list_speakers())
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002, debug=False)
