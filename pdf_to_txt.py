"""
PDF to Text Conversion Service
Extracts text from PDF files
"""
import os
import fitz  # PyMuPDF

def pdf_to_txt(input_path, output_path):
    try:
        pdf_document = fitz.open(input_path)
        page_count = pdf_document.page_count  # ✅ store before close

        full_text = []

        for page_num in range(page_count):
            page = pdf_document[page_num]
            text = page.get_text()

            if text.strip():
                full_text.append(f"--- Page {page_num + 1} ---\n")
                full_text.append(text)
                full_text.append("\n")

        pdf_document.close()  # safe to close now

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("".join(full_text))

        input_size = os.path.getsize(input_path)
        output_size = os.path.getsize(output_path)

        return {
            "success": True,
            "input_size": input_size,
            "output_size": output_size,
            "output_path": output_path,
            "page_count": page_count,  # ✅ use stored value
        }

    except Exception as e:
        return {"success": False, "error": str(e)}



def pdf_to_txt_batch(input_paths, output_dir):
    """
    Extract text from multiple PDFs
    
    Args:
        input_paths: List of input PDF paths
        output_dir: Directory to save outputs
        
    Returns:
        list: Results for each PDF
    """
    results = []
    
    for input_path in input_paths:
        filename = os.path.basename(input_path)
        name, ext = os.path.splitext(filename)
        output_path = os.path.join(output_dir, f"{name}.txt")
        
        result = pdf_to_txt(input_path, output_path)
        result['filename'] = filename
        results.append(result)
    
    return results