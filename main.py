# main.py
import os
from dotenv import load_dotenv
import streamlit as st
from stages.pdfextractionstage import PDFExtractionStage
from stages.imageprocessingstage import ImageProcessingStage

load_dotenv()
claude_api_key_env = os.getenv("ANTHROPIC_API_KEY")
gemini_api_key_env = os.getenv("GEMINI_API_KEY")

# 確保必要資料夾存在（不會全域清空，以免影響其他使用者）
os.makedirs("./input/", exist_ok=True)
os.makedirs("./output_html", exist_ok=True)
os.makedirs("./output_images", exist_ok=True)

# 初始化 Streamlit session_state（每個使用者自己的 session_state）
if "extracted_images" not in st.session_state:
    st.session_state["extracted_images"] = {}
if "failed_files" not in st.session_state:
    st.session_state["failed_files"] = []
if "run_done" not in st.session_state:
    st.session_state["run_done"] = False
if "previous_uploads" not in st.session_state:
    st.session_state["previous_uploads"] = []
if "stage1_prompt_recorded" not in st.session_state:
    st.session_state["stage1_prompt_recorded"] = False
if "stage2_prompt_recorded" not in st.session_state:
    st.session_state["stage2_prompt_recorded"] = False
if "generated_html" not in st.session_state:
    st.session_state["generated_html"] = []  # 記錄本 session 產生的 HTML 檔案

st.title("PDF Extraction and Image Processing App")
st.write("Upload one or more PDF files, **choose the AI model for each stage**, and optionally provide a custom image detection prompt.")

pdf_stage = PDFExtractionStage(claude_api_key_env, gemini_api_key_env)
pdf_stage.display()

image_stage = ImageProcessingStage(claude_api_key_env, gemini_api_key_env)
image_stage.display()
