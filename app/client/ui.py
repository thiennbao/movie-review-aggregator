# ui.py
import requests  # Thư viện HTTP cho API calls
import streamlit as st  # Thư viện Streamlit cho UI
import re  # Xử lý regex
from typing import List, Dict, Tuple
from html import escape  # Escape HTML để tránh XSS

# ========= Cấu hình endpoint =========
BASE_URL = "http://localhost:8000"
PREDICT_URL = f"{BASE_URL}/predict"  # Endpoint dự đoán
HEALTH_URL = f"{BASE_URL}/"         # Endpoint health-check

# Cấu hình màu và icon theo polarity
POLARITY_SETTINGS = {
    'positive': {'icon': '😊', 'color': '#C8E6C9'},  # xanh lá
    'neutral':  {'icon': '😐', 'color': '#FFECB3'},  # vàng
    'negative': {'icon': '☹️', 'color': '#FFCDD2'}   # đỏ
}
# Palette màu cho câu (sentence-level), không trùng với màu polarity
SENTENCE_COLORS = ['#B3E5FC', '#B2EBF2', '#E1BEE7', '#D7CCC8', '#F5F5F5']


def check_api() -> bool:
    """Kiểm tra kết nối đến FastAPI"""
    try:
        response = requests.get(HEALTH_URL, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def call_api(review_text: str) -> Tuple[str, List[Dict[str, Tuple[int, int]]]]:
    """Gửi review đến API, nhận raw_output và danh sách entries"""
    payload = {"review": review_text}
    try:
        resp = requests.post(PREDICT_URL, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        st.error(f"Lỗi khi gọi API: {e}")
        return "", []

    raw_output = data.get("raw_output", "")
    entries = []
    for item in data.get('results', []):
        aspects = item.get('aspects', [])
        polarities = item.get('polarities', [])
        positions = item.get('positions', [])
        for asp, pol, pos in zip(aspects, polarities, positions):
            entries.append({'aspect': asp, 'polarity': pol, 'position': tuple(pos)})
    return raw_output, entries


def render_header():
    """Hiển thị tiêu đề và cấu hình trang"""
    st.set_page_config(page_title="InstructABSA Demo", layout="centered")
    st.title("📝 InstructABSA Demo")
    st.markdown("Nhập review và nhấn **Phân tích** để xem kết quả highlight và sentiment.")


def input_form() -> str:
    """Nhận input review từ người dùng"""
    return st.text_area("Review", height=150, placeholder="Nhập câu đánh giá...")


def render_output(raw_output: str, entries: List[Dict[str, Tuple[int, int]]], review_text: str):
    """Hiển thị raw_output và highlight review"""
    # Hiển thị raw_output
    st.subheader("Kết quả thô:")
    st.code(raw_output)

    # Highlight review
    st.subheader("Review với highlights:")
    text = escape(review_text)

    # Tách câu (còn giữ nguyên cách thể hiện liên tục)
    sentence_re = re.compile(r'([^.!?]+[.!?]?)')
    sentences = [s for s in sentence_re.findall(text) if s.strip()]

    parts = []
    for idx, sentence in enumerate(sentences):
        # Kiểm tra entry trong câu
        matches = [e for e in entries if sentence.lower().find(escape(e['aspect']).lower()) >= 0]
        if not matches:
            # Không highlight nếu không có aspect
            parts.append(sentence)
            continue

        # Highlight aspect tại vị trí
        segs, last = [], 0
        matches = sorted(matches, key=lambda x: x['position'][0])
        for e in matches:
            start, end = e['position']
            if start < 0 or end <= start:
                continue
            # Thêm đoạn trước aspect
            segs.append(sentence[last:start])
            # Span highlight cho aspect
            pol_conf = POLARITY_SETTINGS.get(e['polarity'], {})
            color = pol_conf.get('color', '#FFFFFF')
            icon = pol_conf.get('icon', '')
            segs.append(
                f"<span style='background-color:{color}; padding:2px; border-radius:4px; cursor:help;'"
                f" title='{e['polarity']}'>"
                f"{sentence[start:end]} <sup>{icon}</sup></span>"
            )
            last = end
        segs.append(sentence[last:])
        highlighted = "".join(segs)

        # Wrap câu đã highlight với màu sentence-level
        sent_color = SENTENCE_COLORS[idx % len(SENTENCE_COLORS)]
        parts.append(
            f"<span style='background-color:{sent_color}; padding:2px; border-radius:4px;'>"
            f"{highlighted}</span>"
        )

    # Kết hợp thành một đoạn văn liền mạch
    html = "".join(parts)
    st.markdown(html, unsafe_allow_html=True)
