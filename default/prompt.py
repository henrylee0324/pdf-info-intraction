image_detection_prompt = "如果圖片內是一個完整的表格，回答 'True'，否則回答 'False'。"
table_extraction_prompt = """
請先依照附件中的表格圖片，保留原先的表格階層。
若同一儲存格有多行文字，請將這些文字合併為該儲存格的內容（不要拆分到不同儲存格）。
無需解讀或分析內容，只需確實地保留所有文字與排版層次。
完成後，請使用轉錄所得的內容，依照表格的原始階層重新生成一個 HTML 表格，
並確保結構、文字、以及任何跨列或跨行（colspan、rowspan）都與原圖一致。
    """.strip()