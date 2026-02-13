FROM python:3.11-slim

# Install system dependencies including potrace, Rust (for vtracer), and build tools
RUN apt-get update && apt-get install -y \
    fonts-dejavu-core \
    fonts-dejavu-extra \
    fonts-liberation \
    fontconfig \
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    ffmpeg \
    ghostscript \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    potrace \
    curl \
    build-essential \
    pkg-config \
 && rm -rf /var/lib/apt/lists/*

# Install Rust (required for vtracer compilation)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads outputs

# Expose port (Railway will set this via environment)
EXPOSE 5000

# Start command
CMD ["python", "main.py"]