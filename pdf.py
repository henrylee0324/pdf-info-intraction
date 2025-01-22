from dotenv import load_dotenv
import shutil
import os
from llm.claude import CLAUDE
from llm.gemini import GEMINI
from datetime import datetime
import fitz  # PyMuPDF
import os
from pdf2docx_custom import Converter



class Pdf:
    def __init__(self, llm_name, api_key):
        if not api_key:
            raise ValueError("API key is required to initialize the LLM.")
        llm_mapping = {
            "claude": CLAUDE,
            "gemini": GEMINI,
        }
        if llm_name in llm_mapping:
            self.llm = llm_mapping[llm_name](api_key)
        else:
            raise NameError(f"Unsupported LLM name: {llm_name}. Available options are: {', '.join(llm_mapping.keys())}")
    
    def _capture_table_images(self, pdf_path, output_dir="temp_images"):
        """
        根據 table_infos 內的每個項目，將對應 PDF 頁面的表格區域截圖後儲存成 png。
        
        Args:
            pdf_path (str)      : PDF 檔案路徑
            table_infos (list)  : [{'id': page_id, 'position': Rect(...)}, ...]
            output_dir (str)    : 輸出圖片的資料夾
        """
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            return
        
        # 開啟 PDF
        pdf_doc = fitz.open(pdf_path)
        
        # 輸出資料夾若不存在就自動建立
        os.makedirs(output_dir, exist_ok=True)
        cv = Converter(pdf_path)
        tables = cv.extract_tables()
        for idx, info in enumerate(tables):
            page_id = info['id']           # 頁碼 (注意 0-based or 1-based)
            rect    = info['position']     # Rect(x0, y0, x1, y1)

            # 如果 page_id 與 pdf_doc 的頁碼對不上，要調整 (e.g., page_id - 1)
            # 先假設你回傳的 id = fitz 裡的 page index (0-based)
            if page_id < 0 or page_id >= len(pdf_doc):
                print(f"Warning: Invalid page_id {page_id} for table index {idx}")
                continue

            # 取得對應的 page
            page = pdf_doc[page_id]

            # 用 get_pixmap 擷取該區域 (clip=rect)
            # 可加 matrix=fitz.Matrix(2, 2) 提升解析度
            pix = page.get_pixmap(clip=rect)

            # 組出輸出檔名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"{os.path.splitext(os.path.basename(pdf_path))[0]}_page_{page_id}_table_{idx}_{timestamp}.png"
            output_path = os.path.join(output_dir, output_name)

            # 存檔
            pix.save(output_path)
            print(f"Saved table screenshot: {output_path}")
        
        pdf_doc.close()
    def extraction(self, pdf_path, table_image_dir = "table_images", temp_image_dir = "temp_images", capture_images = None, table_image_check_prompt = ""):
        os.makedirs(table_image_dir, exist_ok=True)
        os.makedirs(temp_image_dir, exist_ok=True)
        if capture_images == None:
            capture_images = self._capture_table_images
        if table_image_check_prompt == "":
            table_image_check_prompt = """如果圖片內是一個完整的表格，回答 'True'，否則回答 'False'。"""

        capture_images(pdf_path, output_dir=temp_image_dir)
        table_paths = []
        for root, dirs, files in os.walk(temp_image_dir):
            for file in files:
                if file.lower().endswith('.png'):
                    # 檔案完整路徑
                    source_path = os.path.join(root, file)
                    prompt = table_image_check_prompt
                    res = self.llm.generate(prompt=prompt, image_path = source_path)
                    if 'True' in res:
                        # 目標檔案的完整路徑
                        target_path = os.path.join(table_image_dir, file)

                        # 移動檔案
                        shutil.move(source_path, target_path)
                        table_paths.append(target_path)
                        print(f"已移動: {source_path} -> {target_path}")
                    else:
                        try:
                            os.remove(source_path)
                            print(f"Deleted: {source_path}")
                        except Exception as e:
                            print(f"Error deleting {source_path}: {e}")
        return table_paths


if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    pdf = Pdf(llm_name = "claude", api_key = api_key)
    pdf.extraction(pdf_path = "./input/Cathays Weekly View.pdf")