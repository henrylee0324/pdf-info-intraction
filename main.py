import os
from dotenv import load_dotenv
import streamlit as st
from pdf import Pdf
from image import Image2table
from datetime import datetime


# 1. 載入環境變數
load_dotenv()
claude_api_key = os.getenv("ANTHROPIC_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")

# 2. 確保 ./input/ 目錄存在
os.makedirs("./input/", exist_ok=True)

# 3. 初始化 session_state
if "extracted_images" not in st.session_state:
    st.session_state.extracted_images = {}  # 用於存儲每個 PDF 提取出的圖片路徑
if "failed_files" not in st.session_state:
    st.session_state.failed_files = []
if "run_done" not in st.session_state:
    st.session_state.run_done = False

# 4. Streamlit 介面
st.title("PDF Extraction and Image Processing App")
st.write("Upload one or more PDF files, choose the AI model, and optionally provide a custom image detection prompt.")

# 5. 模型選擇
model_choice = st.radio(
    "Select the AI model to process the files:",
    options=["Claude", "Gemini"],
    index=0  # 預設選擇第一個
)

# 6. 根據模型選擇取得對應的 API Key
st.subheader("API Key 選擇")
provide_custom_api_key = st.checkbox("提供自定義 API Key", value=False)

if provide_custom_api_key:
    selected_api_key = st.text_input(
        f"請輸入 {model_choice} 的 API Key:",
        type="password",
        placeholder=f"輸入 {model_choice} API Key"
    )
    if not selected_api_key:
        st.warning("請輸入有效的 API Key，否則無法進行處理。")
else:
    selected_api_key = claude_api_key if model_choice == "Claude" else gemini_api_key
    if not selected_api_key:
        st.warning(f"系統未檢測到 {model_choice} 的 API Key，請確認環境變數已正確設置。")


# 7. PDF 文件上傳
uploaded_files = st.file_uploader("Choose one or more PDF files", type="pdf", accept_multiple_files=True)

# 第一階段：按下「Run」提取 PDF 中的圖片，存到 session_state
if uploaded_files:
    default_code = """
import fitz  # PyMuPDF
from pdf2docx_custom import Converter


def capture_images(pdf_path, output_dir="temp_images"):
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
        """
    user_defined_code = st.text_area(
        "請輸入自定義的 Python 程式碼來設計 capture_images 函數:\n"
        "注意：請勿更動Input、Output以及函數名稱。",
        value = default_code,
        placeholder="輸入您的 Python 程式碼...",
        height = 800
        )
    default_image_detection_prompt = """如果圖片內是一個完整的表格，回答 'True'，否則回答 'False'。"""
    user_defined_image_detection_prompt = st.text_area(
        "請輸入自定義的 prompt，這個 prompt 是用來檢查節取出來的圖片是否為表格。",
        value = default_image_detection_prompt,
        placeholder="輸入您的 prompt",
        height = 300
        )
    run_button = st.button("Run")


    if run_button:
        # 清空先前的結果，重新開始
        st.session_state.extracted_images.clear()
        st.session_state.failed_files.clear()
        st.session_state.run_done = False

        # 開始處理每個上傳 PDF
        for uploaded_file in uploaded_files:
            pdf_name = uploaded_file.name
            try:
                # 儲存 PDF 到本地
                temp_file_path = f"./input/{pdf_name}"
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                st.write(f"Initializing PDF processing for {pdf_name} with {model_choice}...")

                # 創建 PDF 物件
                pdf = Pdf(llm_name=model_choice.lower(), api_key=selected_api_key)
                # 提供一個輸入框讓用戶輸入自定義的程式碼

                # 驗證用戶是否已提供自定義程式碼
                if user_defined_code.strip():
                    try:
                        # 執行用戶輸入的程式碼
                        exec(user_defined_code, globals())
                        st.success("成功載入自定義的程式碼。")
                    except Exception as e:
                        st.error(f"載入自定義程式碼失敗: {e}")
                        capture_images = None
                else:
                    capture_images = None  
                try:
                    # 提取圖片
                    image_paths = pdf.extraction(pdf_path=temp_file_path, capture_images = capture_images, table_image_check_prompt=user_defined_image_detection_prompt)
                    if image_paths:
                        st.write(f"Images extracted from {pdf_name}:")
                    else:
                        st.warning(f"No images extracted from {pdf_name}.")
                    st.session_state.extracted_images[pdf_name] = image_paths
                except Exception as e:
                    st.error(f"Error during PDF extraction for {pdf_name}: {e}")
                    st.session_state.failed_files.append(pdf_name)

                os.remove(temp_file_path)  # 移除暫存的 PDF
            except Exception as e:
                st.error(f"Error processing file {pdf_name}: {e}")
                st.session_state.failed_files.append(pdf_name)

        st.session_state.run_done = True
        st.success("PDF extraction completed. Now you can proceed to process images.")

# 顯示提取的圖片（無論是否按下處理按鈕）
if len(st.session_state.extracted_images) > 0:
    st.write("Extracted Images:")
    for pdf_name, image_paths in st.session_state.extracted_images.items():
        st.write(f"From PDF: {pdf_name}")
        for image_path in image_paths:
            st.image(image_path, caption=f"Extracted Image: {os.path.basename(image_path)}", use_container_width=True)

# 第二階段：按下「Process Extracted Images」進行圖片處理
if st.session_state.run_done and len(st.session_state.extracted_images) > 0:
    default_prompt = """
請先依照附件中的表格圖片，保留原先的表格階層。
若同一儲存格有多行文字，請將這些文字合併為該儲存格的內容（不要拆分到不同儲存格）。
無需解讀或分析內容，只需確實地保留所有文字與排版層次。
完成後，請使用轉錄所得的內容，依照表格的原始階層重新生成一個 HTML 表格，
並確保結構、文字、以及任何跨列或跨行（colspan、rowspan）都與原圖一致。"""

    image_detection_prompt = st.text_area(
        "可選: 在此輸入從圖片中提取表格的 prompt:\n"
        "注意: 輸入在此的 prompt 並不會被保存，請自行複製一份保留在電腦上。",
        value=default_prompt,
        placeholder="Enter your custom prompt here...",
        height= 300
    )

    process_images_button = st.button("Process Extracted Images")

    if process_images_button:
        st.write(f"Processing images with model: {model_choice} ...")

        image2table = Image2table(
            llm_name=model_choice.lower(),
            api_key=selected_api_key,
            image_detection_prompt=image_detection_prompt
        )

        failed_images = []
        total_images = sum(len(paths) for paths in st.session_state.extracted_images.values())
        processed_count = 0

        for pdf_name, image_paths in st.session_state.extracted_images.items():
            st.write(f"Processing images extracted from: {pdf_name}")
            for image_path in image_paths:
                try:
                    result = image2table.image_process(image_path=image_path)
                    st.write(f"Processed image: {image_path}")
                    st.html(result)
                except Exception as e:
                    failed_images.append(image_path)
                    st.error(f"Error processing image {image_path}: {e}")

                processed_count += 1
                st.progress(processed_count / total_images)

        if failed_images:
            st.warning("The following images failed to process:")
            st.write(failed_images)

        if st.session_state.failed_files:
            st.warning("The following PDF files failed to extract or process:")
            st.write(st.session_state.failed_files)

        st.write("Process ended!")
