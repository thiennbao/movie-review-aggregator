import pandas as pd
from langdetect import detect, LangDetectException
import emoji
import re
import os

def is_english(text: str) -> bool:
    """Kiểm tra xem văn bản có phải là tiếng Anh không."""
    try:
        # Đảm bảo text là string và không rỗng để langdetect hoạt động tốt nhất
        if not isinstance(text, str) or not text.strip():
            return False
        return detect(text) == 'en'
    except LangDetectException:
        # Xảy ra khi langdetect không thể xác định ngôn ngữ (ví dụ: text quá ngắn, chỉ có số/ký tự đặc biệt)
        return False
    except Exception as e:
        # Các lỗi không mong muốn khác từ langdetect
        # print(f"Warning: langdetect error for text '{text[:30]}...': {e}") # Bỏ comment để debug nếu cần
        return False

def contains_invalid_chars_or_icons(text: str) -> bool:
    """
    Kiểm tra xem văn bản có chứa emoji hoặc các ký tự "không hợp lệ" khác không.
    "Không hợp lệ" ở đây được hiểu là các ký tự không thường xuất hiện trong văn bản tiếng Anh chuẩn,
    sau khi đã nới lỏng để chấp nhận một số ký tự phổ biến từ bước chẩn đoán.
    """
    if not isinstance(text, str):
        return True # Coi như không hợp lệ nếu không phải string

    # 1. Kiểm tra emoji
    if emoji.emoji_count(text) > 0:
        return True

    # 2. Kiểm tra các ký tự không mong muốn bằng regex đã được nới lỏng
    
    pattern = r"[^a-zA-Z0-9\s\.,!?'\":;\-\(\)\[\]%&\$#@\*\+\=/<>’‘“”àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸ…–—_«»]"
    
    if re.search(pattern, text):
        # Để debug những ký tự nào vẫn bị lọc, bạn có thể bật dòng print dưới đây khi cần
        # print(f"DEBUG: Char filter found '{re.search(pattern, text).group(0)}' in: '{text[:70]}...'")
        return True

    return False

def preprocess_csv(input_filepath: str, output_filepath: str):
    """
    Tiền xử lý file CSV: loại bỏ dòng không phải tiếng Anh và dòng chứa icon/ký tự không hợp lệ.
    """
    if not os.path.exists(input_filepath):
        print(f"Lỗi: File đầu vào '{input_filepath}' không tồn tại.")
        return

    print(f"\nĐang xử lý file: {input_filepath}...")
    try:
        # Nên chỉ định dtype cho cột sentenceId nếu nó luôn là số nguyên hoặc luôn là chuỗi
        df = pd.read_csv(input_filepath, dtype={'sentenceId': str})
    except Exception as e:
        print(f"Lỗi khi đọc file CSV '{input_filepath}': {e}")
        return

    initial_row_count = len(df)
    print(f"Số dòng ban đầu: {initial_row_count}")
    
    # Bước 1: Lọc ngôn ngữ
    # Đảm bảo 'raw_text' là string, xử lý NaN bằng cách chuyển thành string rỗng để is_english xử lý
    df_filtered = df[df['raw_text'].fillna('').astype(str).apply(is_english)].copy()
    rows_after_lang_filter = len(df_filtered)
    print(f"Số dòng sau khi lọc ngôn ngữ (chỉ giữ tiếng Anh): {rows_after_lang_filter} (Đã loại bỏ: {initial_row_count - rows_after_lang_filter})")

    # Bước 2: Lọc icon/ký tự không hợp lệ (trên tập đã lọc ngôn ngữ)
    if not df_filtered.empty:
        df_filtered = df_filtered[~df_filtered['raw_text'].fillna('').astype(str).apply(contains_invalid_chars_or_icons)].copy()
        rows_after_char_filter = len(df_filtered)
        print(f"Số dòng sau khi lọc icon/ký tự không hợp lệ: {rows_after_char_filter} (Đã loại bỏ: {rows_after_lang_filter - rows_after_char_filter})")
    else:
        rows_after_char_filter = 0 # Nếu df_filtered rỗng thì không có gì để lọc tiếp
        print("Không có dòng tiếng Anh nào để lọc icon/ký tự.")
        
    # Giữ lại các cột gốc
    # Kiểm tra xem các cột có tồn tại không trước khi chọn
    required_columns = ['sentenceId', 'raw_text', 'aspectTerms']
    existing_required_columns = [col for col in required_columns if col in df_filtered.columns]
    
    if len(existing_required_columns) != len(required_columns):
        print(f"Cảnh báo: Một số cột bắt buộc ({required_columns}) không có trong DataFrame. Các cột hiện có: {df_filtered.columns.tolist()}")
        # Quyết định xử lý: dừng lại, hoặc chỉ lấy các cột có sẵn
        # Ở đây, chúng ta sẽ lấy các cột có sẵn
        if not existing_required_columns:
            print("Lỗi: Không có cột nào trong số các cột bắt buộc tồn tại. Không thể lưu file.")
            return
    
    final_df = df_filtered[existing_required_columns]

    try:
        output_dir = os.path.dirname(output_filepath)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        final_df.to_csv(output_filepath, index=False, encoding='utf-8')
        print(f"Hoàn thành! File đã xử lý được lưu tại: {output_filepath}")
        print(f"Số dòng cuối cùng: {len(final_df)}")
    except Exception as e:
        print(f"Lỗi khi ghi file CSV '{output_filepath}': {e}")

if __name__ == "__main__":
    # Tạo thư mục output_processed nếu chưa có
    processed_dir = 'output_processed'
    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)
        print(f"Đã tạo thư mục: {processed_dir}")



    # Giả sử file nằm cùng cấp với script
    train_file_input = "train.csv"
    test_file_input = "test.csv"

    train_file_output = os.path.join(processed_dir, "train_processed.csv")
    test_file_output = os.path.join(processed_dir, "test_processed.csv")
    
    print("--- BẮT ĐẦU TIỀN XỬ LÝ ---")
    preprocess_csv(train_file_input, train_file_output)
    preprocess_csv(test_file_input, test_file_output)