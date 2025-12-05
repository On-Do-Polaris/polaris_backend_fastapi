# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install uv for faster dependency installation
RUN pip install uv

# Copy dependency files
COPY pyproject.toml .
COPY requirements.txt .

# Install dependencies
RUN uv pip install --system -r requirements.txt

# Production stage
FROM python:3.11-slim AS production

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies (curl, wkhtmltopdf, fonts)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    wget \
    # wkhtmltopdf dependencies
    fontconfig \
    libfreetype6 \
    libjpeg62-turbo \
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
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY main.py .
COPY src/ ./src/
COPY ai_agent/ ./ai_agent/

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
