import psycopg2
import os
from dotenv import load_dotenv
import json


load_dotenv()


def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DATABASE"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("DB_PORT", "5432"),
    )


def get_reviews(url, range):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = f"""
            select * from reviews
            where url = %s
            order by date
            limit %s OFFSET %s
        """
        cursor.execute(query, (url, range[1] - range[0], range[0]))
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        return records
    except Exception as e:
        print(f"Error: {e}")
        return []


def save_review(review):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = f"""
            insert into reviews (id, url, "user", date, results)
            values (%s, %s, %s, %s, %s)
            on conflict (id) do nothing
        """
        cursor.execute(query, (review["id"], review["url"], review["user"], review["date"], json.dumps(review["results"])))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
        return []