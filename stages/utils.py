# utils.py
import os
import json
from datetime import datetime

def record_prompt(stage_label, prompt_text):
    """
    嘗試記錄指定階段的 prompt。如果該 prompt 已存在，則將其 like_count 增加 1；
    否則建立新的記錄並將 like_count 設為 1。
    回傳 True 表示成功記錄或更新 like_count。
    """
    record_file = "prompt_records.json"
    if os.path.exists(record_file):
        with open(record_file, "r", encoding="utf8") as f:
            try:
                records = json.load(f)
            except json.JSONDecodeError:
                records = []
    else:
        records = []

    prompt_exists = False
    for rec in records:
        if rec.get("prompt") == prompt_text and rec.get("stage") == stage_label:
            rec["like_count"] = rec.get("like_count", 1) + 1
            prompt_exists = True
            break

    if not prompt_exists:
        new_record = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage_label,
            "prompt": prompt_text,
            "like_count": 1,
        }
        records.append(new_record)

    with open(record_file, "w", encoding="utf8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    return True

def get_records_by_stage(stage_label):
    """
    讀取 JSON 檔案並回傳指定階段的所有 prompt 紀錄。
    """
    record_file = "prompt_records.json"
    if not os.path.exists(record_file):
        return []
    with open(record_file, "r", encoding="utf8") as f:
        try:
            records = json.load(f)
        except json.JSONDecodeError:
            records = []
    return [rec for rec in records if rec.get("stage") == stage_label]
