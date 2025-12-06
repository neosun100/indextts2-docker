# IndexTTS2 Docker 镜像说明

## 镜像信息

- **镜像名称**: `indextts2:latest`
- **镜像大小**: 28GB
- **类型**: All-in-One 完全独立镜像

## ✅ 完全独立 (All-in-One)

这是一个**完全独立**的Docker镜像，包含了运行IndexTTS2所需的**所有内容**：

### 已打包内容

1. **系统依赖**
   - NVIDIA CUDA 12.1.0 + cuDNN 8
   - Python 3.10/3.11
   - FFmpeg, libsndfile
   - Git, Git LFS

2. **Python依赖** (所有包)
   - PyTorch 2.8.0 (CUDA 12.8)
   - Gradio 5.45.0
   - Flask 3.1.2 + Swagger UI
   - Transformers 4.52.1
   - 所有其他依赖 (共179个包)

3. **IndexTTS2模型文件** (4.4GB)
   - `gpt.pth` (3.3GB)
   - `s2mel.pth` (1.2GB)
   - `bpe.model` (465KB)
   - `feat1.pt`, `feat2.pt`
   - `pinyin.vocab`
   - `qwen0.6bemo4-merge/`
   - `hf_cache/` (本地缓存的模型)

4. **HuggingFace预下载模型** (2.8GB)
   - `amphion/MaskGCT` (semantic_codec)
   - `funasr/campplus` (说话人识别)
   - `nvidia/bigvgan_v2_22khz_80band_256x` (声码器)
   - 所有其他运行时需要的模型

5. **应用代码**
   - Web UI (webui_enhanced.py)
   - API Server (api_server.py)
   - IndexTTS2核心代码
   - 配置文件

## 🚀 使用方法

### 前提条件

**物理机需要**：
- NVIDIA GPU (支持CUDA 12.1+)
- 已安装NVIDIA驱动
- 已安装Docker
- 已安装nvidia-docker2 (Docker GPU支持)

### 一键启动

```bash
docker run -d \
  --name indextts2 \
  --restart=always \
  --gpus all \
  -p 7870:7870 \
  -p 8002:8002 \
  indextts2:latest
```

### 参数说明

- `--restart=always`: 自动重启（服务器重启、容器崩溃都会自动恢复）
- `--gpus all`: 使用所有GPU
- `-p 7870:7870`: Web UI端口
- `-p 8002:8002`: API端口

## ✅ 完全独立性验证

### 无需外部依赖

- ❌ **不需要**外部模型下载
- ❌ **不需要**HuggingFace网络访问
- ❌ **不需要**额外的Python包安装
- ❌ **不需要**挂载本地目录

### 只需要

- ✅ NVIDIA GPU + 驱动
- ✅ Docker + nvidia-docker2
- ✅ 这个镜像

## 📦 镜像导出/导入

### 导出镜像

```bash
docker save indextts2:latest | gzip > indextts2-allinone.tar.gz
```

### 导入镜像

```bash
docker load < indextts2-allinone.tar.gz
```

### 推送到私有仓库

```bash
# 标记镜像
docker tag indextts2:latest your-registry.com/indextts2:latest

# 推送
docker push your-registry.com/indextts2:latest

# 在其他机器拉取
docker pull your-registry.com/indextts2:latest
```

## 🔧 验证镜像完整性

### 检查模型文件

```bash
docker run --rm indextts2:latest ls -lh /app/checkpoints/
```

### 检查HuggingFace缓存

```bash
docker run --rm indextts2:latest du -sh /root/.cache/huggingface/
```

### 测试启动

```bash
docker run --rm --gpus all indextts2:latest \
  uv run python3 -c "from indextts.infer_v2 import IndexTTS2; print('OK')"
```

## 📊 镜像层级结构

```
indextts2:latest (28GB)
├── CUDA 12.1.0 基础镜像 (~8GB)
├── 系统依赖 (~500MB)
├── Python依赖 (~12GB)
│   ├── PyTorch + CUDA库 (~10GB)
│   └── 其他包 (~2GB)
├── IndexTTS2模型 (~4.4GB)
├── HuggingFace模型 (~2.8GB)
└── 应用代码 (~100MB)
```

## 🌐 服务端点

启动后可访问：

- **Web UI**: http://localhost:7870
- **API**: http://localhost:8002
- **Swagger文档**: http://localhost:8002/docs/
- **健康检查**: http://localhost:8002/health

## 🔄 自动重启策略

容器配置了 `--restart=always`，确保：

1. **容器崩溃** → 自动重启
2. **服务器重启** → 自动启动
3. **Docker重启** → 自动启动
4. **手动停止** → 不会自动启动 (使用 `docker stop`)

## 💾 存储需求

- **镜像大小**: 28GB
- **运行时内存**: 建议16GB+ RAM
- **GPU显存**: 建议12GB+ VRAM

## 🎯 适用场景

✅ **适合**：
- 生产环境部署
- 离线环境部署
- 快速迁移到新服务器
- 不依赖外部网络的环境

❌ **不适合**：
- 开发调试（建议使用源码）
- 频繁修改代码（建议挂载卷）

## 📝 构建信息

- **构建时间**: 2025-12-06
- **基础镜像**: nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04
- **Python版本**: 3.10.12
- **PyTorch版本**: 2.8.0+cu128
- **IndexTTS版本**: 2.0.0

## 🔗 相关链接

- GitHub: https://github.com/index-tts/index-tts
- 论文: https://arxiv.org/abs/2506.21619
- HuggingFace: https://huggingface.co/IndexTeam/IndexTTS-2
