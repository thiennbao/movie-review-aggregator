import json
import time
from datetime import datetime
import requests
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import html
import logging
import sys
import random
import glob # Thêm thư viện để tìm file

# --- Simple Logger Setup (Giữ nguyên) ---
def setup_logger(name, log_file, level=logging.INFO):
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        try: os.makedirs(log_dir)
        except OSError as e: print(f"Error creating log dir {log_dir}: {e}")
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    try:
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setFormatter(formatter)
    except IOError as e: print(f"Error setting up file handler {log_file}: {e}"); handler = None
    stream_handler = logging.StreamHandler(sys.stdout); stream_handler.setFormatter(formatter)
    logger = logging.getLogger(name); logger.setLevel(level)
    if logger.hasHandlers(): logger.handlers.clear()
    if handler: logger.addHandler(handler)
    logger.addHandler(stream_handler)
    return logger
# --- End Simple Logger Setup ---

class UserReviewCrawler:
    def __init__(self):
        log_file = f'./logs/user_review_crawler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        self.logger = setup_logger('UserReviewCrawler', log_file)

        self.PAGE_SIZE = 25
        self.MAX_REVIEWS_PER_MOVIE = 100
        # *** THAY ĐỔI: Giới hạn số review tối đa cho mỗi file output ***
        self.MAX_REVIEWS_PER_FILE = 50000 # Đặt giới hạn mong muốn (ví dụ: 100k)

        self.base_url = "https://caching.graphql.imdb.com/"
        self.headers = { # Giữ nguyên headers
            'accept': 'application/graphql+json, application/json',
            'accept-language': 'vi-VN,vi;q=0.9,en-GB;q=0.8,en;q=0.7,fr-FR;q=0.6,fr;q=0.5,en-US;q=0.4',
            'content-type': 'application/json','origin': 'https://www.imdb.com','referer': 'https://www.imdb.com/',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            'x-imdb-client-name': 'imdb-web-next','x-imdb-user-country': 'VN','x-imdb-user-language': 'vi-VN'
        }
        self.output_folder = './output' # Thư mục output chính

        # Đảm bảo thư mục output chính tồn tại
        if not os.path.exists(self.output_folder):
            try:
                os.makedirs(self.output_folder)
                self.logger.info(f"Created directory: {self.output_folder}")
            except OSError as e:
                self.logger.error(f"Could not create directory {self.output_folder}: {e}")
                raise SystemExit(f"Critical error: Cannot create required directory {self.output_folder}")

        self.session = requests.Session()
        self._init_session()

    # _init_session giữ nguyên
    def _init_session(self):
        try:
            self.logger.info("Setting up Chrome for session initialization...")
            chrome_options = Options(); chrome_options.add_argument('--headless'); chrome_options.add_argument('--no-sandbox'); chrome_options.add_argument('--disable-dev-shm-usage')
            driver = webdriver.Chrome(options=chrome_options)
            self.logger.info("Chrome driver initialized")
            driver.get('https://www.imdb.com/'); self.logger.info("Visiting IMDb homepage")
            time.sleep(7)
            cookies = driver.get_cookies(); self.logger.info(f"Retrieved {len(cookies)} cookies")
            for cookie in cookies: self.session.cookies.set(cookie['name'], cookie['value'])
            driver.quit(); self.logger.info("Session initialization completed successfully")
        except Exception as e:
            self.logger.error(f"Error initializing Selenium session: {type(e).__name__} - {str(e)}")
            self.logger.warning("Proceeding without browser-based session cookies.")

    # get_movie_reviews giữ nguyên
    def get_movie_reviews(self, movie_id, movie_name, original_title):
        # ... (code y như phiên bản trước) ...
        after_token = ""; has_next = True; all_reviews = []; page = 1
        self.logger.info(f"Starting fetch for {movie_name} ({movie_id}), limit: {self.MAX_REVIEWS_PER_MOVIE}")
        while has_next and len(all_reviews) < self.MAX_REVIEWS_PER_MOVIE:
            # ... (logic fetch và extract giữ nguyên) ...
             try:
                self.logger.debug(f"Fetching page {page} (Collected: {len(all_reviews)}/{self.MAX_REVIEWS_PER_MOVIE})")
                reviews_page = self._fetch_reviews_page(movie_id, after_token)
                if not reviews_page or 'data' not in reviews_page or not reviews_page['data'].get('title'):
                    # ... (error handling) ...
                    break
                reviews_data = reviews_page['data']['title'].get('reviews')
                if not reviews_data: break
                edges = reviews_data.get('edges', [])
                if not edges and page == 1: self.logger.info(f"No reviews found for {movie_name} ({movie_id}).")

                reviews_processed_this_page = 0
                for edge in edges:
                    if len(all_reviews) >= self.MAX_REVIEWS_PER_MOVIE: has_next = False; break
                    review = self._extract_review_data(edge, movie_id, movie_name, original_title)
                    if review: all_reviews.append(review); reviews_processed_this_page += 1
                if reviews_processed_this_page > 0: self.logger.debug(f"Processed {reviews_processed_this_page} on page {page}. Total: {len(all_reviews)}")

                if len(all_reviews) < self.MAX_REVIEWS_PER_MOVIE:
                    page_info = reviews_data.get('pageInfo', {}); has_next = page_info.get('hasNextPage', False)
                    after_token = page_info.get('endCursor', '')
                    if not has_next: self.logger.info(f"Reached last page for {movie_name}."); break
                else: has_next = False # Đã đủ limit

                page += 1
                if has_next: time.sleep(random.uniform(1.5, 3.0))
             except requests.exceptions.RequestException as req_err: self.logger.error(f"Network error: {req_err}"); time.sleep(5); break
             except Exception as e: self.logger.exception(f"Unexpected error: {str(e)}"); break
        self.logger.info(f"Finished fetching for {movie_name}. Collected {len(all_reviews)} reviews.")
        return all_reviews


    # _fetch_reviews_page giữ nguyên
    def _fetch_reviews_page(self, movie_id, after_token=""):
        # ... (code y như phiên bản trước) ...
        variables = {"after": after_token,"const": movie_id,"filter": {},"first": self.PAGE_SIZE,"locale": "vi-VN","sort": {"by": "HELPFULNESS_SCORE","order": "DESC"}}
        extensions = {"persistedQuery": {"sha256Hash": "89aff4cd7503e060ff1dd5aba91885d8bac0f7a21aa1e1f781848a786a5bdc19","version": 1}}
        encoded_variables = quote(json.dumps(variables)); encoded_extensions = quote(json.dumps(extensions))
        url = f"{self.base_url}?operationName=TitleReviewsRefine&variables={encoded_variables}&extensions={encoded_extensions}"
        try:
            response = self.session.get(url, headers=self.headers, timeout=20); response.raise_for_status(); return response.json()
        except Exception as e: self.logger.error(f"Error fetching page for {movie_id}: {e}"); return None # Đơn giản hóa log lỗi ở đây

