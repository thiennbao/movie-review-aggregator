from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
import asyncio
from crawlers.imdb_crawler import IMDBCrawler
from crawlers.metacritic_crawler import MetacriticCrawler
from crawlers.rotten_crawler import RottenTomatoesCrawler
import uvicorn

# Initialize FastAPI app
app = FastAPI()

# Initialize crawlers
imdb_crawler = IMDBCrawler()
metacritic_crawler = MetacriticCrawler()
rotten_crawler = RottenTomatoesCrawler()

# Pydantic model for request validation
class ReviewRequest(BaseModel):
    url: str
    source: str
    range: list[int] = [0, 100]

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

@app.post("/fetch_reviews")
async def fetch_reviews(request: ReviewRequest):
    """Handle POST request to fetch reviews."""
    try:
        # Extract and validate request data
        url = request.url.rstrip('/')
        reviews_range = request.range

        if not url:
            raise HTTPException(status_code=400, detail="Missing url or source")

        if not isinstance(reviews_range, list) or len(reviews_range) != 2:
            raise HTTPException(status_code=400, detail="Invalid range format, expected [start, end]")

        try:
            start, end = int(reviews_range[0]), int(reviews_range[1])
            if start < 0 or end <= start:
                raise HTTPException(status_code=400, detail="Invalid range: start must be >= 0 and end > start")
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Range values must be integers")
        
        source = "imdb"
        if "imdb" in url:
            source = "imdb"
        elif "rottentomatoes" in url:
            source = "rottentomatoes"
        elif "metacritic" in url:
            source = "metacritic"

        # Validate URL format for the spécifique source
        if source == "imdb" and not is_valid_imdb_url(url):
            raise HTTPException(status_code=400, detail="Invalid IMDb URL. Expected format: https://www.imdb.com/title/ttXXXXXXX/")
        elif source == "metacritic" and not is_valid_metacritic_url(url):
            raise HTTPException(status_code=400, detail="Invalid Metacritic URL. Expected format: https://www.metacritic.com/movie/movie-name/")
        elif source == "rottentomatoes" and not is_valid_rottentomatoes_url(url):
            raise HTTPException(status_code=400, detail="Invalid Rotten Tomatoes URL. Expected format: https://www.rottentomatoes.com/m/movie-name/")
        elif source not in ["imdb", "metacritic", "rottentomatoes"]:
            raise HTTPException(status_code=400, detail="Invalid source. Choose 'imdb', 'metacritic', or 'rottentomatoes'")

        # Process reviews based on source
        reviews = []
        if source == "imdb":
            review_url = imdb_crawler.convert_to_review_url(url)
            reviews = await imdb_crawler.get_reviews_api(review_url, [start, end])
        elif source == "metacritic":
            review_urls = metacritic_crawler.convert_to_review_urls([url])
            reviews = await metacritic_crawler.get_reviews_api(review_urls[0]['href'], [start, end], "critic")
        elif source == "rottentomatoes":
            review_urls = rotten_crawler.convert_to_review_urls([url])
            reviews = await rotten_crawler.get_reviews_api(review_urls[0]['href'], [start, end], "critic")

        return {"reviews": reviews, "count": len(reviews)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6000)