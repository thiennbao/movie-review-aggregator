import requests
import json
import time
import os

OMDB_API_KEY = "    " # Thay bằng API Key của bạn
OUTPUT_FILE = "./output/filtered_movies_omdb.json"
INPUT_FILENAME = "./output/movie_titles_60.json"
try:
    with open(INPUT_FILENAME, "r", encoding="utf-8") as f:
        INPUT_MOVIE_TITLES = json.load(f)
    print(f"✅ Đã tải {len(INPUT_MOVIE_TITLES)} tên phim từ {INPUT_FILENAME}")
    if not isinstance(INPUT_MOVIE_TITLES, list):
         print(f"🚨 Lỗi: File {INPUT_FILENAME} không chứa danh sách JSON hợp lệ.")
         INPUT_MOVIE_TITLES = [] # Đặt thành list rỗng để tránh lỗi sau này
except FileNotFoundError:
    print(f"🚨 Lỗi: Không tìm thấy file {INPUT_FILENAME}. Hãy chạy script generate_titles_by_year.py trước.")
    INPUT_MOVIE_TITLES = []
except json.JSONDecodeError:
    print(f"🚨 Lỗi: File {INPUT_FILENAME} không phải là file JSON hợp lệ.")
    INPUT_MOVIE_TITLES = []
except Exception as e:
    print(f"🚨 Lỗi không xác định khi đọc file {INPUT_FILENAME}: {e}")
    INPUT_MOVIE_TITLES = []

if not os.path.exists("./output"):
    os.makedirs("./output")

collected_movies = []
seen_ids = set()

print(f"Fetching movie data using OMDb API...")

for title in INPUT_MOVIE_TITLES:
    try:
        # Tham số 't' để tìm theo tiêu đề
        url = f"http://www.omdbapi.com/?t={requests.utils.quote(title)}&apikey={OMDB_API_KEY}"
        response = requests.get(url, timeout=10) # Thêm timeout
        response.raise_for_status() # Kiểm tra lỗi HTTP (4xx, 5xx)
        data = response.json()

        if data.get("Response") == "True" and "imdbID" in data:
            movie_id = data.get("imdbID")
            # Kiểm tra trùng lặp ID
            if movie_id and movie_id not in seen_ids:
                movie_data = {
                    "id": movie_id,
                    "name": data.get("Title"),
                    # OMDb thường không có original_title riêng, nếu cần có thể tìm cách khác
                    "original_title": data.get("Title")
                }
                collected_movies.append(movie_data)
                seen_ids.add(movie_id)
                print(f"✅ Found: {data.get('Title')} ({movie_id})")
            elif movie_id in seen_ids:
                print(f"⚠️ Duplicate ID skipped: {movie_id} for title '{title}'")

        else:
            print(f"❌ Movie not found or error for title: '{title}' - Response: {data.get('Error', 'N/A')}")

        # Thêm delay để tránh vượt rate limit
        time.sleep(0.2) # Chờ 0.2 giây giữa các request

    except requests.exceptions.RequestException as e:
        print(f"🚨 Request failed for title '{title}': {e}")
    except json.JSONDecodeError:
         print(f"🚨 Failed to decode JSON response for title '{title}'")
    except Exception as e:
         print(f"🚨 An unexpected error occurred for title '{title}': {e}")


print(f"\n🚀 Total unique movies collected: {len(collected_movies)}")

if collected_movies:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(collected_movies, f, indent=4, ensure_ascii=False)
    print(f"✅ Saved {len(collected_movies)} movies to {OUTPUT_FILE}")
else:
    print("❌ No movies collected.")