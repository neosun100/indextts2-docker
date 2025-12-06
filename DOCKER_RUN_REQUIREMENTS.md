# IndexTTS2 Docker 容器运行前提条件

## 🔧 物理机要求

### 必需条件

1. **NVIDIA GPU**
   - 支持 CUDA 12.1 或更高版本
   - 建议显存：12GB+

2. **NVIDIA 驱动**
   ```bash
   # 检查驱动是否安装
   nvidia-smi
   ```

3. **Docker**
   ```bash
   # 检查 Docker 版本
   docker --version
   # 建议版本：20.10+
   ```

4. **nvidia-docker2** (Docker GPU 支持)
   ```bash
   # 检查是否安装
   docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
   ```

## 📁 目录准备

### ❌ 不需要手动创建

Docker 会**自动创建**挂载目录，无需手动操作：
- `/tmp/indextts-outputs/` - Docker 自动创建

### ✅ 可选：提前创建（推荐）

虽然不是必需的，但提前创建可以设置权限：

```bash
# 可选：提前创建并设置权限
mkdir -p /tmp/indextts-outputs
chmod 755 /tmp/indextts-outputs
```

## 🚀 启动命令

### 标准启动（推荐）

```bash
docker run -d \
  --name indextts2 \
  --restart=always \
  --gpus all \
  -p 7870:7870 \
  -p 8002:8002 \
  -v /tmp/indextts-outputs:/app/outputs \
  indextts2:latest
```

### 参数说明

| 参数 | 说明 | 必需 |
|------|------|------|
| `-d` | 后台运行 | 是 |
| `--name indextts2` | 容器名称 | 推荐 |
| `--restart=always` | 自动重启 | 推荐 |
| `--gpus all` | 使用所有GPU | 是 |
| `-p 7870:7870` | Web UI 端口 | 是 |
| `-p 8002:8002` | API 端口 | 是 |
| `-v /tmp/indextts-outputs:/app/outputs` | 音频文件挂载 | 是 |

## ✅ 启动前检查清单

运行以下命令确认环境就绪：

```bash
# 1. 检查 GPU
nvidia-smi

# 2. 检查 Docker
docker --version

# 3. 检查 Docker GPU 支持
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# 4. 检查镜像是否存在
docker images indextts2:latest

# 5. 检查端口是否被占用
netstat -tuln | grep -E ':(7870|8002)'
```

## 🎯 完整启动流程

### 方式1：从本地镜像启动

```bash
# 1. 确认镜像存在
docker images indextts2:latest

# 2. 启动容器（目录会自动创建）
docker run -d \
  --name indextts2 \
  --restart=always \
  --gpus all \
  -p 7870:7870 \
  -p 8002:8002 \
  -v /tmp/indextts-outputs:/app/outputs \
  indextts2:latest

# 3. 等待服务启动（约60秒）
sleep 60

# 4. 验证服务
curl http://localhost:8002/health
curl -I http://localhost:7870/
```

### 方式2：从镜像文件导入并启动

```bash
# 1. 导入镜像
docker load < indextts2-allinone.tar.gz

# 2. 启动容器
docker run -d \
  --name indextts2 \
  --restart=always \
  --gpus all \
  -p 7870:7870 \
  -p 8002:8002 \
  -v /tmp/indextts-outputs:/app/outputs \
  indextts2:latest

# 3. 验证
sleep 60 && curl http://localhost:8002/health
```

## 📊 验证运行状态

```bash
# 查看容器状态
docker ps | grep indextts2

# 查看容器日志
docker logs -f indextts2

# 查看挂载目录
ls -la /tmp/indextts-outputs/

# 测试 API
curl http://localhost:8002/health

# 测试 Web UI
curl -I http://localhost:7870/
```

## ⚠️ 常见问题

### 问题1：端口被占用

```bash
# 查看占用端口的进程
netstat -tuln | grep -E ':(7870|8002)'

# 停止占用端口的容器
docker ps | grep -E '7870|8002'
docker stop <container_id>
```

### 问题2：GPU 不可用

```bash
# 检查 nvidia-docker2
dpkg -l | grep nvidia-docker

# 重启 Docker
sudo systemctl restart docker

# 测试 GPU
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### 问题3：容器启动失败

```bash
# 查看详细日志
docker logs indextts2

# 删除并重新创建
docker rm -f indextts2
docker run -d --name indextts2 --restart=always --gpus all \
  -p 7870:7870 -p 8002:8002 \
  -v /tmp/indextts-outputs:/app/outputs \
  indextts2:latest
```

## 🎉 启动成功标志

当看到以下内容时，表示启动成功：

1. **健康检查通过**
   ```bash
   $ curl http://localhost:8002/health
   {"status":"ok"}
   ```

2. **Web UI 可访问**
   ```bash
   $ curl -I http://localhost:7870/
   HTTP/1.1 200 OK
   ```

3. **容器运行正常**
   ```bash
   $ docker ps | grep indextts2
   indextts2   Up 2 minutes   0.0.0.0:7870->7870/tcp, 0.0.0.0:8002->8002/tcp
   ```

4. **挂载目录存在**
   ```bash
   $ ls -la /tmp/indextts-outputs/
   drwxr-xr-x 2 root root 4096 ...
   ```

## 📝 总结

### 必需操作
1. ✅ 安装 NVIDIA 驱动
2. ✅ 安装 Docker + nvidia-docker2
3. ✅ 准备镜像（本地或导入）
4. ✅ 运行 docker run 命令

### 不需要操作
1. ❌ 手动创建 `/tmp/indextts-outputs/` 目录（Docker 自动创建）
2. ❌ 安装 Python 或其他依赖（镜像已包含）
3. ❌ 下载模型文件（镜像已包含）
4. ❌ 配置网络访问 HuggingFace（镜像已包含）

**一条命令即可启动！** 🚀
