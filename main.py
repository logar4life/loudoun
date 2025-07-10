import subprocess
import sys
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

scripts = [
    ("loudoun.py", "Step 1: Scraping and downloading PDFs..."),
    ("loudoun_pdf_processor.py", "Step 2: Making PDFs searchable..."),
    ("loudoun_pdf_analyzer.py", "Step 3: Analyzing searchable PDFs...")
]

app = FastAPI()

@app.post("/run_all")
def run_all():
    results = []
    for script, message in scripts:
        result = subprocess.run([sys.executable, script])
        results.append({
            "step": message,
            "script": script,
            "returncode": result.returncode
        })
        if result.returncode != 0:
            return JSONResponse(status_code=500, content={
                "success": False,
                "error": f"{script} failed with exit code {result.returncode}",
                "results": results
            })
    return {"success": True, "results": results}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
