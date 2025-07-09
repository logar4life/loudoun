import subprocess
import sys

scripts = [
    ("loudoun.py", "Step 1: Scraping and downloading PDFs..."),
    ("loudoun_pdf_processor.py", "Step 2: Making PDFs searchable..."),
    ("loudoun_pdf_analyzer.py", "Step 3: Analyzing searchable PDFs...")
]

for script, message in scripts:
    print(f"\n{message}")
    result = subprocess.run([sys.executable, script])
    if result.returncode != 0:
        print(f"Error: {script} failed with exit code {result.returncode}")
        sys.exit(result.returncode)

print("\nAll steps completed successfully!")
