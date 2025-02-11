# pdf_extraction_stage.py
import os
import streamlit as st
from .pdf import Pdf
from default.code import pdf_extraction_code
from default.prompt import image_detection_prompt
from .utils import record_prompt, get_records_by_stage

class PDFExtractionStage:
    def __init__(self, claude_api_key_env, gemini_api_key_env):
        self.claude_api_key_env = claude_api_key_env
        self.gemini_api_key_env = gemini_api_key_env

    def clear_previous_outputs(self):
        """
        刪除本 session 中先前產生的圖片與 HTML（只刪除本次流程的檔案，不會清空整個資料夾）。
        """
        # 刪除圖片
        for pdf_name, img_paths in st.session_state.get("extracted_images", {}).items():
            for img_path in img_paths:
                if os.path.exists(img_path):
                    os.remove(img_path)
        st.session_state["extracted_images"] = {}
        st.session_state["failed_files"] = []
        st.session_state["run_done"] = False

        # 刪除本 session 產生的 HTML（若有記錄）
        if "generated_html" in st.session_state:
            for html_file in st.session_state["generated_html"]:
                if os.path.exists(html_file):
                    os.remove(html_file)
            st.session_state["generated_html"] = []

    def display(self):
        
        st.subheader("第一階段：PDF 圖片擷取")
        
        # 讀取並依 like_count 由大到小排序（stage："表格圖片擷取"）
        records = get_records_by_stage("表格圖片擷取")
        records = sorted(records, key=lambda rec: rec.get("like_count", 1), reverse=True)
        if records:
            st.info("以下是已記錄的 Prompt（含喜歡次數），您可以從下方選擇並一鍵複製到輸入區：")
            actual_prompts = [record["prompt"] for record in records]
            display_prompts = [
                f"(喜歡 {record.get('like_count', 1)} 次) {record['prompt']} "
                for record in records
            ]
            selected_display = st.selectbox("請選擇一個已記錄的 Prompt", display_prompts, key="pdf_prompt_select")
            index = display_prompts.index(selected_display)
            selected_prompt = actual_prompts[index]
            if st.button("一鍵複製到輸入區", key="pdf_copy_prompt_button"):
                st.session_state["pdf_prompt_input"] = selected_prompt
                st.success("已複製到輸入區！")
        else:
            st.info("目前尚無記錄的 Prompt。")
        
        # 模型選擇與 API Key 輸入
        pdf_model_choice = st.radio(
            "Select the AI model for PDF extraction:",
            options=["Claude", "Gemini"],
            index=0,
            key="pdf_model_choice"
        )
        pdf_provide_custom_api_key = st.checkbox("為第一階段提供自定義 API Key", value=False, key="pdf_custom_checkbox")
        if pdf_provide_custom_api_key:
            pdf_api_key = st.text_input(
                f"請輸入 {pdf_model_choice} 的 API Key (第一階段):",
                type="password",
                placeholder=f"輸入 {pdf_model_choice} API Key",
                key="pdf_api_key_input"
            )
            if not pdf_api_key:
                st.warning("請輸入有效的 API Key (第一階段)，否則無法進行處理。")
        else:
            pdf_api_key = self.claude_api_key_env if pdf_model_choice == "Claude" else self.gemini_api_key_env
            if not pdf_api_key:
                st.warning(f"系統未檢測到 {pdf_model_choice} (第一階段) 的 API Key，請確認環境變數已正確設置。")
        
        st.subheader("上傳 PDF 進行第一階段的圖片擷取")
        uploaded_files = st.file_uploader("Choose one or more PDF files", type="pdf", accept_multiple_files=True, key="pdf_uploader")
        
        if uploaded_files:
            current_upload_names = [file.name for file in uploaded_files]
            if current_upload_names != st.session_state.get("previous_uploads", []):
                self.clear_previous_outputs()
                st.session_state["previous_uploads"] = current_upload_names
        
        with st.expander("請輸入自定義的 Python 程式碼來設計 capture_images 函數 (點此展開)", expanded=False):
            user_defined_code = st.text_area(
                "請輸入自定義的 Python 程式碼來設計 capture_images 函數:\n注意：請勿更動 Input、Output 以及函數名稱。",
                value=pdf_extraction_code,
                height=500,
                key="pdf_code_input"
            )
        if "pdf_prompt_input" not in st.session_state:
            st.session_state["pdf_prompt_input"] = image_detection_prompt
        user_defined_image_detection_prompt = st.text_area(
            "請輸入自定義的 prompt，這個 prompt 是用來檢查提取出來的圖片是否為表格。",
            value=st.session_state["pdf_prompt_input"],
            height=300,
            key="pdf_prompt_input"
        )
        run_button = st.button("Run (PDF 圖片擷取)", key="pdf_run_button")
        if run_button:
            if not pdf_api_key:
                st.error("第一階段的 API Key 不存在，請確認後再重新執行。")
            else:
                self.clear_previous_outputs()
                for uploaded_file in uploaded_files:
                    pdf_name = uploaded_file.name
                    try:
                        temp_file_path = f"./input/{pdf_name}"
                        with open(temp_file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        st.write(f"Initializing PDF processing for {pdf_name} with model: {pdf_model_choice}...")
                        
                        pdf = Pdf(llm_name=pdf_model_choice.lower(), api_key=pdf_api_key)
                        
                        capture_images = None
                        if user_defined_code.strip():
                            try:
                                exec(user_defined_code, globals())
                                st.success("成功載入自定義的程式碼。")
                            except Exception as e:
                                st.error(f"載入自定義程式碼失敗: {e}")
                                capture_images = None
                        
                        try:
                            image_paths = pdf.extraction(
                                pdf_path=temp_file_path,
                                capture_images=capture_images,
                                table_image_check_prompt=user_defined_image_detection_prompt
                            )
                            if image_paths:
                                st.write(f"Images extracted from {pdf_name}:")
                            else:
                                st.warning(f"No images extracted from {pdf_name}.")
                            st.session_state.setdefault("extracted_images", {})[pdf_name] = image_paths
                        except Exception as e:
                            st.error(f"Error during PDF extraction for {pdf_name}: {e}")
                            st.session_state.setdefault("failed_files", []).append(pdf_name)
                        try:
                            os.remove(temp_file_path)
                        except OSError:
                            pass
                    except Exception as e:
                        st.error(f"Error processing file {pdf_name}: {e}")
                        st.session_state.setdefault("failed_files", []).append(pdf_name)
                st.session_state["run_done"] = True
                st.success("PDF extraction completed. Now you can proceed to process images.")
        
        if st.session_state.get("extracted_images"):
            st.write("---")
            st.subheader("提取出的圖片 (第一階段結果)")
            for pdf_name, image_paths in st.session_state["extracted_images"].items():
                if image_paths:
                    st.write(f"From PDF: {pdf_name}")
                    for image_path in image_paths:
                        st.image(image_path, caption=f"Extracted Image: {os.path.basename(image_path)}", use_container_width=True)
                else:
                    st.write(f"From PDF: {pdf_name} - No images extracted.")
            
            if st.button("我對於表格圖片擷取的結果滿意", key="satisfied_image_extraction"):
                record_prompt("表格圖片擷取", st.session_state["pdf_prompt_input"])
                st.success("已記錄滿意的 prompt！")
