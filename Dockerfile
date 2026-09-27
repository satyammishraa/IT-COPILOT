FROM python:3.11-slim

# Hugging Face Spaces runs containers as a non-root user with id 1000
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/home/user/.cache/huggingface
WORKDIR /home/user/app

# 1) CPU-only PyTorch (~200 MB instead of ~2.5 GB for the GPU build)
RUN pip install --no-cache-dir --user torch --index-url https://download.pytorch.org/whl/cpu

# 2) Project dependencies
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 3) Download the embedding model at build time, so the app starts fast
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# 4) App code (the .env file is excluded by .dockerignore; keys come from Space secrets)
COPY --chown=user . .

EXPOSE 8501
CMD ["streamlit", "run", "src/ui.py", "--server.port=8501", "--server.address=0.0.0.0"]