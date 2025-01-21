import os
from dotenv import load_dotenv
from pdf import Pdf
from image import Image2table


if __name__ == "__main__":
    load_dotenv()
    claud_api_key = os.getenv("ANTHROPIC_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    pdf = Pdf(llm_name = "claude", api_key = claud_api_key)
    image_paths = pdf.extraction(pdf_path = "./input/Cathays Weekly View.pdf")
    image2table = Image2table(llm_name = "claude", api_key = claud_api_key)
    for image_path in image_paths:
        image2table.image_process(image_path=image_path)   
