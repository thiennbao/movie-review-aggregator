import websockets
import json
import re
import logging
from typing import Optional, Literal, List, AsyncGenerator
from psycopg2.extras import RealDictCursor
from .db_connection import get_db_connection
from .db_connection import save_reviews_to_postgres
import os
from dotenv import load_dotenv
import asyncio
from fastapi import HTTPException
from datetime import date, datetime

# Load biến môi trường
load_dotenv()

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Hàm xác thực URL
def is_valid_imdb_url(url: str) -> bool:
    pattern = r"^https://www\.imdb\.com/title/tt\d+/?$"
    return bool(re.match(pattern, url))

def is_valid_metacritic_url(url: str) -> bool:
    pattern = r"^https://www\.metacritic\.com/movie/[\w-]+/?$"
    return bool(re.match(pattern, url))

def is_valid_rottentomatoes_url(url: str) -> bool:
    pattern = r"^https://www\.rottentomatoes\.com/m/[\w-]+/?$"
    return bool(re.match(pattern, url))

def normalize_url(url: str) -> str:
    """Normalize URL by removing trailing slashes and converting to lowercase."""
    return url.rstrip('/').lower()

def serialize_date(obj):
    """Convert date or datetime objects to ISO 8601 strings."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return obj

async def fetch_reviews_with_websocket(url: str, source: str, max_retries: int = 3, timeout: float = 300.0) -> List[dict]:
    """
    Fetch reviews from the crawler API via WebSocket with retry logic (for HTTP endpoint).
    """
    crawler_api = os.getenv("CRAWLER_API_BASE_URL", "ws://localhost:5000")  # Adjusted for local testing
    websocket_url = f"{crawler_api}/ws/reviews"
    reviews = []
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempt {attempt}/{max_retries}: Connecting to WebSocket {websocket_url} for {url} ({source})")
            async with websockets.connect(websocket_url, timeout=timeout) as websocket:
                # Send request
                request_data = {"url": url, "source": source}
                await websocket.send(json.dumps(request_data))
                logger.info(f"Sent request: {request_data}")

                # Receive review batches
                while True:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                        data = json.loads(message)
                        
                        if "error" in data:
                            logger.error(f"WebSocket error: {data['error']}")
                            raise HTTPException(status_code=400, detail=data["error"])
                        
                        if "reviews" in data:
                            batch_reviews = data["reviews"]
                            logger.info(f"Received batch {data.get('batch_num', 'unknown')} with {data.get('count', 0)} reviews")
                            reviews.extend(batch_reviews)
                            
                    except asyncio.TimeoutError:
                        logger.warning(f"Attempt {attempt}: WebSocket timeout after {timeout} seconds")
                        raise HTTPException(status_code=504, detail="WebSocket timeout while receiving reviews")
                    except websockets.exceptions.ConnectionClosed:
                        logger.info("WebSocket connection closed")
                        break
                
                return reviews
                
        except (websockets.exceptions.WebSocketException, asyncio.TimeoutError) as e:
            logger.warning(f"Attempt {attempt}: WebSocket error: {str(e)}")
            if attempt == max_retries:
                raise HTTPException(status_code=500, detail=f"Failed to fetch reviews after {max_retries} attempts: {str(e)}")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Attempt {attempt}: Unexpected error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

async def keep_alive(websocket):
    """Send ping messages to keep WebSocket connection alive."""
    try:
        while True:
            await asyncio.sleep(30)  # Ping every 30 seconds
            await websocket.ping()
            logger.debug("Sent ping to keep WebSocket alive")
    except Exception as e:
        logger.warning(f"Keep-alive ping failed: {str(e)}")

async def fetch_reviews_with_websocket_stream(url: str, source: str, reviews_range: list, max_retries: int = 5, timeout: float = 600.0) -> AsyncGenerator[dict[str, any], None]:
    """
    Fetch reviews from the crawler API via WebSocket and stream batches.
    """
    crawler_api = os.getenv("CRAWLER_API_BASE_URL", "ws://localhost:5000")
    websocket_url = f"{crawler_api}/ws/reviews"
    
    try:
        logger.info(f"Connecting to WebSocket {websocket_url} for {url} ({source})")
        async with websockets.connect(websocket_url, timeout=timeout) as websocket:
            # Start keep-alive task
            # asyncio.create_task(keep_alive(websocket))
                
            # Send request
            request_data = {"url": url, "source": source, "range": reviews_range, "batch_size": 50}
            await websocket.send(json.dumps(request_data))
            logger.info(f"Sent request: {request_data}")

            # Stream review batches
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                    logger.debug(f"Raw message received: {message}")
                    data = json.loads(message)
                        
                    if "error" in data:
                        logger.error(f"WebSocket error: {data['error']}")
                        yield {"error": data["error"]}
                        return
                        
                    if "reviews" in data:
                        logger.info(f"Streaming batch {data.get('batch_num', 'unknown')} with {data.get('count', 0)} reviews")
                        yield data

                        # Gửi xác nhận về server
                        confirmation = {"status": "received", "batch_num": data.get("batch_num", 0)}
                        await websocket.send(json.dumps(confirmation))
                        logger.info(f"Sent confirmation for batch {data.get('batch_num', 'unknown')}")
                    if "INFO" in data:
                        logger.info(f"Info message: {data['INFO']}")
                        yield {"info": data["INFO"]}
                            
                    if "NO MORE REVIEWS" in data:
                        logger.info("No more reviews to fetch")
                        yield {"message": "No more reviews to fetch"}
                        break
                            
                except asyncio.TimeoutError:
                    logger.error("Timeout waiting for data from server")
                    yield {"error": "Timeout waiting for data from server"}
                    return
                except websockets.exceptions.ConnectionClosed:
                    logger.info("WebSocket connection closed")
                    break
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode JSON: {str(e)}")
                    yield {"error": f"Invalid JSON data: {str(e)}"}
                    return
                except Exception as e:
                    logger.error(f"Unexpected error receiving data: {str(e)}")
                    yield {"error": f"Unexpected error: {str(e)}"}
                    return
    except (websockets.exceptions.WebSocketException, asyncio.TimeoutError) as e:
        logger.warning(f"WebSocket error: {str(e)}")
        yield {"error": f"Failed to fetch reviews : {str(e)}"}
        await asyncio.sleep(2)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        yield {"error": f"Unexpected error: {str(e)}"}
        return

async def fetch_and_store_reviews_ws(url: str, source: str, reviews_range: Optional[List[int]] = None) -> AsyncGenerator[dict, None]:
    """
    Fetch reviews from the crawler API via WebSocket, store them in the database, and stream batches.
    """
    url = normalize_url(url)
    source = source.lower()
    start, end = reviews_range if reviews_range else (0, 100)
    
    logger.info(f"Streaming reviews for URL: {url}, Source: {source}")

    # Kiểm tra URL trong database
    conn = None
    cursor = None
    count = 0
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = "SELECT movie_name FROM movies WHERE link ILIKE %s"
        cursor.execute(query, (f"%{url}%",))
        movie = cursor.fetchone()
        
        if movie:
            movie_name = movie["movie_name"]
            query = "SELECT COUNT(*) FROM reviews WHERE movie_id = (SELECT movie_id FROM movies WHERE movie_name = %s) AND source = %s"
            cursor.execute(query, (movie_name, source))
            count_row = cursor.fetchone()
            count = count_row['count']
            logger.info(f"Found {count} existing reviews for {movie_name} from {source}")
            
            if start < count:
                reviews_data = await query_reviews(movie_name, source, reviews_range=reviews_range)
                number_of_reviews = reviews_data["count"]
                yield {
                    "message": f"Reviews for {movie_name} already exist in the database.",
                    "movie_name": movie_name,
                    "reviews": reviews_data["reviews"],
                    "count": reviews_data["count"]
                }
                if count >= end:
                    return
    except Exception as e:
        logger.error(f"Database query error: {str(e)}")
        yield {"error": f"Database query error: {str(e)}"}
        return
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    # Adjust range to fetch only remaining reviews
    new_start = 0
    if start > count:
        new_start = count
    else:
        new_start = start + number_of_reviews
    if end <= new_start:
        logger.info("No additional reviews needed to fetch")
        yield {"message": "No additional reviews needed", "count": 0}
        return

    # Xác thực URL
    if source == "imdb" and not is_valid_imdb_url(url):
        yield {"error": "Invalid IMDb URL. Expected format: https://www.imdb.com/title/ttXXXXXXX/"}
        return
    elif source == "metacritic" and not is_valid_metacritic_url(url):
        yield {"error": "Invalid Metacritic URL. Expected format: https://www.metacritic.com/movie/movie-name/"}
        return
    elif source == "rottentomatoes" and not is_valid_rottentomatoes_url(url):
        yield {"error": "Invalid Rotten Tomatoes URL. Expected format: https://www.rottentomatoes.com/m/movie-name/"}
        return

    # Fetch and stream reviews
    reviews_count = 0
    async for batch in fetch_reviews_with_websocket_stream(url, source, [new_start, end], max_retries=5, timeout=600.0):
        if "error" in batch:
            logger.error(f"Error fetching reviews: {batch['error']}")
            yield batch
            return

        reviews = batch.get("reviews", [])
        reviews_count += len(reviews)
        if not reviews:
            continue

        # Sửa đổi danh sách reviews
        modified_reviews = []
        for review in reviews:
            modified_review = {
                "review": review.get("review", ""),
                "score": review.get("score", "N/A"),
                "user": review.get("author_name", "Unknown"),
                "review_date": review.get("review_date", None) if review.get("review_date") != "" else None,
                "source": source,
                "role": review.get("role", "user"),
                "aspects": review.get("aspects", []),
            }
            modified_reviews.append(modified_review)

        # Lấy tên phim
        movie_name = reviews[0]["movie_name"] if reviews and "movie_name" in reviews[0] else "Unknown Movie"

        # Lưu đánh giá vào cơ sở dữ liệu (trong task bất đồng bộ để tránh chặn)
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: save_reviews_to_postgres(modified_reviews, movie_name, source, url))
            logger.info(f"Saved batch {batch.get('batch_num', 'unknown')} with {len(modified_reviews)} reviews for {movie_name}")
        except Exception as e:
            logger.error(f"Failed to save reviews to database: {str(e)}")
            yield {"error": f"Database save error: {str(e)}"}
            return

        # Yield batch to client
        if reviews_count + new_start > start:
            yield {
                "batch_num": batch.get("batch_num"),
                "reviews": modified_reviews,
                "count": len(modified_reviews)
            }

async def query_reviews(movie_name: Optional[str] = None, source: Optional[str] = None, limit: int = 100, reviews_range: Optional[List[int]] = None) -> dict:
    """
    Query reviews from the database based on movie name and/or source.
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Truy vấn reviews
        query = """
        SELECT r.review_id, r.review, r.score, r.author_name AS user, r.review_date, r.source, r.role
        FROM reviews r
        JOIN movies m ON r.movie_id = m.movie_id
        WHERE 1=1
        """
        params = []

        if movie_name:
            query += " AND m.movie_name ILIKE %s"
            params.append(f"%{movie_name}%")
        if source != "rottentomatoes":
            query += " AND r.source = %s"
            params.append(source)
        else:
            query += " AND r.source IN ('rottentomatoes', 'rotten')"

        if reviews_range:
            start, end = reviews_range
            if start < 0 or end < start:
                raise HTTPException(status_code=400, detail="Invalid range: start must be >= 0 and end >= start")
            query += " ORDER BY r.review_date DESC OFFSET %s LIMIT %s"
            params.extend([start, end - start + 1])
        else:
            query += " ORDER BY r.review_date DESC LIMIT %s"
            params.append(limit)

        logger.info(f"Executing query_reviews with movie_name: {movie_name or 'all'}, source: {source or 'all'}, range: {reviews_range or limit}")
        
        cursor.execute(query, params)
        reviews = cursor.fetchall()
        
        for review in reviews:
            review["review_date"] = serialize_date(review.get("review_date"))

        # Truy vấn aspects cho các reviews
        review_ids = [review["review_id"] for review in reviews]
        if review_ids:
            aspect_query = """
            SELECT review_id, aspect, sentiment
            FROM aspect_sentiment
            WHERE review_id IN %s
            """
            cursor.execute(aspect_query, (tuple(review_ids),))
            aspects = cursor.fetchall()

            # Nhóm aspects theo review_id
            aspects_by_review = {}
            for aspect in aspects:
                review_id = aspect["review_id"]
                if review_id not in aspects_by_review:
                    aspects_by_review[review_id] = []
                aspects_by_review[review_id].append({
                    "term": aspect["aspect"],
                    "polarity": aspect["sentiment"]
                })

            # Thêm aspects vào reviews
            for review in reviews:
                review["aspects"] = aspects_by_review.get(review["review_id"], [])

        logger.debug(f"Queried reviews: {reviews}")
        logger.info(f"Queried {len(reviews)} reviews for movie: {movie_name or 'all'}, source: {source or 'all'}")

        return {"movie_name": movie_name, "reviews": reviews, "count": len(reviews)}
    finally:
        cursor.close()
        conn.close()

async def query_movies(limit: int = 100):
    """
    Query movies from the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        query = """
        SELECT m.movie_name, m.link
        FROM movies m
        LIMIT %s
        """
        params = [limit]

        cursor.execute(query, params)
        movies = cursor.fetchall()

        logger.info(f"Queried {len(movies)} movies")
        return {"movies": movies, "count": len(movies)}
    finally:
        cursor.close()
        conn.close()