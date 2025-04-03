import os
from flask import Flask, request, jsonify
import json
import re
from sentence_transformers import SentenceTransformer, util
from sentence_transformers import SentenceTransformer
from flask_cors import CORS
import sqlite3
import psycopg2
import difflib

app = Flask(__name__)
# Allow requests from your Blogger site
CORS(app, resources={r"/chatbot/*": {"origins": "https://goddesign14b.blogspot.com"}})

# Get database URL from Render environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://queries_db_user:Gb8Q5E9uj5O8Ep38FWcwSwR03BWqzyzC@dpg-cv6jltogph6c73dnggd0-a.oregon-postgres.render.com/queries_db")

def store_user_query(query):
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Ensure table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_queries (
                id SERIAL PRIMARY KEY,
                query TEXT
            )
        """)

        # Insert query
        cursor.execute("INSERT INTO user_queries (query) VALUES (%s)", (query,))
        conn.commit()

        cursor.close()
        conn.close()
        print("Query successfully saved!")

    except Exception as e:
        print(f"Error storing query: {e}")

# Load blog posts
def load_blog_posts():
    try:
        with open("blog.txt", "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open("blog.txt", "r", encoding="ISO-8859-1") as f:
            content = f.read()

    sections = content.strip().split("\n\n")
    blog_data = {}
    latest_post = None
    latest_post_number = -1

    for section in sections:
        lines = section.strip().split("\n")
        title = lines[0].strip()

        if title.lower() == "blog overview":
            blog_data["Blog Overview"] = "\n".join(lines[1:]).strip()
            continue

        content_without_post_number = "\n".join([line for line in lines[1:] if not line.startswith("Post number:")]).strip()
        blog_data[title] = content_without_post_number

        match = re.search(r"Post number:\s*(\d+)", section)
        if match:
            post_number = int(match.group(1))
            if post_number > latest_post_number:
                latest_post_number = post_number
                latest_post = title

    return blog_data, latest_post

# Load blog data
blog_posts, latest_post = load_blog_posts()
blog_topics = [topic for topic in blog_posts.keys() if topic != "Blog Overview"]

# Load user feedback
try:
    with open("feedback.json", "r", encoding="utf-8") as f:
        feedback = json.load(f)
except FileNotFoundError:
    feedback = {}

# Create a file to store queries if it doesn't exist
if not os.path.exists("user_queries.json"):
    with open("user_queries.json", "w", encoding="utf-8") as f:
        json.dump([], f)

# Hardcoded lookup dictionary for exact topic names
topic_lookup = {
    "cosmos": "Cosmos",
    "the garden of eden": "The Garden of Eden",
    "evolution and entropy": "Evolution and Entropy",
    "the big bang": "The Big Bang",
    "georges lemaitre": "Georges Lemaitre",
    "standard model": "Standard Model",
    "democritus": "Democritus",
    "aristotle": "Aristotle",
    "copernicus": "Copernicus",
    "galileo": "Galileo",
    "issac newton": "Issac Newton",
    "albert einstein": "Albert Einstein",
    "sun": "Sun",
    "milky way galaxy": "Milky Way Galaxy",
    "dark matter and energy": "Dark Matter and Energy",
    "quantum mechanics": "Quantum Mechanics",
    "global warming": "Global Warming",
    "genetics": "Genetics",
    "the human genome project": "The Human Genome Project",
    "the origin of species": "The Origin of Species",
    "gregor mendel": "Gregor Mendel",
    "eugenics": "Eugenics"
}

@app.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.json
    user_query = data.get("query", "").strip().lower()

    # Store the user query
    store_user_query(user_query)

    # Common greetings and responses
    if user_query in ["hi", "hello"]:
        return jsonify({"response": "Hi, How may I help you?"})

    if user_query in ["thank you", "thanks"]:
        return jsonify({"response": "You're welcome! If you have any suggestions or comments, please feel free to share."})

    if "blog overview" in user_query or "overview of blog" in user_query or "overview about blog" in user_query:
        return jsonify({"response": blog_posts.get("Blog Overview", "No overview available.")})

    if any(phrase in user_query for phrase in ["list topics", "list of topics", "list post", "list of posts"]):
        return jsonify({"response": "Here are the available topics:\n" + "\n".join(f" - {topic}" for topic in topic_lookup.values())})

    if "latest post" in user_query:
        return jsonify({"response": f"The latest post is '{latest_post}'."})

    if any(phrase in user_query for phrase in ["recommend", "best post", "suggest"]):
        return jsonify({"response": "Please check recommendations on the blog."})

    # Normalize the query to match topics
    matched_topic = None
    for key in topic_lookup:
        if key in user_query:
            matched_topic = topic_lookup[key]
            break

    if matched_topic:
        return jsonify({"response": blog_posts.get(matched_topic, "No content found.")})

    return jsonify({"response": "No matching topic found."})



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
