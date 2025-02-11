pdf_extraction_code = """
import fitz  # PyMuPDF
from pdf2docx_custom import Converter

def capture_images(pdf_path, output_dir="temp_images"):
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return
    
    pdf_doc = fitz.open(pdf_path)
    os.makedirs(output_dir, exist_ok=True)
    cv = Converter(pdf_path)
    tables = cv.extract_tables()
    for idx, info in enumerate(tables):
        page_id = info['id']
        rect = info['position']
        if page_id < 0 or page_id >= len(pdf_doc):
            print(f"Warning: Invalid page_id {page_id} for table index {idx}")
            continue
        page = pdf_doc[page_id]
        # 使用 matrix=fitz.Matrix(2,2) 提升解析度
        pix = page.get_pixmap(clip=rect, matrix=fitz.Matrix(2, 2))
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"{os.path.splitext(os.path.basename(pdf_path))[0]}_page_{page_id}_table_{idx}_{timestamp}.png"
        output_path = os.path.join(output_dir, output_name)
        pix.save(output_path)
        print(f"Saved table screenshot: {output_path}")
    pdf_doc.close()
    """
