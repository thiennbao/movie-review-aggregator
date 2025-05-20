import requests
import json
import time
import os
from datetime import datetime

# --- Cấu hình ---
# !!! THAY BẰNG API KEY (V3 AUTH) CỦA BẠN TỪ TMDB !!!
TMDB_API_KEY = "YOUR_TMDB_API_KEY_V3" # Thay bằng API Key của bạn
# !!! Nếu không có API Key, hãy tạo một tài khoản trên TMDB và lấy key tại đây: https://www.themoviedb.org/settings/api
# -----------------------------------------------------

OUTPUT_FILENAME = "tmdb_movie_titles_by_year.json" # File lưu kết quả
YEAR_START = 1929 # Hoặc năm bắt đầu bạn muốn
YEAR_END = datetime.now().year # Năm kết thúc (năm hiện tại)
LANGUAGE = "en-US" # Ngôn ngữ cho tên phim (en-US thường tốt cho OMDb)
SORT_BY = "popularity.desc" # Sắp xếp theo độ phổ biến giảm dần
DELAY_BETWEEN_PAGES = 0.5 # Giây - Nghỉ giữa các trang trong cùng 1 năm (TMDB rate limit ~40-50 req/10s)
DELAY_BETWEEN_YEARS = 1 # Giây - Nghỉ giữa các năm khác nhau (nếu cần)

TMDB_BASE_URL = "https://api.themoviedb.org/3"

def fetch_movies_for_year(year, api_key):
    """Hàm lấy danh sách tên phim cho một năm từ TMDB, xử lý phân trang."""
    titles_in_year = set() # Dùng set để tránh trùng lặp trong năm
    page = 1
    total_pages = 1 # Sẽ cập nhật sau request đầu tiên
    max_pages_per_year = 25 # Giới hạn số trang cho mỗi năm để tránh quá nhiều request (500 phim) - điều chỉnh nếu cần

    print(f"\nFetching movies for year: {year}")

    while page <= total_pages and page <= max_pages_per_year:
        print(f"  - Fetching page {page}/{total_pages if total_pages > 1 else '?' }...")
        try:
            params = {
                'api_key': api_key,
                'primary_release_year': year,
                'language': LANGUAGE,
                'sort_by': SORT_BY,
                'page': page,
                'include_adult': 'false'
            }
            response = requests.get(f"{TMDB_BASE_URL}/discover/movie", params=params, timeout=15)
            response.raise_for_status() # Kiểm tra lỗi HTTP (4xx, 5xx)

            data = response.json()

            # Cập nhật tổng số trang từ request đầu tiên
            if page == 1:
                total_pages = data.get('total_pages', 1)
                print(f"  - Year {year}: Found {data.get('total_results', 0)} movies across ~{total_pages} pages.")
                # Giới hạn lại total_pages nếu vượt max_pages_per_year
                total_pages = min(total_pages, max_pages_per_year)


            results = data.get('results', [])
            if not results and page > 1: # Nếu trang sau trang 1 không có kết quả thì dừng
                 print(f"  - No more results found for year {year} at page {page}.")
                 break

            count_before = len(titles_in_year)
            for movie in results:
                # Lấy title, có thể dùng original_title nếu title không có
                title = movie.get('title') or movie.get('original_title')
                if title:
                    titles_in_year.add(title.strip())

            count_after = len(titles_in_year)
            print(f"    -> Added {count_after - count_before} new unique titles from page {page}.")

            page += 1 # Chuyển sang trang tiếp theo
            time.sleep(DELAY_BETWEEN_PAGES) # Quan trọng: Chờ giữa các request trang

        except requests.exceptions.HTTPError as e:
            print(f"🚨 HTTP Error fetching page {page} for year {year}: {e}")
            # Nếu lỗi 4xx (vd: 401 Unauthorized, 404 Not Found) thì dừng luôn cho năm đó
            if 400 <= e.response.status_code < 500:
                 print("   Stopping fetch for this year due to client error.")
                 break
            # Nếu lỗi server (5xx), có thể thử lại hoặc chờ lâu hơn
            time.sleep(5) # Chờ lâu hơn nếu lỗi server
        except requests.exceptions.RequestException as e:
            print(f"🚨 Request Error fetching page {page} for year {year}: {e}")
            time.sleep(5) # Chờ và thử lại ở vòng lặp sau (nếu có) hoặc dừng
            break # Hoặc dừng hẳn cho năm đó
        except json.JSONDecodeError:
             print(f"🚨 Error decoding JSON response for page {page}, year {year}.")
             # Thường là do response rỗng hoặc lỗi mạng, dừng cho năm này
             break
        except Exception as e:
             print(f"🚨 An unexpected error occurred for page {page}, year {year}: {e}")
             break # Dừng để tránh lỗi lặp lại

    print(f"  - Finished year {year}. Collected {len(titles_in_year)} unique titles.")
    return titles_in_year

if __name__ == "__main__":
    if TMDB_API_KEY == "YOUR_TMDB_API_KEY_V3":
        print("🚨 LỖI: Bạn chưa thay thế 'YOUR_TMDB_API_KEY_V3' bằng API Key thực của bạn!")
        print("👉 Hãy lấy API Key (v3 auth) từ trang TMDB: https://www.themoviedb.org/settings/api")
        exit()

    all_movie_titles = set()
    print(f"🚀 Bắt đầu quá trình lấy tên phim từ TMDB ({YEAR_START} - {YEAR_END})...")

    for current_year in range(YEAR_START, YEAR_END + 1):
        year_titles = fetch_movies_for_year(current_year, TMDB_API_KEY)
        if year_titles:
            count_before = len(all_movie_titles)
            all_movie_titles.update(year_titles)
            print(f"   -> Tổng cộng thêm {len(all_movie_titles) - count_before} tên phim mới (Tổng duy nhất: {len(all_movie_titles)})")

        # Có thể thêm delay giữa các năm nếu muốn cẩn thận hơn
        if current_year < YEAR_END and DELAY_BETWEEN_YEARS > 0:
             print(f"--- Nghỉ {DELAY_BETWEEN_YEARS} giây trước khi xử lý năm {current_year + 1} ---")
             time.sleep(DELAY_BETWEEN_YEARS)

    print(f"\n\n🚀 Hoàn thành! Tổng cộng thu thập được {len(all_movie_titles)} tên phim duy nhất từ TMDB ({YEAR_START} - {YEAR_END}).")

    # Chuyển set thành list và sắp xếp
    final_title_list = sorted(list(all_movie_titles))

    # Lưu danh sách tên phim vào file JSON
    try:
        output_folder = "./output"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        output_path = os.path.join(output_folder, OUTPUT_FILENAME)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(final_title_list, f, indent=4, ensure_ascii=False)
        print(f"✅ Đã lưu danh sách tên phim vào: {output_path}")

    except Exception as e:
        print(f"🚨 Lỗi khi lưu file: {e}")

    print("\nBây giờ bạn có thể:")
    print(f"1. Sử dụng file '{output_path}' làm đầu vào cho script `omdb.py`.")
    print(f"2. Sửa `omdb.py` để đọc trực tiếp file này (như hướng dẫn trước) thay vì dùng list cứng.")
    print(f"3. `omdb.py` sẽ dùng các tên phim này để tìm IMDb ID chính xác.")