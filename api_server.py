from flask import Flask, request, jsonify, send_file
from flask_swagger_ui import get_swaggerui_blueprint
from indextts.infer_v2 import IndexTTS2
import os
import uuid
import json

app = Flask(__name__)
tts = IndexTTS2(cfg_path="checkpoints/config.yaml", model_dir="checkpoints", use_fp16=True, use_cuda_kernel=False, use_deepspeed=False)

# Swagger UI 配置
SWAGGER_URL = '/docs'
API_URL = '/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "IndexTTS2 API"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

@app.route('/swagger.json')
def swagger_spec():
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "IndexTTS2 API",
            "description": "IndexTTS2 零样本语音合成 API - 支持声音克隆和情感控制",
            "version": "2.0.0",
            "contact": {
                "name": "IndexTTS Team",
                "email": "indexspeech@bilibili.com",
                "url": "https://github.com/index-tts/index-tts"
            }
        },
        "servers": [
            {"url": "http://localhost:8002", "description": "本地开发"},
            {"url": "https://index-tts-api.aws.xin", "description": "生产环境"}
        ],
        "paths": {
            "/health": {
                "get": {
                    "summary": "健康检查",
                    "description": "检查 API 服务是否正常运行",
                    "responses": {
                        "200": {
                            "description": "服务正常",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string", "example": "ok"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/tts": {
                "post": {
                    "summary": "语音合成",
                    "description": "使用 IndexTTS2 进行零样本语音合成，支持声音克隆和情感控制",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["text", "spk_audio_prompt"],
                                    "properties": {
                                        "text": {
                                            "type": "string",
                                            "description": "要合成的文本内容",
                                            "example": "你好，这是IndexTTS2的测试。"
                                        },
                                        "spk_audio_prompt": {
                                            "type": "string",
                                            "description": "说话人参考音频路径（必需）",
                                            "example": "examples/voice_01.wav"
                                        },
                                        "emo_audio_prompt": {
                                            "type": "string",
                                            "description": "情感参考音频路径（可选）",
                                            "example": "examples/emo_sad.wav"
                                        },
                                        "emo_alpha": {
                                            "type": "number",
                                            "format": "float",
                                            "minimum": 0.0,
                                            "maximum": 1.0,
                                            "default": 1.0,
                                            "description": "情感强度 (0.0-1.0)，推荐 0.6-1.0",
                                            "example": 0.9
                                        },
                                        "emo_vector": {
                                            "type": "array",
                                            "items": {"type": "number", "format": "float"},
                                            "minItems": 8,
                                            "maxItems": 8,
                                            "description": "8维情感向量 [happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]",
                                            "example": [0.8, 0, 0, 0, 0, 0, 0.5, 0]
                                        },
                                        "use_emo_text": {
                                            "type": "boolean",
                                            "default": False,
                                            "description": "是否启用文本情感识别",
                                            "example": False
                                        },
                                        "emo_text": {
                                            "type": "string",
                                            "description": "独立的情感文本（需要 use_emo_text=true）",
                                            "example": "你吓死我了！"
                                        },
                                        "use_random": {
                                            "type": "boolean",
                                            "default": False,
                                            "description": "是否启用随机采样（会降低克隆相似度）",
                                            "example": False
                                        }
                                    }
                                },
                                "examples": {
                                    "basic": {
                                        "summary": "基础合成",
                                        "value": {
                                            "text": "你好，这是一个测试。",
                                            "spk_audio_prompt": "examples/voice_01.wav"
                                        }
                                    },
                                    "emotion_vector": {
                                        "summary": "情感向量控制",
                                        "value": {
                                            "text": "哇塞！这个太棒了！",
                                            "spk_audio_prompt": "examples/voice_01.wav",
                                            "emo_vector": [0.8, 0, 0, 0, 0, 0, 0.5, 0],
                                            "emo_alpha": 0.9
                                        }
                                    },
                                    "emotion_audio": {
                                        "summary": "情感音频参考",
                                        "value": {
                                            "text": "今天天气真好。",
                                            "spk_audio_prompt": "examples/voice_01.wav",
                                            "emo_audio_prompt": "examples/emo_sad.wav",
                                            "emo_alpha": 0.8
                                        }
                                    },
                                    "emotion_text": {
                                        "summary": "文本情感识别",
                                        "value": {
                                            "text": "快躲起来！他要来了！",
                                            "spk_audio_prompt": "examples/voice_01.wav",
                                            "use_emo_text": True,
                                            "emo_alpha": 0.6
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "成功生成音频",
                            "content": {
                                "audio/wav": {
                                    "schema": {
                                        "type": "string",
                                        "format": "binary"
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "请求参数错误",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "error": {"type": "string"}
                                        }
                                    },
                                    "example": {
                                        "error": "text and spk_audio_prompt required"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "EmotionVector": {
                    "type": "array",
                    "description": "8维情感向量",
                    "items": {"type": "number", "format": "float"},
                    "minItems": 8,
                    "maxItems": 8,
                    "example": [0.8, 0, 0, 0, 0, 0, 0.5, 0]
                }
            }
        }
    }
    return jsonify(spec)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/tts', methods=['POST'])
def synthesize():
    data = request.json
    text = data.get('text')
    spk_audio_prompt = data.get('spk_audio_prompt')
    emo_audio_prompt = data.get('emo_audio_prompt')
    emo_alpha = data.get('emo_alpha', 1.0)
    emo_vector = data.get('emo_vector')
    use_emo_text = data.get('use_emo_text', False)
    emo_text = data.get('emo_text')
    use_random = data.get('use_random', False)
    
    if not text or not spk_audio_prompt:
        return jsonify({"error": "text and spk_audio_prompt required"}), 400
    
    os.makedirs("/app/outputs", exist_ok=True)
    output_path = f"/app/outputs/tts_{uuid.uuid4()}.wav"
    
    tts.infer(
        spk_audio_prompt=spk_audio_prompt,
        text=text,
        output_path=output_path,
        emo_audio_prompt=emo_audio_prompt,
        emo_alpha=emo_alpha,
        emo_vector=emo_vector,
        use_emo_text=use_emo_text,
        emo_text=emo_text,
        use_random=use_random,
        verbose=True
    )
    
    return send_file(output_path, mimetype='audio/wav')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002)
