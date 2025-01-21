import pdfplumber
from pdf2image import convert_from_path
from dotenv import load_dotenv
import shutil
import os
from llm.claude import CLAUDE
from llm.gemini import GEMINI



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
    
    def extraction(self, pdf_path, table_image_dir = "table_images", temp_image_dir = "temp_images"):
        os.makedirs(table_image_dir, exist_ok=True)
        os.makedirs(temp_image_dir, exist_ok=True)

        def is_valid_table(table, page):
            # 提取表格的數據內容
            table_data = table.extract()
            if not table_data or len(table_data) < 2:  # 表格行數少於 2，可能是誤檢
                return False
            # 根據表格的大小篩選
            bbox = table.bbox
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            if width < 50 or height < 50:  # 過小的區域排除
                return False
            # 判斷文字密度
            text_objects = page.within_bbox(bbox).extract_text()
            if not text_objects or len(text_objects.strip()) < 30:  # 文字過少可能是圖表
                return False
            # 檢查區域內是否包含大量圖形元素
            graphic_elements = page.within_bbox(bbox).objects.get("line", [])
            if len(graphic_elements) > 5:  # 如果有太多線條，可能是圖表
                return False

            return True

        # 讀取 PDF 文件
        with pdfplumber.open(pdf_path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                # 提取該頁的表格
                tables = page.find_tables()
                valid_tables = [table for table in tables if is_valid_table(table, page)]

                # 如果有有效表格，轉換該頁為圖片
                if valid_tables:
                    images = convert_from_path(pdf_path, first_page=page_number, last_page=page_number)
                    page_image = images[0]

                    for table_index, table in enumerate(valid_tables, start=1):
                        # 提取表格的邊界（bounding box）
                        bbox = table.bbox  # (x0, y0, x1, y1)
                        # 將 PDF 坐標轉換為像素坐標
                        dpi = 200  # 設置轉換時的 DPI
                        scale = dpi / 72  # PDF 坐標是 72 DPI
                        bbox_pixels = [int(coord * scale) for coord in bbox]
                        # 裁剪圖片
                        cropped_image = page_image.crop(bbox_pixels)
                        output_path = os.path.join(temp_image_dir, f"{os.path.splitext(os.path.basename(pdf_path))[0]}_table_page_{page_number}_table_{table_index}.png")
                        cropped_image.save(output_path, "PNG")
                        print(f"表格圖片已保存：{output_path}")
        table_paths = []
        for root, dirs, files in os.walk(temp_image_dir):
            for file in files:
                if file.lower().endswith('.png'):
                    # 檔案完整路徑
                    source_path = os.path.join(root, file)
                    prompt = "如果圖片內是一個表格，回答 'True'，否則回答 'False'。"
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