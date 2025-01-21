import os
from dotenv import load_dotenv
from pdf import Pdf
from image import Image2table
import streamlit as st

# 加载环境变量
load_dotenv()

claude_api_key = os.getenv("ANTHROPIC_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")

# 创建文件夹
os.makedirs("./input/", exist_ok=True)

# 初始化 Streamlit 应用
st.title("PDF Extraction and Image Processing App")
st.write("Upload one or more PDF files, choose the AI model, and optionally provide a custom image detection prompt.")

# 用户选择处理器
model_choice = st.radio(
    "Select the AI model to process the files:",
    options=["Claude", "Gemini"],
    index=0  # 默认选中第一个
)

# 用户输入 image_detection_prompt
image_detection_prompt = st.text_area(
    "Optional: Provide a custom image detection prompt (leave blank for default):",
    value="",
    placeholder="Enter your custom prompt here..."
)

# 根据选择获取对应的 API 密钥
selected_api_key = claude_api_key if model_choice == "Claude" else gemini_api_key

# 文件上传
uploaded_files = st.file_uploader("Choose one or more PDF files", type="pdf", accept_multiple_files=True)

# 添加 "Run" 按钮
if uploaded_files:
    st.success("Files uploaded successfully! Now click 'Run' to start processing.")
    run_button = st.button("Run")

    if run_button:
        failed_files = []

        for uploaded_file in uploaded_files:
            try:
                # 保存上传的文件到本地
                temp_file_path = f"./input/{uploaded_file.name}"
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # 初始化 PDF 处理
                st.write(f"Initializing PDF processing for {uploaded_file.name} with {model_choice}...")
                pdf = Pdf(llm_name=model_choice.lower(), api_key=selected_api_key)

                # 提取 PDF 中的图片路径
                try:
                    image_paths = pdf.extraction(pdf_path=temp_file_path)
                    st.write(f"Images extracted from {uploaded_file.name}:")
                    st.write(image_paths)
                except Exception as e:
                    st.error(f"Error during PDF extraction for {uploaded_file.name}: {e}")
                    failed_files.append(uploaded_file.name)
                    continue

                # 初始化图像处理
                st.write(f"Processing extracted images from {uploaded_file.name} with {model_choice}...")
                image2table = Image2table(
                    llm_name=model_choice.lower(),
                    api_key=selected_api_key,
                    image_detection_prompt=image_detection_prompt
                )

                # 处理图片并显示进度
                progress_bar = st.progress(0)
                failed_images = []
                for i, image_path in enumerate(image_paths):
                    try:
                        result = image2table.image_process(image_path=image_path)
                        st.write(f"Processed image: {image_path}")
                        st.html(result)
                    except Exception as e:
                        failed_images.append(image_path)
                        st.error(f"Error processing image {image_path}: {e}")
                    progress_bar.progress((i + 1) / len(image_paths))

                if failed_images:
                    st.warning(f"The following images from {uploaded_file.name} failed to process:")
                    st.write(failed_images)

                # 清理临时文件
                os.remove(temp_file_path)

            except Exception as e:
                st.error(f"Error processing file {uploaded_file.name}: {e}")
                failed_files.append(uploaded_file.name)

        if failed_files:
            st.warning("The following files failed to process:")
            st.write(failed_files)

        st.write("Process ended!")
