# main.py
import os
import sys
import streamlit as st
import requests

# ========= Cấu hình môi trường =========
os.environ["TF_ENABLE_ONEDNN_OPTS"]    = "0"
os.environ["TRANSFORMERS_NO_TF"]       = "1"
os.environ["WANDB_DISABLED"]           = "true"
os.environ["KMP_DUPLICATE_LIB_OK"]     = "TRUE"
os.environ["TF_USE_LEGACY_KERAS"]      = "1"
os.environ["HF_HUB_DISABLE_XET"]       = "1"
os.environ['TF_CPP_MIN_LOG_LEVEL']     = '2'

# Nếu bạn để main.py ở client/, không cần chỉnh sys.path
# sys.path.insert(0, os.path.dirname(__file__))

from client.ui import render_header, input_form, render_output

# ========= Thông số kết nối API =========
API_ROOT = "http://localhost:8000"
PREDICT_ENDPOINT = f"{API_ROOT}/predict"

def check_api():
    """Kiểm tra healthcheck của FastAPI."""
    try:
        r = requests.get(API_ROOT + "/")
        return r.status_code == 200
    except requests.RequestException:
        return False

def call_api(review_text: str) -> tuple[str, list[tuple[str,str]]]:
    """Gửi review lên FastAPI và trả về raw_output + danh sách pairs."""
    payload = {"review": review_text}
    try:
        resp = requests.post(PREDICT_ENDPOINT, json=payload, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        st.error(f"Lỗi khi gọi API: {e}")
        st.stop()

    data = resp.json()
    raw = data.get("raw_output", "")
    # results: [{ "aspect": "...", "polarity": "..." }, ...]
    pairs = [(item["aspect"], item["polarity"]) for item in data.get("results", [])]
    return raw, pairs

def main():
    # (1) Header
    render_header()

    # (2) Kiểm tra API
    if not check_api():
        st.error("Không kết nối được tới FastAPI trên cổng 8000. Vui lòng kiểm tra server đang chạy.")
        return

    # (3) Input form
    review_text = input_form()

    # (4) Khi người dùng bấm nút
    if st.button("Phân tích"):
        if not review_text.strip():
            st.warning("Vui lòng nhập một câu review.")
        else:
            with st.spinner("Đang phân tích…"):
                raw_out, pairs = call_api(review_text)
            render_output(raw_out, pairs)

if __name__ == "__main__":
    main()
