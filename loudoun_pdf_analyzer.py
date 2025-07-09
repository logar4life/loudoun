import os
import glob
import pandas as pd
import tiktoken
from openai import OpenAI
from pathlib import Path
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up OpenAI API with modern client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using PyMuPDF"""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""

def split_text_into_chunks(text, max_tokens=2000):
    """Split text into chunks to avoid token limits"""
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        words = text.split()
        chunks, current_chunk = [], []

        for word in words:
            current_chunk.append(word)
            token_count = len(enc.encode(" ".join(current_chunk)))
            if token_count > max_tokens:
                chunks.append(" ".join(current_chunk[:-1]))
                current_chunk = [word]

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks
    except Exception as e:
        print(f"Error splitting text into chunks: {e}")
        # Fallback: simple split by sentences
        return [text[i:i+4000] for i in range(0, len(text), 4000)]

def analyze_pdf_with_openai(text, pdf_name):
    """Use OpenAI API to extract owner name, address, APN/tax ID, and date with chunking"""
    try:
        # Split text into chunks
        chunks = split_text_into_chunks(text)
        all_results = []

        for i, chunk in enumerate(chunks):
            print(f"  Processing chunk {i+1}/{len(chunks)}...")
            
            prompt = f"""
            Extract the following information from this PDF text chunk:
            1. Owner Name (or Property Owner)
            2. Property Address (full address)
            3. Tax ID/APN (Assessment Parcel Number or Tax Identification Number)
            4. Date (Sale Date, Deed Date, or any clearly labeled date in the document)

            Return the information in JSON format like this:
            {{
                "date": "2024-05-01",
                "owner_name": "John Doe",
                "address": "123 Main St, City, State ZIP",
                "apn_taxid": "123-456-789"
            }}

            If any information is not found, use "Not found" as the value.
            Only extract information that is clearly present in the text.

            PDF Name: {pdf_name}
            Text Content:
            {chunk}
            """

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a data extraction specialist. Extract only the requested information and return it in valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )

            # Extract the response content
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON from the response
            try:
                # Remove any markdown formatting if present
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                
                result = json.loads(content)
                all_results.append(result)
            except json.JSONDecodeError:
                # If JSON parsing fails, create a structured response
                all_results.append({
                    "date": "Error parsing response",
                    "owner_name": "Error parsing response",
                    "address": "Error parsing response", 
                    "apn_taxid": "Error parsing response"
                })

        # Combine results and find the most complete information
        combined_info = {
            "date": "Not found",
            "owner_name": "Not found",
            "address": "Not found", 
            "apn_taxid": "Not found"
        }
        
        for result in all_results:
            if isinstance(result, dict) and "error" not in result:
                for key in combined_info:
                    if key in result and result[key] != "Not found" and combined_info[key] == "Not found":
                        combined_info[key] = result[key]

        return combined_info

    except Exception as e:
        print(f"Error analyzing PDF {pdf_name} with OpenAI: {e}")
        return {
            "date": "Error occurred",
            "owner_name": "Error occurred",
            "address": "Error occurred",
            "apn_taxid": "Error occurred"
        }

def clean_apn_taxid(apn):
    """Clean APN/Tax ID by removing all non-numeric characters."""
    if not isinstance(apn, str):
        return apn
    # Remove all non-digit characters
    cleaned = ''.join(c for c in apn if c.isdigit())
    return cleaned if cleaned else apn

def main():
    # Path to the PDF directory
    pdf_directory = os.path.join(os.path.dirname(__file__), "loudoun_pdf")
    
    # Find all searchable PDFs
    searchable_pdfs = glob.glob(os.path.join(pdf_directory, "*_searchable.pdf"))
    
    if not searchable_pdfs:
        print("No searchable PDFs found!")
        return
    
    print(f"Found {len(searchable_pdfs)} searchable PDFs")
    
    # Store all results
    all_results = []
    
    for pdf_path in searchable_pdfs:
        pdf_name = os.path.basename(pdf_path)
        print(f"Processing: {pdf_name}")
        
        # Extract text from PDF
        text = extract_text_from_pdf(pdf_path)
        
        if not text.strip():
            print(f"No text extracted from {pdf_name}")
            result = {
                "pdf_name": pdf_name,
                "date": "No text extracted",
                "owner_name": "No text extracted",
                "address": "No text extracted",
                "apn_taxid": "No text extracted"
            }
            all_results.append(result)
            continue
        
        # Analyze with OpenAI
        analysis_result = analyze_pdf_with_openai(text, pdf_name)
        
        # Add to results
        apn_raw = analysis_result.get("apn_taxid", "Not Found")
        result = {
            "pdf_name": pdf_name,
            "date": analysis_result.get("date", "Not Found"),
            "owner_name": analysis_result.get("owner_name", "Not Found"),
            "address": analysis_result.get("address", "Not Found"),
            "apn_taxid": clean_apn_taxid(apn_raw)
        }
        all_results.append(result)
        print(f"Completed: {pdf_name}")
    
    # Print all results in JSON format
    print("\n" + "="*50)
    print("ANALYSIS RESULTS (JSON FORMAT)")
    print("="*50)
    print(json.dumps(all_results, indent=2, ensure_ascii=False))
    print(f"\nTotal PDFs processed: {len(searchable_pdfs)}")

if __name__ == "__main__":
    main() 