FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV HF_ENDPOINT=https://hf-mirror.com
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git git-lfs curl python3.11 python3.11-dev python3-pip \
    libsndfile1 ffmpeg && \
    rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

COPY . /app

RUN git lfs install && git lfs pull

RUN uv sync --all-extras && uv pip install flask flask-swagger-ui

# 预下载所有HuggingFace模型到镜像中
RUN uv run python3 -c "from indextts.infer_v2 import IndexTTS2; IndexTTS2(cfg_path='checkpoints/config.yaml', model_dir='checkpoints', use_fp16=True)" || true

EXPOSE 7870 8002

CMD ["bash", "-c", "uv run api_server.py & uv run webui_enhanced.py --server_name 0.0.0.0 --server_port 7870 --use_fp16"]
