from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
import subprocess
import sys
import os
import asyncio
import threading
import time
from datetime import datetime
from typing import Dict, Any
import json

app = FastAPI(
    title="Loudoun Data Processing API",
    description="API to orchestrate Loudoun data scraping, PDF processing, and analysis",
    version="1.0.0"
)

# Global state to track processing status
processing_status = {
    "is_running": False,
    "current_step": None,
    "progress": 0,
    "logs": [],
    "start_time": None,
    "end_time": None,
    "error": None
}

def log_message(message: str):
    """Add a log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    processing_status["logs"].append(log_entry)
    print(log_entry)

def run_script(script_path: str, script_name: str) -> bool:
    """Run a Python script and return success status"""
    try:
        log_message(f"Starting {script_name}...")
        
        # Change to the script directory
        script_dir = os.path.dirname(os.path.abspath(script_path))
        original_dir = os.getcwd()
        os.chdir(script_dir)
        
        # Run the script
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout
            encoding='utf-8',
            errors='ignore'
        )
        
        # Restore original directory
        os.chdir(original_dir)
        
        if result.returncode == 0:
            log_message(f"✅ {script_name} completed successfully")
            if result.stdout:
                log_message(f"Output: {result.stdout.strip()}")
            return True
        else:
            log_message(f"❌ {script_name} failed with return code {result.returncode}")
            if result.stderr:
                log_message(f"Error: {result.stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        log_message(f"⏰ {script_name} timed out after 1 hour")
        return False
    except Exception as e:
        log_message(f"❌ Error running {script_name}: {str(e)}")
        return False

def process_all_scripts():
    """Process all scripts in sequence"""
    try:
        processing_status["is_running"] = True
        processing_status["start_time"] = datetime.now().isoformat()
        processing_status["error"] = None
        processing_status["logs"] = []
        
        # Get the current directory (loudoun folder)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Step 1: Run loudoun.py (scraping)
        processing_status["current_step"] = "Scraping data and downloading PDFs"
        processing_status["progress"] = 0
        log_message("🚀 Starting Loudoun data processing pipeline...")
        
        loudoun_script = os.path.join(current_dir, "loudoun.py")
        if not run_script(loudoun_script, "loudoun.py"):
            processing_status["error"] = "Failed to scrape data and download PDFs"
            return
        
        processing_status["progress"] = 33
        log_message("📊 Data scraping completed successfully")
        
        # Step 2: Run loudoun_pdf_processor.py (PDF processing)
        processing_status["current_step"] = "Processing PDFs to make them searchable"
        processing_status["progress"] = 33
        
        processor_script = os.path.join(current_dir, "loudoun_pdf_processor.py")
        if not run_script(processor_script, "loudoun_pdf_processor.py"):
            processing_status["error"] = "Failed to process PDFs"
            return
        
        processing_status["progress"] = 66
        log_message("🔍 PDF processing completed successfully")
        
        # Step 3: Run loudoun_pdf_analyzer.py (PDF analysis)
        processing_status["current_step"] = "Analyzing PDFs with OpenAI"
        processing_status["progress"] = 66
        
        analyzer_script = os.path.join(current_dir, "loudoun_pdf_analyzer.py")
        if not run_script(analyzer_script, "loudoun_pdf_analyzer.py"):
            processing_status["error"] = "Failed to analyze PDFs"
            return
        
        processing_status["progress"] = 100
        processing_status["current_step"] = "Completed"
        log_message("🎉 All processing completed successfully!")
        
    except Exception as e:
        processing_status["error"] = f"Unexpected error: {str(e)}"
        log_message(f"❌ Unexpected error: {str(e)}")
    finally:
        processing_status["is_running"] = False
        processing_status["end_time"] = datetime.now().isoformat()

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Loudoun Data Processing API",
        "version": "1.0.0",
        "endpoints": {
            "/start": "Start the processing pipeline",
            "/status": "Get current processing status",
            "/logs": "Get processing logs"
        }
    }

@app.post("/start")
async def start_processing(background_tasks: BackgroundTasks):
    """Start the processing pipeline"""
    if processing_status["is_running"]:
        raise HTTPException(status_code=400, detail="Processing is already running")
    
    # Reset status
    processing_status["is_running"] = False
    processing_status["current_step"] = None
    processing_status["progress"] = 0
    processing_status["logs"] = []
    processing_status["start_time"] = None
    processing_status["end_time"] = None
    processing_status["error"] = None
    
    # Start processing in background
    background_tasks.add_task(process_all_scripts)
    
    return {
        "message": "Processing started",
        "status": "Processing will begin shortly"
    }

@app.get("/status")
async def get_status():
    """Get current processing status"""
    return {
        "is_running": processing_status["is_running"],
        "current_step": processing_status["current_step"],
        "progress": processing_status["progress"],
        "start_time": processing_status["start_time"],
        "end_time": processing_status["end_time"],
        "error": processing_status["error"],
        "log_count": len(processing_status["logs"])
    }

@app.get("/logs")
async def get_logs(limit: int = 50):
    """Get processing logs"""
    logs = processing_status["logs"][-limit:] if limit > 0 else processing_status["logs"]
    return {
        "logs": logs,
        "total_logs": len(processing_status["logs"]),
        "showing_last": len(logs)
    }

@app.get("/logs/full")
async def get_full_logs():
    """Get all processing logs"""
    return {
        "logs": processing_status["logs"],
        "total_logs": len(processing_status["logs"])
    }

@app.post("/reset")
async def reset_status():
    """Reset processing status"""
    processing_status["is_running"] = False
    processing_status["current_step"] = None
    processing_status["progress"] = 0
    processing_status["logs"] = []
    processing_status["start_time"] = None
    processing_status["end_time"] = None
    processing_status["error"] = None
    
    return {"message": "Status reset successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 