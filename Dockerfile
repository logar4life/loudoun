# Use official Python image
FROM python:3.11-slim

# Set environment variables for headless operation
ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV DOCKER_ENV=true
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Install system dependencies including chromium and chromedriver
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    fonts-liberation \
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libxss1 \
    libasound2 \
    libgbm1 \
    libu2f-udev \
    libvulkan1 \
    xdg-utils \
    chromium \
    chromium-driver \
    xvfb \
    dbus-x11 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories for Chrome
RUN mkdir -p /tmp/chrome && \
    chmod 777 /tmp/chrome

# Create a non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /tmp/chrome

# Set workdir
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Make startup script executable
RUN chmod +x start.sh

# Create necessary directories and set permissions
RUN mkdir -p /app/loudoun_pdf && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Start the application using the startup script
CMD ["./start.sh"] 