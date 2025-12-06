# IndexTTS2 部署更新说明

## 更新时间
2025-12-06 23:33

## 更新内容

### 1. Web UI 界面增强 ✅

已在 Web UI 中添加了详细的中文说明，包括：

#### 📝 基础说明
- 快速开始指南（4步操作流程）
- 拼音控制发音提示
- 音频上传建议（3-10秒清晰人声）

#### 🎨 情感控制详细说明
- **三种情感控制方式**的完整说明：
  1. 情感音频参考（最直接）
  2. 情感向量手动控制（最精确）- 8维情感滑块
  3. 文本情感自动识别（最便捷）

#### 💡 使用建议
- 情感强度参数说明（推荐值：0.6-1.0）
- 随机采样的影响说明
- 4种典型使用场景示例

#### 📚 参数说明表格
- 所有参数的详细说明和推荐值
- 最佳实践指南
- 音频质量、长度、情感控制建议

#### 🔗 相关链接
- API文档（Swagger）链接
- GitHub、论文、在线Demo链接

#### 🌐 API服务说明
- API地址和端点说明
- Swagger文档访问方式
- 健康检查和语音合成端点介绍

### 2. Swagger API 文档 ✅

已在 API 服务器中集成完整的 Swagger/OpenAPI 文档：

#### 访问地址
- **Swagger UI**: https://index-tts-api.aws.xin/docs/
- **OpenAPI JSON**: https://index-tts-api.aws.xin/swagger.json

#### 文档内容
- **健康检查端点** (`GET /health`)
  - 完整的请求/响应示例
  
- **语音合成端点** (`POST /tts`)
  - 详细的参数说明（中文）
  - 5个实际使用示例：
    1. 基础合成
    2. 情感音频参考
    3. 情感向量控制
    4. 文本情感识别
    5. 独立情感文本
  - 完整的请求/响应格式
  - 参数类型和约束说明

#### 交互功能
- 在线测试 API 端点
- 自动生成请求代码
- 实时查看响应结果

### 3. 技术修复 ✅

- 修复了 Gradio `Audio` 组件的 `info` 参数兼容性问题
- 添加了麦克风录音支持（`sources=["upload", "microphone"]`）
- 优化了 Markdown 说明的布局和可读性

## 服务状态

### 运行状态
- ✅ Docker 容器运行正常
- ✅ Web UI 可访问：https://index-tts.aws.xin
- ✅ API 服务可访问：https://index-tts-api.aws.xin
- ✅ Swagger 文档可访问：https://index-tts-api.aws.xin/docs/
- ✅ 健康检查正常：`{"status":"ok"}`

### 端口映射
- 7870 → Web UI (Gradio)
- 8002 → API Server (Flask + Swagger)

### Nginx 配置
- SSL/TLS 加密
- 反向代理到本地服务
- 无需身份验证

## 使用指南

### Web UI 使用
1. 访问 https://index-tts.aws.xin
2. 查看页面上的详细说明
3. 按照4步快速开始指南操作
4. 根据需要选择情感控制方式

### API 使用
1. 访问 https://index-tts-api.aws.xin/docs/ 查看 Swagger 文档
2. 在 Swagger UI 中测试 API 端点
3. 复制生成的代码到你的应用中
4. 参考5个示例选择合适的使用方式

### 情感控制建议
- **简单克隆**：只上传说话人音频
- **情感克隆**：上传说话人音频 + 情感音频
- **精确控制**：上传说话人音频 + 调节情感向量
- **智能识别**：上传说话人音频 + 启用文本情感识别（情感强度0.6）

## 相关文件

- `webui_enhanced.py` - 增强的 Web UI（包含详细说明）
- `api_server.py` - API 服务器（包含 Swagger 文档）
- `USER_GUIDE.md` - 详细的用户使用指南
- `Dockerfile` - Docker 构建配置
- `/etc/nginx/nginx.conf` - Nginx 反向代理配置

## 技术栈

- **前端**: Gradio 5.45.0
- **后端**: Flask 3.1.2
- **API 文档**: flask-swagger-ui 5.21.0 + OpenAPI 3.0
- **容器**: Docker + NVIDIA CUDA 12.1
- **反向代理**: Nginx + SSL/TLS
- **模型**: IndexTTS2 (PyTorch 2.8.0)

## 联系方式

- GitHub: https://github.com/index-tts/index-tts
- Email: indexspeech@bilibili.com
- 论文: https://arxiv.org/abs/2506.21619
