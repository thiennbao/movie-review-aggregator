import json
import re
import os
import glob # Để tìm các file theo pattern
from langdetect import detect, LangDetectException # Cần cài đặt: pip install langdetect
import emoji # Cần cài đặt: pip install emoji

# --- Các hàm lọc được tái sử dụng từ script preprocess_csv.py ---
def is_english(text: str) -> bool:
    """Kiểm tra xem văn bản có phải là tiếng Anh không."""
    try:
        if not isinstance(text, str) or not text.strip():
            return False
        return detect(text) == 'en'
    except LangDetectException:
        return False
    except Exception:
        return False

def contains_invalid_chars_or_icons(text: str, log_invalid_char_debug=False) -> bool:
    """
    Kiểm tra xem văn bản có chứa emoji hoặc các ký tự "không hợp lệ" khác không.
    Sử dụng regex đã được nới lỏng từ các phân tích trước.
    """
    if not isinstance(text, str) or not text.strip(): # Nếu rỗng hoặc không phải string thì coi như không có char invalid
        return False

    if emoji.emoji_count(text) > 0:
        if log_invalid_char_debug:
            emojis_found = [char for char in text if emoji.is_emoji(char)]
            print(f"DEBUG (JSONL): Emoji(s) '{''.join(emojis_found)}' found in: '{text[:70]}...'")
        return True

    # Regex đã được nới lỏng để chấp nhận các ký tự Latin có dấu và một số ký hiệu phổ biến
    pattern = r"[^a-zA-Z0-9\s\.,!?'\":;\-\(\)\[\]%&\$#@\*\+\=/<>’‘“”àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸ…–—_«»]"
    
    match = re.search(pattern, text)
    if match:
        if log_invalid_char_debug:
            print(f"DEBUG (JSONL): Invalid char '{match.group(0)}' (Unicode: {ord(match.group(0))}) found in text: '{text[:70]}...'")
        return True
    return False

def preprocess_single_jsonl_file(input_filepath: str, output_filepath: str, debug_char_filter: bool = False):
    """
    Tiền xử lý một file JSON Lines: loại bỏ review không phải tiếng Anh 
    và review chứa icon/ký tự không hợp lệ trong 'review_content' và 'review_title'.
    """
    if not os.path.exists(input_filepath):
        print(f"Lỗi: File đầu vào '{input_filepath}' không tồn tại.")
        return

    print(f"\nĐang xử lý file: {input_filepath}...")
    
    initial_review_count = 0
    reviews_after_lang_filter = 0
    final_kept_reviews = 0

    try:
        # Đảm bảo thư mục output tồn tại
        output_dir = os.path.dirname(output_filepath)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Đã tạo thư mục output: {output_dir}")

        with open(input_filepath, 'r', encoding='utf-8') as infile, \
             open(output_filepath, 'w', encoding='utf-8') as outfile:
            
            for line_number, line in enumerate(infile, 1):
                initial_review_count += 1
                try:
                    review = json.loads(line.strip())
                except json.JSONDecodeError:
                    print(f"Cảnh báo: Bỏ qua dòng {line_number} không phải JSON hợp lệ trong file {input_filepath}: {line.strip()[:100]}...")
                    continue

                # Lấy nội dung cần kiểm tra
                content_to_check = review.get('review_content', '')
                title_to_check = review.get('review_title', '') # Cũng kiểm tra tiêu đề

                # Bước 1: Lọc ngôn ngữ (chỉ dựa trên review_content)
                if not is_english(content_to_check):
                    continue # Bỏ qua nếu không phải tiếng Anh
                reviews_after_lang_filter += 1

                # Bước 2: Lọc icon/ký tự không hợp lệ (kiểm tra cả content và title)
                # Nếu muốn chỉ kiểm tra content, bỏ `or contains_invalid_chars_or_icons(title_to_check, ...)`
                if contains_invalid_chars_or_icons(content_to_check, log_invalid_char_debug=debug_char_filter) or \
                   contains_invalid_chars_or_icons(title_to_check, log_invalid_char_debug=debug_char_filter):
                    continue # Bỏ qua nếu có ký tự không hợp lệ
                
                # Nếu review vượt qua cả 2 bộ lọc, ghi vào file output
                outfile.write(json.dumps(review, ensure_ascii=False) + '\n')
                final_kept_reviews += 1
        
        print(f"Số review ban đầu trong file: {initial_review_count}")
        removed_by_lang = initial_review_count - reviews_after_lang_filter
        print(f"Số review sau khi lọc ngôn ngữ (tiếng Anh): {reviews_after_lang_filter} (Đã loại bỏ: {removed_by_lang})")
        removed_by_char = reviews_after_lang_filter - final_kept_reviews
        print(f"Số review sau khi lọc icon/ký tự: {final_kept_reviews} (Đã loại bỏ: {removed_by_char})")
        print(f"Hoàn thành! File đã xử lý được lưu tại: {output_filepath}")
        print(f"Số review cuối cùng trong file output: {final_kept_reviews}")

    except Exception as e:
        print(f"Lỗi không mong muốn khi xử lý file '{input_filepath}': {e}")


if __name__ == "__main__":
    # --- Cấu hình đường dẫn ---
    # Giả sử các file reviews_part_XXX.jsonl nằm trong thư mục ./output
    input_folder = "./data" 
    # Thư mục để lưu các file đã xử lý
    processed_folder = "./output_processed_json" 

    if not os.path.exists(processed_folder):
        os.makedirs(processed_folder)
        print(f"Đã tạo thư mục: {processed_folder}")

    # Tìm tất cả các file reviews_part_XXX.jsonl trong thư mục input
    # (Bạn có thể thay đổi pattern "reviews_part_*.jsonl" nếu cần)
    input_file_pattern = os.path.join(input_folder, "reviews_part_*.json")
    review_files = glob.glob(input_file_pattern)

    if not review_files:
        print(f"Không tìm thấy file nào khớp với pattern '{input_file_pattern}' trong thư mục '{input_folder}'.")
        print("Hãy đảm bảo bạn đã chạy crawler review và có các file output đúng vị trí.")
    else:
        print(f"--- BẮT ĐẦU TIỀN XỬ LÝ CHO CÁC FILE JSON ({len(review_files)} files) ---")
        # Bật cờ này thành True nếu bạn muốn xem chi tiết ký tự nào bị lọc bởi bộ lọc ký tự
        debug_character_filter = False 

        for input_file in sorted(review_files): # Sắp xếp để xử lý theo thứ tự
            # Tạo tên file output tương ứng
            base_filename = os.path.basename(input_file)
            output_filename = base_filename.replace(".json", "_processed.json")
            output_file_path = os.path.join(processed_folder, output_filename)
            
            preprocess_single_jsonl_file(input_file, output_file_path, debug_char_filter=debug_character_filter)
        
        print("\n--- HOÀN TẤT TOÀN BỘ QUÁ TRÌNH TIỀN XỬ LÝ ---")