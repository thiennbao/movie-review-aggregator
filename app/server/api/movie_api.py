from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, HttpUrl, validator
from typing import Literal, List
from services.review_service import fetch_and_store_reviews_ws
import logging
import json
import traceback
import asyncio

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Movie Reviews API",
    description="API to fetch movie reviews via crawler API and store them in the database",
)

# Pydantic model cho yêu cầu thu thập đánh giá
class ReviewRequest(BaseModel):
    url: HttpUrl
    source: Literal["imdb", "metacritic", "rottentomatoes"]
    range: List[int]

    @validator("range")
    def validate_range(cls, v):
        if len(v) != 2:
            raise ValueError("Range must contain exactly two integers: [start, end]")
        start, end = v
        if start < 0:
            raise ValueError("Range start must be >= 0")
        if end <= start:
            raise ValueError("Range end must be greater than start")
        return v

@app.websocket("/ws/reviews/fetch")
async def fetch_and_store_reviews_ws_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint to fetch reviews from the crawler API and stream them to the client.
    """
    await websocket.accept()
    try:
        # Receive initial request
        data = await websocket.receive_json()
        try:
            request = ReviewRequest(**data)
            logger.info(f"Received valid request: {json.dumps(data)}")
        except ValueError as e:
            await websocket.send_json({"error": f"Invalid request format: {str(e)}"})
            return

        async for batch in fetch_and_store_reviews_ws(str(request.url), request.source, request.range):
            await websocket.send_json(batch)

    except WebSocketDisconnect:
        logger.info("Client disconnected from WebSocket")
    except HTTPException as e:
        if websocket.client_state == 1:  # CONNECTED
            await websocket.send_json({"error": e.detail})
    except Exception as e:
        logger.error(f"Error in fetch_and_store_reviews_ws: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        if websocket.client_state == 1:  # CONNECTED
            await websocket.send_json({"error": f"Internal server error: {str(e)}"})
    finally:
        if websocket.client_state == 1:  # CONNECTED
            await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)