import gradio as gr
from indextts.infer_v2 import IndexTTS2
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--server_name", default="0.0.0.0")
parser.add_argument("--server_port", type=int, default=7870)
parser.add_argument("--use_fp16", action="store_true")
parser.add_argument("--use_cuda_kernel", action="store_true")
parser.add_argument("--use_deepspeed", action="store_true")
args = parser.parse_args()

tts = IndexTTS2(cfg_path="checkpoints/config.yaml", model_dir="checkpoints", 
                use_fp16=args.use_fp16, use_cuda_kernel=args.use_cuda_kernel, 
                use_deepspeed=args.use_deepspeed)

def synthesize(text, spk_audio, emo_audio, emo_alpha, happy, angry, sad, afraid, 
               disgusted, melancholic, surprised, calm, use_emo_text, emo_text, use_random):
    import os
    import time
    import shutil
    import traceback
    
    try:
        os.makedirs("/app/outputs", exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # 保存上传的说话人音频
        spk_saved = f"/app/outputs/upload_spk_{timestamp}.wav"
        shutil.copy(spk_audio, spk_saved)
        
        # 保存上传的情感音频（如果有）
        emo_saved = None
        if emo_audio:
            emo_saved = f"/app/outputs/upload_emo_{timestamp}.wav"
            shutil.copy(emo_audio, emo_saved)
        
        # 生成输出音频
        output_path = f"/app/outputs/tts_{timestamp}.wav"
        
        emo_vector = [happy, angry, sad, afraid, disgusted, melancholic, surprised, calm] if any([happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]) else None
        tts.infer(spk_audio_prompt=spk_saved, text=text, output_path=output_path,
                  emo_audio_prompt=emo_saved if emo_saved else None,
                  emo_alpha=emo_alpha, emo_vector=emo_vector,
                  use_emo_text=use_emo_text, emo_text=emo_text if emo_text else None,
                  use_random=use_random, verbose=True)
        return output_path
    except Exception as e:
        error_msg = f"生成失败: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        gr.Warning(f"生成失败: {str(e)}")
        return None

with gr.Blocks(title="IndexTTS2 - 情感可控的零样本语音合成") as demo:
    gr.Markdown("""
    # 🎙️ IndexTTS2 - 情感可控的零样本语音合成
    
    **IndexTTS2** 是业界领先的自回归零样本 TTS 模型，支持精确的情感控制和声音克隆。
    
    ### 🚀 快速开始
    1. **输入文本**：输入要合成的文字内容
    2. **上传音频**：上传参考音频进行声音克隆（3-10秒效果最佳）
    3. **调节情感**（可选）：通过多种方式控制语音情感
    4. **生成语音**：点击按钮生成高质量语音
    """)
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("### 📝 基础设置")
            
            gr.Markdown("💡 **提示**：支持拼音控制发音，详见 checkpoints/pinyin.vocab")
            text_input = gr.Textbox(
                label="合成文本",
                placeholder="请输入要合成的文字内容...\n支持中英文混合，支持拼音标注（如：之前你做DE5很好）",
                lines=4
            )
            
            gr.Markdown("🎤 **说话人音频（必需）** - 上传参考音频进行声音克隆。建议：3-10秒清晰人声，无背景噪音")
            spk_audio = gr.Audio(label="说话人音频", type="filepath", sources=["upload", "microphone"])
            
            gr.Markdown("🎭 **情感参考音频（可选）** - 上传单独的情感参考音频。如不提供，将使用说话人音频的情感")
            emo_audio = gr.Audio(label="情感参考音频", type="filepath", sources=["upload", "microphone"])
            
            gr.Markdown("---")
            
            with gr.Accordion("🎨 情感控制选项", open=False):
                gr.Markdown("""
                ### 情感控制说明
                
                IndexTTS2 提供**三种**情感控制方式，可以单独使用或组合使用：
                
                1. **情感音频**：上传带有目标情感的音频（最直接）
                2. **情感向量**：手动调节8种情感的强度（最精确）
                3. **文本情感**：让AI自动从文本中识别情感（最便捷）
                """)
                
                gr.Markdown("**情感强度** - 控制情感的影响程度。1.0=完全应用情感，0.0=无情感。推荐：0.6-1.0")
                emo_alpha = gr.Slider(0, 1, value=1.0, label="情感强度 (Emotion Alpha)")
                
                gr.Markdown("#### 方式1️⃣：情感向量手动控制")
                gr.Markdown("*精确控制8种基础情感的强度，可以混合多种情感*")
                
                with gr.Row():
                    happy = gr.Slider(0, 1, value=0, label="😊 开心")
                    angry = gr.Slider(0, 1, value=0, label="😠 愤怒")
                    sad = gr.Slider(0, 1, value=0, label="😢 悲伤")
                    afraid = gr.Slider(0, 1, value=0, label="😨 恐惧")
                
                with gr.Row():
                    disgusted = gr.Slider(0, 1, value=0, label="🤢 厌恶")
                    melancholic = gr.Slider(0, 1, value=0, label="😔 忧郁")
                    surprised = gr.Slider(0, 1, value=0, label="😲 惊讶")
                    calm = gr.Slider(0, 1, value=0, label="😌 平静")
                
                gr.Markdown("#### 方式2️⃣：文本情感自动识别")
                
                gr.Markdown("让AI自动从文本中识别情感并应用。推荐情感强度设为0.6")
                use_emo_text = gr.Checkbox(label="启用文本情感识别", value=False)
                
                gr.Markdown("提供不同于合成文本的情感描述，AI将从这段文字中提取情感")
                emo_text = gr.Textbox(
                    label="独立情感文本（可选）",
                    placeholder="例如：你吓死我了！你是鬼吗？",
                    lines=2
                )
                
                gr.Markdown("#### ⚙️ 高级选项")
                
                gr.Markdown("⚠️ **随机采样** - 增加输出多样性，但会降低声音克隆的相似度。一般不建议开启")
                use_random = gr.Checkbox(label="启用随机采样", value=False)
                
                gr.Markdown("""
                ---
                ### 💡 使用建议
                
                **场景1 - 简单克隆**：只上传说话人音频，不调节任何情感
                
                **场景2 - 情感克隆**：上传说话人音频 + 情感音频（两个不同的音频）
                
                **场景3 - 精确控制**：上传说话人音频 + 手动调节情感向量（如：开心0.8 + 惊讶0.5）
                
                **场景4 - 智能识别**：上传说话人音频 + 勾选"文本情感识别"（情感强度建议0.6）
                """)
        
        with gr.Column():
            gr.Markdown("### 🔊 生成结果")
            
            submit_btn = gr.Button("🎵 生成语音", variant="primary", size="lg")
            
            output_audio = gr.Audio(label="合成音频")
            
            gr.Markdown("""
            ---
            ### 📚 参数说明
            
            | 参数 | 说明 | 推荐值 |
            |------|------|--------|
            | 情感强度 | 控制情感影响程度 | 0.6-1.0 |
            | 情感向量 | 8维情感精确控制 | 单一或混合 |
            | 文本情感 | AI自动识别 | 情感强度0.6 |
            | 随机采样 | 增加多样性 | 一般关闭 |
            
            ### 🎯 最佳实践
            
            - **音频质量**：参考音频越清晰，克隆效果越好
            - **音频长度**：3-10秒最佳，太短信息不足，太长无明显提升
            - **情感控制**：初次使用建议从单一情感开始（如只调节"开心"）
            - **文本情感**：适合快速生成，情感强度建议0.6以下更自然
            
            ### 🔗 相关链接
            
            - [📖 API文档 (Swagger)](https://index-tts-api.aws.xin/docs) - 完整的REST API使用说明
            - [GitHub](https://github.com/index-tts/index-tts)
            - [论文](https://arxiv.org/abs/2506.21619)
            - [在线Demo](https://index-tts.github.io/index-tts2.github.io/)
            """)
    
    gr.Markdown("""
    ---
    ### 🌐 API服务
    
    本系统提供完整的REST API服务，支持程序化调用：
    
    - **API地址**: `https://index-tts-api.aws.xin`
    - **Swagger文档**: [https://index-tts-api.aws.xin/docs](https://index-tts-api.aws.xin/docs)
    - **健康检查**: `GET /health`
    - **语音合成**: `POST /tts`
    
    访问Swagger文档可查看详细的API参数说明、示例代码和在线测试功能。
    """)
    
    submit_btn.click(synthesize, 
                     inputs=[text_input, spk_audio, emo_audio, emo_alpha, happy, angry, sad, 
                            afraid, disgusted, melancholic, surprised, calm, use_emo_text, emo_text, use_random],
                     outputs=output_audio)

demo.launch(server_name=args.server_name, server_port=args.server_port)
