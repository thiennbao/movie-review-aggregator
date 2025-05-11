from flask import Flask
from flask_socketio import SocketIO, emit
import requests
import uuid
import json

from service import db_connection
from utils import utils


app = Flask(__name__)
socket_server = SocketIO(app, cors_allowed_origins="*")


@socket_server.on("ask_reviews")
def handle_message(data):
    url, range = data["url"], data["range"]
    
    # Read reviews from database
    reviews_in_db = db_connection.get_reviews(url, range)
    reviews_in_db = [{
        "id": review[0],
        "user": review[1],
        "date": utils.serialize_date(review[2]),
        "results": json.loads(review[3]),
    } for review in reviews_in_db]
    
    # Send reviews to client
    for review in reviews_in_db:
        emit("review", review)

    # If not enough, request crawler to crawl
    if len(reviews_in_db) < range[1] - range[0]:
        range_to_crawl = [range[0] + len(reviews_in_db), range[1]]
        crawler_res = requests.post("http://localhost:6000/fetch_reviews", json={"url": url, "range": range_to_crawl, "source": "imdb"})
        reviews_from_crawler = crawler_res.json()["reviews"]
        print(f"Got {len(reviews_from_crawler)} reviews from crawler")
        for review in reviews_from_crawler:
            res = requests.post("http://localhost:8000/predict", json={"review": review["review"]})
            new_review = {
                "id": str(uuid.uuid4()),
                "url": url,
                "user": review["author_name"],
                "date": review["review_date"],
                "results": res.json()["results"]
            }
            emit("review", new_review)
            db_connection.save_review(new_review)



if __name__ == "__main__":
    socket_server.run(app, host="0.0.0.0", port=5000)
