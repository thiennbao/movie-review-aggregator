from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, HttpUrl
from typing import Literal
import re
from imdb_crawler import IMDBCrawler
from metacritic_crawler import MetacriticCrawler
from rotten_crawler import RottenTomatoesCrawler

app = FastAPI(title="Movie Reviews API", description="API to fetch movie reviews from IMDb, Metacritic, and Rotten Tomatoes")

# Pydantic model for request validation
class ReviewRequest(BaseModel):
    url: HttpUrl
    source: Literal["imdb", "metacritic", "rottentomatoes"]

# Initialize crawlers
imdb_crawler = IMDBCrawler()
metacritic_crawler = MetacriticCrawler()
rotten_crawler = RottenTomatoesCrawler()

def is_valid_imdb_url(url: str) -> bool:
    """Validate IMDb movie URL."""
    pattern = r"^https://www\.imdb\.com/title/tt\d+/?$"
    return bool(re.match(pattern, url))

def is_valid_metacritic_url(url: str) -> bool:
    """Validate Metacritic movie URL."""
    pattern = r"^https://www\.metacritic\.com/movie/[\w-]+/?$"
    return bool(re.match(pattern, url))

def is_valid_rottentomatoes_url(url: str) -> bool:
    """Validate Rotten Tomatoes movie URL."""
    pattern = r"^https://www\.rottentomatoes\.com/m/[\w-]+/?$"
    return bool(re.match(pattern, url))

@app.websocket("/ws/reviews")
async def websocket_reviews(websocket: WebSocket):
    """WebSocket endpoint to stream reviews in real-time."""
    await websocket.accept()
    try:
        while True:
            try:
                data = await websocket.receive_json()
                url = data.get("url")
                if data.get("source"):
                    source = data.get("source")
                elif "imdb" in url:
                    source = "imdb"
                elif "metacritic" in url:
                    source = "metacritic"              
                elif "rottentomatoes" in url:
                    source = "rottentomatoes"
                reviews_range = data.get("range", [0, 100])

                if not url or not source:
                    await websocket.send_json({"error": "Missing url or source"})
                    return  # Exit the loop instead of closing immediately

                url = str(url).rstrip('/')
                source = source.lower()

                # Validate URL format for the specific source
                if source == "imdb" and not is_valid_imdb_url(url):
                    await websocket.send_json({"error": "Invalid IMDb URL. Expected format: https://www.imdb.com/title/ttXXXXXXX/"})
                    return
                elif source == "metacritic" and not is_valid_metacritic_url(url):
                    await websocket.send_json({"error": "Invalid Metacritic URL. Expected format: https://www.metacritic.com/movie/movie-name/"})
                    return
                elif source == "rottentomatoes" and not is_valid_rottentomatoes_url(url):
                    await websocket.send_json({"error": "Invalid Rotten Tomatoes URL. Expected format: https://www.rottentomatoes.com/m/movie-name/"})
                    return

                if source == "imdb":
                    review_url = imdb_crawler.convert_to_review_url(url)
                    await imdb_crawler.get_reviews_ws(review_url,reviews_range, websocket)
                elif source == "metacritic":
                    review_urls = metacritic_crawler.convert_to_review_urls([url])
                    print(review_urls)
                    await metacritic_crawler.get_reviews_ws(review_urls[0]['href'],reviews_range, websocket, "critic")
                elif source == "rottentomatoes":
                    review_urls = rotten_crawler.convert_to_review_urls([url])
                    print(review_urls)
                    await rotten_crawler.get_reviews_ws(review_urls[0]['href'],reviews_range, websocket, "critic")
                else:
                    await websocket.send_json({"error": "Invalid source. Choose 'imdb', 'metacritic', or 'rottentomatoes'"})
                    return

            except WebSocketDisconnect:
                print("Client disconnected")
                break
            except Exception as e:
                await websocket.send_json({"error": f"Error processing request: {str(e)}"})
                break

    finally:
        # Only close if the connection is still active
        if websocket.client_state == 1:  # CONNECTED
            await websocket.close()
            
            
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)