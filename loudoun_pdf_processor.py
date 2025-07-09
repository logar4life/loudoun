import easyocr
from pdf2image import convert_from_path
from PIL import Image
from fpdf import FPDF
import numpy as np
import re
import os
import glob
from pathlib import Path
import hashlib

def get_file_hash(file_path, chunk_size=8192):
    """
    Calculate SHA-256 hash of a file
    """
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def remove_duplicate_pdfs(folder_path):
    """
    Remove duplicate PDF files based on file hash
    """
    folder_path = Path(folder_path).resolve()
    
    if not folder_path.exists():
        print(f"Error: Folder {folder_path} does not exist!")
        return
    
    # Find all PDF files in the folder
    pdf_files = list(folder_path.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {folder_path}")
        return
    
    print(f"Checking for duplicates among {len(pdf_files)} PDF files...")
    
    # Group files by their hash
    file_hashes = {}
    for pdf_file in pdf_files:
        file_hash = get_file_hash(pdf_file)
        if file_hash not in file_hashes:
            file_hashes[file_hash] = []
        file_hashes[file_hash].append(pdf_file)
    
    # Remove duplicates, keeping the file with the shortest name (usually the original)
    duplicates_removed = 0
    for file_hash, files in file_hashes.items():
        if len(files) > 1:
            # Sort by filename length to keep the shortest (original) name
            files.sort(key=lambda x: len(x.name))
            original_file = files[0]
            duplicate_files = files[1:]
            
            print(f"  Found duplicates for {original_file.name}:")
            for duplicate in duplicate_files:
                print(f"    - {duplicate.name} (duplicate)")
            
            # Remove duplicate files
            for duplicate in duplicate_files:
                try:
                    duplicate.unlink()
                    print(f"    ✓ Removed duplicate: {duplicate.name}")
                    duplicates_removed += 1
                except Exception as e:
                    print(f"    ✗ Error removing duplicate {duplicate.name}: {str(e)}")
    
    if duplicates_removed > 0:
        print(f"\nRemoved {duplicates_removed} duplicate PDF files.")
    else:
        print("No duplicate PDF files found.")
    
    return duplicates_removed

def process_pdf_to_searchable(input_pdf_path, output_pdf_path, reader):
    """
    Process a single PDF file to make it searchable using OCR
    """
    try:
        print(f"Processing: {input_pdf_path}")
        
        # Convert PDF to images
        pages = convert_from_path(input_pdf_path, 300)
        
        # Create new PDF
        pdf = FPDF()
        
        for i, page in enumerate(pages):
            print(f"  Processing page {i+1}/{len(pages)}")
            
            # Convert PIL image to numpy array for EasyOCR
            img_array = np.array(page)
            
            # Extract text using EasyOCR
            results = reader.readtext(img_array)
            
            # Combine all detected text and clean up special characters
            text = '\n'.join([result[1] for result in results])
            
            # Clean up text to remove problematic Unicode characters
            # Replace common problematic characters with ASCII equivalents
            text = text.replace('€', 'EUR')
            text = text.replace('£', 'GBP')
            text = text.replace('$', 'USD')
            text = text.replace('°', ' degrees')
            text = text.replace('±', '+/-')
            text = text.replace('×', 'x')
            text = text.replace('÷', '/')
            
            # Remove any remaining non-ASCII characters
            text = re.sub(r'[^\x00-\x7F]+', ' ', text)
            
            # Clean up extra whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, text)
        
        # Save the searchable PDF
        pdf.output(output_pdf_path)
        print(f"  ✓ Completed: {output_pdf_path}")
        return True
        
    except Exception as e:
        print(f"  ✗ Error processing {input_pdf_path}: {str(e)}")
        return False

def process_all_pdfs_in_folder(folder_path):
    """
    Process all PDF files in the specified folder and delete originals after creating searchable versions
    """
    # Get the absolute path to the folder
    folder_path = Path(folder_path).resolve()
    
    if not folder_path.exists():
        print(f"Error: Folder {folder_path} does not exist!")
        return
    
    # First, remove duplicate PDFs
    print("Step 1: Removing duplicate PDFs...")
    remove_duplicate_pdfs(folder_path)
    print()
    
    # Find all PDF files in the folder (excluding already searchable ones)
    pdf_files = [f for f in folder_path.glob("*.pdf") if not f.name.endswith("_searchable.pdf")]
    
    if not pdf_files:
        print(f"No original PDF files found in {folder_path}")
        return
    
    print(f"Step 2: Found {len(pdf_files)} original PDF files to process:")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file.name}")
    
    # Initialize EasyOCR reader once
    print("\nStep 3: Initializing EasyOCR reader...")
    reader = easyocr.Reader(['en'])
    print("EasyOCR reader initialized.")
    
    print("\nStep 4: Starting OCR processing...")
    
    # Process each PDF file
    for pdf_file in pdf_files:
        # Create output filename with "_searchable" suffix
        output_filename = pdf_file.stem + "_searchable.pdf"
        output_path = pdf_file.parent / output_filename
        
        # Process the PDF
        success = process_pdf_to_searchable(str(pdf_file), str(output_path), reader)
        
        # If searchable PDF was created successfully, delete the original
        if success and output_path.exists():
            try:
                pdf_file.unlink()
                print(f"  ✓ Deleted original: {pdf_file.name}")
            except Exception as e:
                print(f"  ✗ Error deleting original {pdf_file.name}: {str(e)}")
        else:
            print(f"  ⚠ Warning: Searchable PDF not created for {pdf_file.name}, keeping original")
        
        print()  # Add blank line between files
    
    print("All PDF processing completed!")
    print("Original PDF files have been deleted. Only searchable PDFs remain in the folder.")

if __name__ == "__main__":
    # Process all PDFs in the loudoun_pdf folder
    pdf_folder = "loudoun_pdf"
    process_all_pdfs_in_folder(pdf_folder) 