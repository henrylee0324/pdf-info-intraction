import os
import base64
from dotenv import load_dotenv
import anthropic
import PIL.Image
from llm.llm import LLM

class CLAUDE(LLM):      
    def generate(self, prompt="", image_path=None, model_name="claude-3-5-sonnet-20241022"):
        client = anthropic.Client(
            api_key=self.api_key,
        )

        messages = []

        if image_path:
            with open(image_path, "rb") as image_file:
                image = base64.b64encode(image_file.read()).decode("utf-8")
                messages.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image,
                    },
                })
        messages.append({
            "type": "text",
            "text": prompt
        })
        try:
            response = client.messages.create(
                model=model_name,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": messages,
                    }
                ]
            )
            print(response.content)
            extracted_text = "".join(block.text for block in response.content if hasattr(block, "text"))
            return extracted_text
        except Exception as e:
            print(f"Error: {e}")
        

if __name__ == "__main__":
    load_dotenv()
    claude = CLAUDE(os.getenv("ANTHROPIC_API_KEY"))
    prompt = """請先依照附件中的表格圖片，保留原先的表格階層。 
    若同一儲存格有多行文字，請將這些文字合併為該儲存格的內容（不要拆分到不同儲存格）。 
    無需解讀或分析內容，只需確實地保留所有文字與排版層次。 
    完成後，請使用轉錄所得的內容，依照表格的原始階層重新生成一個 HTML 表格，並確保結構、文字、以及任何跨列或跨行（colspan、rowspan）都與原圖一致。
    """
    res = claude.generate(prompt=prompt, image_path="./image/test3.png")
    if res:
        # Save the HTML content to a file
        output_file = "test.html"
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(res)
        print(f"HTML table has been saved to {output_file}")
    else:
        print("Failed to generate the HTML content.")
    
 

    
