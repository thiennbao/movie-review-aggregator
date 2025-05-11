# ui.py
import requests
import streamlit as st
import re
from typing import List, Dict, Tuple

API_URL = "http://localhost:8000/predict"

# Mapping polarity to icon và màu nền
POLARITY_ICON = {
    'positive': '😊',
    'neutral': '😐',
    'negative': '☹️'
}
COLOR_LIST = ['#FFECB3', '#C8E6C9', '#BBDEFB', '#F8BBD0', '#D1C4E9']


def check_api() -> bool:
    """Kiểm tra healthcheck của FastAPI"""
    try:
        r = requests.get(API_URL.replace('/predict','/'))
        return r.status_code == 200
    except requests.RequestException:
        return False


def call_api(review_text: str) -> Tuple[str, List[Dict[str, Tuple[str, Tuple[int,int]]]]]:
    """Gọi API và trả về raw_output cùng list entries chứa aspect, polarity và position"""
    payload = {"review": review_text}
    resp = requests.post(API_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    raw = data.get("raw_output", "")
    entries = []
    for item in data.get('results', []):
        for asp, pol, pos in zip(item['aspects'], item['polarities'], item['positions']):
            entries.append({'aspect': asp, 'polarity': pol, 'position': pos})
    return raw, entries


def render_header():
    """Thiết lập tiêu đề và cấu hình trang"""
    st.set_page_config(page_title="InstructABSA Demo", layout="centered")
    st.title("📝 InstructABSA")
    st.markdown("Nhập review dưới đây, nhấn **Phân tích** để highlight các aspect terms và hiển thị sentiment icon.")


def input_form() -> str:
    """Nhận câu review từ người dùng"""
    return st.text_area("Review:", height=150, placeholder="Nhập một câu đánh giá...")


def render_output(raw_output: str, entries: List[Dict], review_text: str):
    """Hiển thị raw_output và câu review với highlight + icon sentiment"""
    # Kết quả thô
    st.subheader("Kết quả thô:")
    st.code(raw_output)

    # Highlight review
    st.subheader("Review với highlights:")
    highlighted = review_text
    # Map mỗi aspect sang màu
    color_map = {}
    for idx, e in enumerate(entries):
        asp = e['aspect']
        if asp not in color_map:
            color_map[asp] = COLOR_LIST[idx % len(COLOR_LIST)]

    # Sắp xếp để tránh ghi đè lẫn nhau
    for e in sorted(entries, key=lambda x: len(x['aspect']), reverse=True):
        asp = e['aspect']
        pol = e['polarity']
        color = color_map[asp]
        icon = POLARITY_ICON.get(pol, '')
        span = (
            f"<span style='background-color:{color}; padding:2px; border-radius:4px;' "
            f"title='{pol} {icon}'>{asp} <sup>{icon}</sup></span>"
        )
        # Replace với regex để insensitive và chính xác
        highlighted = re.sub(re.escape(asp), span, highlighted, flags=re.IGNORECASE)

    st.markdown(highlighted, unsafe_allow_html=True)
