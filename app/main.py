# main.py
import os
import sys
import streamlit as st
from client.ui import render_header, input_form, render_output, check_api, call_api

# ========= Cấu hình môi trường =========
os.environ["TF_ENABLE_ONEDNN_OPTS"]    = "0"
os.environ["TRANSFORMERS_NO_TF"]       = "1"
os.environ["WANDB_DISABLED"]           = "true"
os.environ["KMP_DUPLICATE_LIB_OK"]     = "TRUE"
os.environ["TF_USE_LEGACY_KERAS"]      = "1"
os.environ["HF_HUB_DISABLE_XET"]       = "1"
os.environ['TF_CPP_MIN_LOG_LEVEL']     = '2'

# ========= Main =========
def main():
    # Header và config
    render_header()

    # Kiểm tra API và hiển thị cảnh báo nếu lỗi
    if not check_api():
        st.error("Không kết nối được tới FastAPI trên cổng 8000. Vui lòng kiểm tra server đang chạy.")
        return

    # Nhập liệu
    review_text = input_form()

    # Khi người dùng bấm nút
    if st.button("Phân tích"):
        if not review_text.strip():
            st.warning("Vui lòng nhập một câu review.")
        else:
            with st.spinner("Đang phân tích…"):
                raw_out, entries = call_api(review_text)
            # Hiển thị raw output và highlight
            render_output(raw_out, entries, review_text)


if __name__ == "__main__":
    main()
