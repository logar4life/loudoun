# Loudoun Data Processing API

A FastAPI application for processing Loudoun data with automated web scraping, PDF processing, and analysis capabilities.

## Features

- Web scraping with Selenium and Chrome/Chromium
- PDF processing and analysis
- OpenAI integration for data analysis
- Docker containerization with proper browser setup
- RESTful API endpoints for process management

## Prerequisites

- Docker and Docker Compose installed
- At least 2GB of available RAM for the container

## Quick Start

### Using Docker Compose (Recommended)

1. **Build and run the application:**
   ```bash
   docker-compose up --build
   ```

2. **Access the API:**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/

3. **Start data processing:**
   ```bash
   curl -X POST http://localhost:8000/start
   ```

4. **Check processing status:**
   ```bash
   curl http://localhost:8000/status
   ```

### Using Docker directly

1. **Build the image:**
   ```bash
   docker build -t loudoun-app .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8000:8000 \
     -v $(pwd)/loudoun_pdf:/app/loudoun_pdf \
     -v $(pwd)/loudoun_results.xlsx:/app/loudoun_results.xlsx \
     loudoun-app
   ```

## API Endpoints

- `GET /` - API information and available endpoints
- `POST /start` - Start the data processing pipeline
- `GET /status` - Get current processing status
- `GET /logs` - Get processing logs (last 50 by default)
- `GET /logs/full` - Get all processing logs

## Browser Setup

The application uses Chrome/Chromium with Selenium for web scraping. The Docker setup includes:

- **Chromium browser** - System-installed browser for headless operation
- **ChromeDriver** - WebDriver for browser automation
- **Xvfb** - Virtual display server for headless operation
- **Proper permissions** - Non-root user with necessary access

### Browser Configuration

The browser is configured with the following options for Docker compatibility:

- Headless mode enabled
- No sandbox (required for Docker)
- Disabled GPU acceleration
- Custom user data directory
- Remote debugging enabled
- Security settings optimized for automation

## Troubleshooting

### Chrome/Chromium fails to start

If you encounter browser startup issues:

1. **Check container logs:**
   ```bash
   docker-compose logs loudoun-app
   ```

2. **Test browser setup:**
   ```bash
   docker-compose exec loudoun-app python test_browser.py
   ```

3. **Verify system resources:**
   - Ensure at least 2GB RAM available
   - Check disk space (at least 1GB free)

### Common Issues

1. **"Chrome failed to start: exited abnormally"**
   - This is usually resolved by the current Docker setup
   - Ensure you're using the latest image: `docker-compose build --no-cache`

2. **Permission denied errors**
   - The container runs as non-root user (appuser)
   - All necessary directories have proper permissions

3. **Display issues**
   - Xvfb virtual display is automatically started
   - DISPLAY environment variable is set to :99

## Development

### Local Development (without Docker)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Chrome/ChromeDriver:**
   - Install Chrome browser
   - Install ChromeDriver (webdriver-manager will handle this automatically)

3. **Run the application:**
   ```bash
   uvicorn main:app --reload
   ```

### Testing

Run the browser test to verify setup:
```bash
python test_browser.py
```

## File Structure

```
loudoun/
├── main.py                 # FastAPI application
├── loudoun.py             # Web scraping script
├── loudoun_pdf_processor.py # PDF processing script
├── loudoun_pdf_analyzer.py # PDF analysis script
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
├── requirements.txt       # Python dependencies
├── start.sh              # Startup script for Docker
├── test_browser.py       # Browser test script
└── loudoun_pdf/          # PDF storage directory
```

## Environment Variables

- `DOCKER_ENV=true` - Indicates running in Docker environment
- `DISPLAY=:99` - Virtual display for headless operation
- `CHROME_BIN=/usr/bin/chromium` - Chrome binary location
- `CHROMEDRIVER_PATH=/usr/bin/chromedriver` - ChromeDriver location

## Volumes

The following directories are mounted as volumes:

- `./loudoun_pdf` - PDF storage directory
- `./loudoun_results.xlsx` - Results file

## Health Check

The container includes a health check that verifies the API is responding:
- Interval: 30 seconds
- Timeout: 10 seconds
- Retries: 3
- Start period: 40 seconds

## Support

For issues related to:
- **Browser automation**: Check the browser test script
- **Docker setup**: Verify Docker and Docker Compose versions
- **API functionality**: Check the FastAPI documentation at `/docs` 