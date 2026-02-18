FROM python:3.11-slim

# Install system dependencies (WITHOUT Rust - saves 1GB+)
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    fonts-liberation \
    fontconfig \
    libreoffice-core-nogui \
    libreoffice-writer-nogui \
    libreoffice-calc-nogui \
    libreoffice-impress-nogui \
    ffmpeg \
    ghostscript \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libgl1 \
    potrace \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* \
 && rm -rf /tmp/* \
 && rm -rf /usr/share/doc/* \
 && rm -rf /usr/share/man/*

WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && rm -rf /root/.cache

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads outputs

# Expose port (Railway will set this via environment)
EXPOSE 5000

# Start command
CMD ["gunicorn", "main:app", "--workers", "1", "--threads", "4", "--worker-class", "gthread", "--timeout", "120", "--keep-alive", "5", "--bind", "0.0.0.0:5000", "--log-level", "info"]