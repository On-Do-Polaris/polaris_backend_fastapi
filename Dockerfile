# Build stage
FROM ubuntu:22.04 AS builder

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.11 and pip
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.11 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/* && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Install uv for faster dependency installation
RUN python3.11 -m pip install uv

# Copy dependency files
COPY pyproject.toml .
COPY requirements.txt .

# Install CPU-only PyTorch first (to avoid GPU version with Triton)
# Force CPU-only version by using PyTorch's CPU wheel index
RUN PIP_INDEX_URL=https://download.pytorch.org/whl/cpu \
    PIP_EXTRA_INDEX_URL=https://pypi.org/simple \
    uv pip install --python /usr/bin/python3.11 \
    torch torchvision torchaudio

# Install other dependencies
# PyTorch CPU version is already installed, dependencies will use it
RUN uv pip install --python /usr/bin/python3.11 -r requirements.txt

# Clean up build stage caches to reduce layer size
RUN rm -rf /root/.cache/pip /root/.cache/uv /tmp/* /var/tmp/* && \
    find /usr/local/lib/python3.11/dist-packages -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.11/dist-packages -type f -name "*.pyc" -delete 2>/dev/null || true && \
    find /usr/local/lib/python3.11/dist-packages -type f -name "*.pyo" -delete 2>/dev/null || true

# Production stage
FROM ubuntu:22.04 AS production

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.11
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.11 \
    && rm -rf /var/lib/apt/lists/* && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Install system dependencies (curl, wkhtmltopdf, fonts)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    wget \
    # wkhtmltopdf dependencies
    fontconfig \
    libfreetype6 \
    libjpeg-turbo8 \
    libpng16-16 \
    libx11-6 \
    libxcb1 \
    libxext6 \
    libxrender1 \
    xfonts-75dpi \
    xfonts-base \
    # Korean fonts for PDF generation
    fonts-nanum \
    fonts-nanum-extra \
    fonts-baekmuk \
    && rm -rf /var/lib/apt/lists/*

# Install wkhtmltopdf (latest version)
RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_amd64.deb && \
    dpkg -i wkhtmltox_0.12.6.1-2.jammy_amd64.deb || true && \
    apt-get install -f -y && \
    dpkg -i wkhtmltox_0.12.6.1-2.jammy_amd64.deb && \
    rm wkhtmltox_0.12.6.1-2.jammy_amd64.deb && \
    wkhtmltopdf --version

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/dist-packages /usr/local/lib/python3.11/dist-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY main.py .
COPY src/ ./src/
COPY ai_agent/ ./ai_agent/
COPY static/ ./static/
COPY utils/ ./utils/

# Create scratch directory for output files (before changing user)
RUN mkdir -p /app/scratch && chmod 755 /app/scratch

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
