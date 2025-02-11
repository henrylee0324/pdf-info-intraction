# image_processing_stage.py
import os
import streamlit as st
from default.prompt import table_extraction_prompt
from .image import Image2table
from .utils import record_prompt, get_records_by_stage

class ImageProcessingStage:
    def __init__(self, claude_api_key_env, gemini_api_key_env):
        self.claude_api_key_env = claude_api_key_env
        self.gemini_api_key_env = gemini_api_key_env

    def clear_previous_html(self):
        """
        只清除本 session 中先前生成的 HTML 檔案。
        """
        if "generated_html" in st.session_state:
            for html_file in st.session_state["generated_html"]:
                if os.path.exists(html_file):
                    os.remove(html_file)
            st.session_state["generated_html"] = []
        else:
            st.session_state["generated_html"] = []

    def display(self):
        if st.session_state.get("run_done") and st.session_state.get("extracted_images"):
            st.write("---")
            st.subheader("第二階段：圖片處理")
            
            # 重新執行前清除本 session 產生的 HTML
            self.clear_previous_html()
            print("clear html")

            # 讀取並依 like_count 由大到小排序（stage："表格內容擷取"）
            records = get_records_by_stage("表格內容擷取")
            records = sorted(records, key=lambda rec: rec.get("like_count", 1), reverse=True)
            if records:
                st.info("以下是已記錄的 Prompt（含喜歡次數），您可以從下方選擇並一鍵複製到輸入區：")
                actual_prompts = [record["prompt"] for record in records]
                display_prompts = [
                    f"(喜歡 {record.get('like_count', 1)} 次 {record['prompt']} )"
                    for record in records
                ]
                selected_display = st.selectbox("請選擇一個已記錄的 Prompt", display_prompts, key="image_prompt_select")
                index = display_prompts.index(selected_display)
                selected_prompt = actual_prompts[index]
                if st.button("一鍵複製到輸入區", key="image_copy_prompt_button"):
                    st.session_state["image_prompt_input"] = selected_prompt
                    st.success("已複製到輸入區！")
            else:
                st.info("目前尚無記錄的 Prompt。")
            
            if "image_prompt_input" not in st.session_state:
                st.session_state["image_prompt_input"] = table_extraction_prompt
            image_processing_prompt = st.text_area(
                "可選: 在此輸入從圖片中提取表格的 prompt (第二階段):",
                value=st.session_state["image_prompt_input"],
                height=300,
                key="image_prompt_input"
            )
            
            process_images_button = st.button("Process Extracted Images (第二階段)", key="image_run_button")
            
            image_api_key = None
            image_provide_custom_api_key = st.checkbox("為第二階段提供自定義 API Key", value=False, key="image_custom_checkbox")
            if image_provide_custom_api_key:
                image_api_key = st.text_input(
                    f"請輸入 {st.session_state.get('image_model_choice', 'Claude')} 的 API Key (第二階段):",
                    type="password",
                    placeholder="輸入 API Key",
                    key="image_api_key_input"
                )
                if not image_api_key:
                    st.warning("請輸入有效的 API Key (第二階段)，否則無法進行處理。")
            else:
                image_model_choice = st.radio(
                    "Select the AI model for image processing:",
                    options=["Claude", "Gemini"],
                    index=0,
                    key="image_model_choice"
                )
                image_api_key = self.claude_api_key_env if image_model_choice == "Claude" else self.gemini_api_key_env
                if not image_api_key:
                    st.warning(f"系統未檢測到 {image_model_choice} (第二階段) 的 API Key，請確認環境變數已正確設置。")
            
            if process_images_button:
                if not image_api_key:
                    st.error("第二階段的 API Key 不存在，請確認後再重新執行。")
                else:
                    self.clear_previous_html()
                    st.write(f"Processing images with model: {st.session_state.get('image_model_choice', 'Claude')} ...")
                    image2table = Image2table(
                        llm_name=st.session_state.get("image_model_choice", "claude").lower(),
                        api_key=image_api_key,
                        image_detection_prompt=image_processing_prompt
                    )
                    failed_images = []
                    total_images = sum(len(paths) for paths in st.session_state["extracted_images"].values())
                    processed_count = 0
                    for pdf_name, image_paths in st.session_state["extracted_images"].items():
                        if not image_paths:
                            continue
                        st.write(f"Processing images extracted from: {pdf_name}")
                        for image_path in image_paths:
                            col1, col2 = st.columns(2)
                            with col1:
                                st.image(image_path, caption=f"Extracted Image: {os.path.basename(image_path)}", use_container_width=True)
                            with col2:
                                try:
                                    result = image2table.image_process(image_path=image_path)
                                    st.write("Extracted Table:")
                                    st.html(result)
                                    # 若 image2table.image_process 產生 HTML 檔案，請將檔案路徑記錄至 st.session_state["generated_html"]
                                    # 例如：
                                    # html_path = save_html_result(result)
                                    # st.session_state.setdefault("generated_html", []).append(html_path)
                                except Exception as e:
                                    failed_images.append(image_path)
                                    st.error(f"Error processing image {image_path}: {e}")
                            processed_count += 1
                            st.progress(processed_count / total_images)
                    if failed_images:
                        st.warning("The following images failed to process:")
                        st.write(failed_images)
                    if st.session_state.get("failed_files"):
                        st.warning("The following PDF files failed to extract or process:")
                        st.write(st.session_state["failed_files"])
                    st.write("Process ended!")
            
            if st.button("我對於表格內容擷取的結果滿意", key="satisfied_content_extraction"):
                record_prompt("表格內容擷取", st.session_state["image_prompt_input"])
                st.success("已記錄滿意的 prompt！")
