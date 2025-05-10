# ui.py
import streamlit as st

def render_header():
    st.set_page_config(page_title="InstructABSA Demo", layout="centered")
    st.title("📝 InstructABSA")
    st.markdown(
        "Nhập review dưới đây, nhấn **Phân tích** để nhận các cặp `aspect: polarity`."
    )

def input_form():
    """Trả về câu review do user nhập."""
    return st.text_area("Review:", height=150, placeholder="Nhập một câu đánh giá...")

def render_output(raw_output: str, pairs: list[tuple[str,str]]):
    st.subheader("Kết quả thô:")
    st.code(raw_output)
    st.subheader("Các cặp Aspect–Polarity:")
    if not pairs:
        st.info("Không tìm thấy cặp nào.")
    else:
        for asp, pol in pairs:
            st.markdown(f"- **{asp}** → *{pol}*")
