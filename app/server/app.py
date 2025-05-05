from flask import Flask
from flask_socketio import SocketIO, emit

import json
import os


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")


@socketio.on("ask_reviews")
def handle_message(url):
    print(f"TODO: crawl reviews for {url}")
    dir_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(dir_path, "mock-reviews.json")
    with open(file_path) as mock_file:
        mock_data = json.load(mock_file)
        for i, review in enumerate(mock_data["reviews"]):
            emit("review", review)
            print(f"Sent review {i} for {url}")
            socketio.sleep(1)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
