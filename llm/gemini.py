import PIL.Image
import os
import google.generativeai as genai
from dotenv import load_dotenv
from llm.llm import LLM

class GEMINI(LLM):
    def __init__(self, api_key):
        super().__init__(api_key)
        genai.configure(api_key = self.api_key)
    def generate(self, prompt = "", image_path = None, model_name = "gemini-1.5-pro-002"):
        message = [prompt]
        if image_path:
            image = PIL.Image.open(image_path)
            message.append(image)
        else:
            image = None        
        model = genai.GenerativeModel(model_name=model_name)
        try:
            response = model.generate_content(message)
            print(f"response: {response.text}")
            return(response.text)
        except Exception as e:
            print(f"Error: {e}")

    
if __name__ == "__main__":
    load_dotenv()
    gemini = GEMINI(os.getenv("GEMINI_API_KEY"))
    prompt = """請先依照附件中的表格圖片，保留原先的表格階層。 
    若同一儲存格有多行文字，請將這些文字合併為該儲存格的內容（不要拆分到不同儲存格）。 
    無需解讀或分析內容，只需確實地保留所有文字與排版層次。 
    完成後，請使用轉錄所得的內容，依照表格的原始階層重新生成一個 HTML 表格，並確保結構、文字、以及任何跨列或跨行（colspan、rowspan）都與原圖一致。
    """
    res = gemini.generate(prompt=prompt, image_path="./image/test3.png")
    if res:
        # Save the HTML content to a file
        output_file = "test.html"
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(res)
        print(f"HTML table has been saved to {output_file}")
    else:
        print("Failed to generate the HTML content.")    
 
    