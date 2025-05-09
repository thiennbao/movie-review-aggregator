from fastapi import FastAPI
import psycopg2
import os
from dotenv import load_dotenv
from psycopg2.extras import execute_values
import logging

# Khởi tạo FastAPI
app = FastAPI(title="Movie Reviews API", description="API to fetch movie reviews with ABSA")

# Load biến môi trường
load_dotenv()

# Hàm kết nối PostgreSQL
def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DATABASE"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("DB_PORT", "5432"),
    )
    
def normalize_review(review, source: str):
    if not isinstance(review, dict):
        print(f"Skipping invalid review item: {review} (type: {type(review)})")
        return None
    role = review.get("role", "user")  # Lấy role từ review, mặc định là "user"
    if source == "imdb":
        return {
            "review": review.get("review", "No Review"),
            "score": review.get("score", "No Score"),
            "author_name": review.get("author_name", "No Author"),
            "review_date": review.get("review_date", None),
            "link": review.get("link", None),
            "role": role,
        }
    elif source == "rottentomatoes":
        sentiment = review.get("sentiment", "N/A")
        score = {
            "POSITIVE": "Positive",
            "NEGATIVE": "Negative",
            "NEUTRAL": "Neutral",
            "N/A": "No Score",
        }.get(sentiment, "No Score")
        return {
            "review": review.get("review", "No Review"),
            "score": score,
            "author_name": review.get("author", "N/A"),
            "review_date": review.get("review_date", None),
            "link": review.get("link", None),
            "role": role,
        }
    elif source == "metacritic":
        return {
            "review": review.get("review", "No Review"),
            "score": review.get("score", "No Score"),
            "author_name": review.get("author_name", "No Author"),
            "review_date": review.get("review_date", None),
            "link": review.get("link", None),
            "role": role,
            "aspects": review.get("aspects", [])
        }
    return None

def save_reviews_to_postgres(reviews, movie_name: str, source: str, movie_link: str = None):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Đảm bảo movie_name không phải None
        if not movie_name:
            movie_name = "Unknown Movie"

        # Kiểm tra xem movie đã tồn tại chưa
        query_check = """
        SELECT movie_id FROM movies
        WHERE movie_name = %s AND (link = %s OR link IS NULL)
        """
        cursor.execute(query_check, (movie_name, movie_link))
        existing_movie = cursor.fetchone()

        if existing_movie:
            movie_id = existing_movie[0]
            logger.info(f"Movie '{movie_name}' already exists with movie_id: {movie_id}")
        else:
            # Thêm movie mới nếu chưa tồn tại
            query_insert_movie = """
            INSERT INTO movies (movie_name, link)
            VALUES (%s, %s)
            ON CONFLICT (movie_name, link) DO NOTHING
            RETURNING movie_id
            """
            cursor.execute(query_insert_movie, (movie_name, movie_link))
            result = cursor.fetchone()
            movie_id = result[0] if result else cursor.execute(query_check, (movie_name, movie_link)).fetchone()[0]
            logger.info(f"Inserted new movie '{movie_name}' with movie_id: {movie_id}")

        if not isinstance(reviews, list):
            print(f"Reviews is not a list: {reviews} (type: {type(reviews)})")
            return

        # Chuẩn hóa đánh giá
        normalized_reviews = [normalize_review(r, source) for r in reviews]
        normalized_reviews = [r for r in normalized_reviews if r is not None]
        if not normalized_reviews:
            print(f"No valid reviews to save for {movie_name}")
            return

        # Lưu đánh giá vào bảng reviews và lấy review_id
        query = """
        INSERT INTO reviews (movie_id, review, score, author_name, review_date, source, role)
        VALUES %s
        ON CONFLICT (review_id) DO NOTHING  -- Sử dụng review_id làm khóa chính
        RETURNING review_id
        """
        values = [
            (movie_id, r["review"], r["score"], r["author_name"], r["review_date"], source, r["role"])
            for r in normalized_reviews
        ]
        execute_values(cursor, query, values, fetch=True)
        review_ids = [row[0] for row in cursor.fetchall()]

        # Lưu aspects vào bảng aspect_sentiment
        aspect_query = """
        INSERT INTO aspect_sentiment (review_id, aspect, sentiment)
        VALUES %s
        ON CONFLICT (review_id, aspect) DO NOTHING  -- Tránh trùng lặp aspect
        """
        aspect_values = []
        for review, review_id in zip(normalized_reviews, review_ids):
            for aspect in review["aspects"]:
                aspect_values.append((
                    review_id,
                    aspect["term"],  # Lưu term vào cột aspect
                    aspect["polarity"]  # Lưu polarity vào cột sentiment
                ))

        if aspect_values:
            execute_values(cursor, aspect_query, aspect_values)
            print(f"Saved {len(aspect_values)} aspects for {len(normalized_reviews)} reviews")

        conn.commit()
        print(f"Saved {len(normalized_reviews)} {source} reviews for {movie_name}")

    except Exception as e:
        print(f"Error saving reviews to database: {e}")
        if conn:
            conn.rollback()
        raise  # Ném lỗi để ReviewsAPIView có thể bắt
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)