# *** PHIÊN BẢN ĐẦY ĐỦ VÀ CHÍNH XÁC ***
    def _extract_review_data(self, edge, movie_id, movie_name, original_title):
        try:
            node = edge.get('node', {})
            if not node:
                self.logger.warning("Encountered an edge with no node data.")
                return None

            # --- Trích xuất dữ liệu ---
            review_id = node.get('id')

            # Lấy nội dung review
            raw_content = node.get('text', {}).get('originalText', {}).get('plaidHtml', '')
            clean_content = html.unescape(raw_content or '').replace('<br/>', '\n').replace('<br>', '\n').strip()

            # Lấy tiêu đề review
            raw_title = node.get('summary', {}).get('originalText', '')
            clean_title = html.unescape(raw_title or '').strip() # Sẽ là "" nếu không có

            # Lấy các trường khác, sử dụng .get() với giá trị mặc định hoặc None
            is_spoiler = node.get('spoiler', False) # Mặc định là False
            author_rating = node.get('authorRating') # Sẽ là None nếu không có
            likes = node.get('helpfulness', {}).get('upVotes', 0) # Mặc định là 0
            dislikes = node.get('helpfulness', {}).get('downVotes', 0) # Mặc định là 0
            username = node.get('author', {}).get('nickName') # Sẽ là None nếu không có
            submit_date = node.get('submissionDate') # Sẽ là None nếu không có

            # --- Kiểm tra điều kiện cơ bản ---
            # Bỏ qua nếu thiếu ID hoặc nội dung chính
            if not review_id or not clean_content:
                 self.logger.warning(f"Skipping review due to missing ID or content for movie {movie_id}. ID: {review_id}")
                 return None

            # --- Tạo dictionary kết quả với đầy đủ các key ---
            review = {
                'review_id': review_id,
                'movie_id': movie_id,
                'movie_name': movie_name,
                'original_title': original_title,
                'review_title': clean_title,       # Key đã có
                'review_content': clean_content,
                'spoiler': is_spoiler,              # Key đã có
                'rating': author_rating,            # Key đã có
                'like': likes,                      # Key đã có
                'dislike': dislikes,                # Key đã có
                'reviewer_username': username,      # Key đã có
                'submission_date': submit_date,     # Key đã có
                'updated_at': datetime.now().isoformat()
            }

            # Ghi log DEBUG để kiểm tra giá trị trước khi trả về (như đề xuất trước)
            self.logger.debug(f"Constructed review dict for {review.get('review_id')}: {review}")

            return review

        except Exception as e:
            # Ghi log lỗi chi tiết kèm traceback
            self.logger.exception(f"Error extracting review data for movie {movie_id}: {str(e)}")
            return None


    def _get_current_output_state(self):
        """Xác định file output tiếp theo và số lượng review hiện có trong đó."""
        current_part_index = 1
        reviews_in_current_part = 0
        output_pattern = os.path.join(self.output_folder, "reviews_part_*.json")
        existing_files = sorted(glob.glob(output_pattern)) # Tìm và sắp xếp các file đã có

        if existing_files:
            latest_file = existing_files[-1]
            try:
                # Lấy chỉ số từ tên file cuối cùng
                filename_part = os.path.basename(latest_file)
                index_str = filename_part.replace("reviews_part_", "").replace(".json", "")
                current_part_index = int(index_str) # Đây là file đang ghi dở hoặc vừa đầy

                # Đếm số dòng (review) trong file cuối cùng này
                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        reviews_in_current_part = sum(1 for _ in f)
                    self.logger.info(f"Resuming. Latest file is {latest_file} with {reviews_in_current_part} reviews.")

                    # Nếu file cuối cùng đã đầy, chuẩn bị sang file mới
                    if reviews_in_current_part >= self.MAX_REVIEWS_PER_FILE:
                        self.logger.info(f"File {latest_file} reached limit ({self.MAX_REVIEWS_PER_FILE}). Starting new file.")
                        current_part_index += 1
                        reviews_in_current_part = 0 # Reset bộ đếm cho file mới

                except IOError as e:
                     self.logger.error(f"Could not read latest file {latest_file} to count lines: {e}. Starting new file index {current_part_index + 1}.")
                     # Nếu không đọc được file cũ, an toàn nhất là bắt đầu file mới
                     current_part_index += 1
                     reviews_in_current_part = 0
                except ValueError:
                     self.logger.error(f"Could not parse index from filename {latest_file}. Starting new file index {current_part_index + 1}.")
                     # Nếu tên file lạ, cũng bắt đầu file mới
                     current_part_index += 1
                     reviews_in_current_part = 0

            except Exception as e:
                self.logger.exception(f"Error determining current output state from existing files. Starting from part 1. Error: {e}")
                current_part_index = 1
                reviews_in_current_part = 0
        else:
             self.logger.info("No existing output files found. Starting from part 1.")

        return current_part_index, reviews_in_current_part

    # *** THAY ĐỔI: Hàm crawl chính ***
    def crawl_movies_reviews(self, input_file):
        """Crawl reviews và lưu vào các file .json được giới hạn số lượng review."""
        if not os.path.exists(input_file):
            self.logger.critical(f"CRITICAL: Input file not found: {input_file}. Exiting.")
            print(f"Lỗi: Không tìm thấy file input: {input_file}.")
            return 0

        movies = []
        try:
            # ... (Đọc file input như cũ) ...
            self.logger.info(f"Reading movies from: {input_file}")
            with open(input_file, 'r', encoding='utf-8') as f: movies = json.load(f)
            if not isinstance(movies, list): self.logger.error(f"{input_file} not a JSON list."); return 0
            self.logger.info(f"Loaded {len(movies)} movie entries.")
        except Exception as e: self.logger.error(f"Error reading {input_file}: {e}"); return 0

        # *** Xác định trạng thái file output hiện tại ***
        current_part_index, reviews_in_current_part = self._get_current_output_state()
        # Format tên file với zero-padding (ví dụ: 001, 002, ...)
        current_output_filename = os.path.join(self.output_folder, f"reviews_part_{current_part_index:03d}.json")

        successful_movies_processed = 0 # Đếm số phim đã xử lý (có thể có hoặc không có review)
        total_movies = len(movies)

        for index, movie in enumerate(movies):
            movie_id = movie.get('id')
            movie_name = movie.get('name', f'Unknown (Index {index})')
            original_title = movie.get('original_title', movie_name)

            if not movie_id or not movie_id.startswith('tt'):
                self.logger.warning(f"Skipping movie index {index} due to invalid 'id': {movie_id}.")
                continue

            self.logger.info(f"\n--- Processing movie {index + 1}/{total_movies}: {movie_name} ({movie_id}) ---")

            # Lấy reviews cho phim này
            movie_reviews = self.get_movie_reviews(movie_id, movie_name, original_title)

            if movie_reviews:
                num_reviews_to_add = len(movie_reviews)

                # *** Kiểm tra xem có cần chuyển sang file mới KHÔNG ***
                # Chỉ chuyển nếu file hiện tại đã CÓ dữ liệu và việc thêm review MỚI sẽ vượt quá giới hạn
                if reviews_in_current_part > 0 and (reviews_in_current_part + num_reviews_to_add) > self.MAX_REVIEWS_PER_FILE:
                    self.logger.info(f"Current file ({os.path.basename(current_output_filename)}) limit reached ({reviews_in_current_part}/{self.MAX_REVIEWS_PER_FILE}). Switching to next file.")
                    current_part_index += 1
                    reviews_in_current_part = 0 # Reset bộ đếm cho file mới
                    # Cập nhật tên file output hiện tại
                    current_output_filename = os.path.join(self.output_folder, f"reviews_part_{current_part_index:03d}.json")
                    self.logger.info(f"Now writing to: {current_output_filename}")

                # *** Ghi reviews vào file .json hiện tại (ở chế độ append) ***
                try:
                    # Mở file ở chế độ append ('a')
                    with open(current_output_filename, 'a', encoding='utf-8') as f:
                        for review in movie_reviews:
                            # Ghi mỗi review thành một dòng JSON
                            f.write(json.dumps(review, ensure_ascii=False) + '\n')

                    reviews_in_current_part += num_reviews_to_add # Cập nhật số review trong file hiện tại
                    self.logger.info(f"Successfully appended {num_reviews_to_add} reviews for {movie_id} to {os.path.basename(current_output_filename)}. Current file review count: {reviews_in_current_part}")
                    successful_movies_processed += 1 # Có thể coi là xử lý thành công nếu ghi được review

                except IOError as e:
                    self.logger.error(f"I/O error appending reviews for {movie_id} to {current_output_filename}: {str(e)}")
                except Exception as e:
                    self.logger.exception(f"Unexpected error appending reviews for {movie_id} to {current_output_filename}: {str(e)}")
            else:
                self.logger.info(f"No reviews were collected for {movie_name} ({movie_id}).")
                # Vẫn có thể tính là phim đã xử lý thành công dù không có review để ghi
                successful_movies_processed += 1


            # Delay giữa các phim
            sleep_time = random.uniform(2.0, 4.0)
            self.logger.debug(f"Sleeping for {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)

        self.logger.info(f"--- Finished processing all {total_movies} movies. ---")
        return successful_movies_processed # Trả về số lượng phim đã xử lý

def main():
    for directory in ['./logs', './output']: # Chỉ cần đảm bảo các thư mục gốc
        try: os.makedirs(directory, exist_ok=True); print(f"Directory ensured: {directory}")
        except OSError as e: print(f"Error creating directory {directory}: {e}")

    crawler = UserReviewCrawler()
    input_file = "output/filtered_movies_omdb.json"

    print(f"Starting crawler. Reading movies from: {input_file}")
    print(f"Reviews limit per movie: {crawler.MAX_REVIEWS_PER_MOVIE}")
    print(f"Output files review limit: {crawler.MAX_REVIEWS_PER_FILE} reviews per file (approx).")
    print(f"Output files format: reviews_part_XXX.json in: {crawler.output_folder}")

    processed_movie_count = crawler.crawl_movies_reviews(input_file)

    if processed_movie_count > 0:
        crawler.logger.info(f"\nCrawling completed. Processed {processed_movie_count} movies.")
        print(f"\nCrawling completed.")
        print(f"Processed {processed_movie_count} movies.")
        print(f"Review data saved in 'reviews_part_XXX.json' files in: {crawler.output_folder}")
    else:
         # ... (Xử lý lỗi như cũ, kiểm tra input file...) ...
         if not os.path.exists(input_file): message = f"... Reason: Input file '{input_file}' not found."
         else: message = "... No movies processed or errors occurred."
         crawler.logger.error(message); print(f"\n{message} Check logs for details.")

if __name__ == "__main__":
    main()