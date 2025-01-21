import os
from dotenv import load_dotenv  
from llm.claude import CLAUDE
from llm.gemini import GEMINI

class Image2table:
    def __init__(self, llm_name, api_key, image_detection_prompt = ""):
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
        if image_detection_prompt == "":
            self.image_detection_prompt = """請先依照附件中的表格圖片，保留原先的表格階層。 
            若同一儲存格有多行文字，請將這些文字合併為該儲存格的內容（不要拆分到不同儲存格）。 
            無需解讀或分析內容，只需確實地保留所有文字與排版層次。 
            完成後，請使用轉錄所得的內容，依照表格的原始階層重新生成一個 HTML 表格，並確保結構、文字、以及任何跨列或跨行（colspan、rowspan）都與原圖一致。
            """
        else:
            self.image_detection_prompt = image_detection_prompt
        self.table_check_prompt = """閱讀這個 html 格式的表格。這個表格可能排版已經亂掉了。
        如果你認為他的排版是正確的，回應與原先一樣的 html 格式表格。
        若他的排版是錯誤的，請替我修正格式後再重新回應一個新的 html 格式表格。
        請注意不要隨意刪除儲存格內容。
        """
    def image_process(self, image_path, html_dir = ""):
        if html_dir == "":
            html_dir = "./html"
        os.makedirs(html_dir, exist_ok=True)
        html_path = f"{html_dir}/{os.path.splitext(os.path.basename(image_path))[0]}.html"
        res = self.llm.generate(prompt=self.image_detection_prompt, image_path = image_path)
        if res:
            # Save the HTML content to a file
            with open(html_path, "w", encoding="utf-8") as file:
                file.write(res)
            print(f"HTML table has been saved to {html_path}")
        else:
            print("Failed to generate the HTML content.") 
        os.remove(image_path)
        return html_path



if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    image2table = Image2table(llm_name = "claude", api_key = api_key)
    image2table.image_process(image_path="./table_images/table_page_5_table_1.png")    