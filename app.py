import os
from flask import Flask, request, jsonify
import json
import re
from sentence_transformers import SentenceTransformer, util
from flask import Flask
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
# Allow requests from your Blogger site
CORS(app, resources={r"/chatbot/*": {"origins": "https://goddesign14b.blogspot.com"}})

# Initialize database
def init_db():
    conn = sqlite3.connect("queries.db")  # SQLite database file
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Store user query in the database
def store_user_query(query):
    print(f"Storing query: {query}")  # Debugging log
    try:
        conn = sqlite3.connect("queries.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO user_queries (query) VALUES (?)", (query,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error storing query: {e}")

# Call init_db() at the start of the app
init_db()

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

# Load sentence transformer model
model = SentenceTransformer("all-MiniLM-L6-v2")
topic_embeddings = model.encode(blog_topics, convert_to_tensor=True)

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

# Function to store user queries
def store_user_query(query):
    print(f"Storing query: {query}")  # Add a print statement to check the query
    try:
        with open("user_queries.json", "r+", encoding="utf-8") as f:
            queries = json.load(f)
            queries.append({"query": query})
            f.seek(0)  # Go to the start of the file
            json.dump(queries, f, indent=4)
    except Exception as e:
        print(f"Error storing query: {e}")  # Handle potential issues with file access

@app.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.json
    user_query = data.get("query", "").strip().lower()
    
    # Store the user query
    store_user_query(user_query)
    
    # Response logic
    if user_query in ["hi", "hello"]:
        return jsonify({"response": "Hi, How may I help you?"})
    
    if user_query in ["thank you", "thanks"]:
        return jsonify({"response": "You're welcome! Let me know if you have any other questions."})

    if any(phrase in user_query for phrase in ["list topics", "list of topics", "list post", "list of posts"]):
        return jsonify({"response": "Here are the available topics:\n" + "\n".join(f" - {topic}" for topic in blog_topics)})
    
    if "overview" in user_query or "summary" in user_query:
        if "blog" in user_query:
            return jsonify({"response": blog_posts.get("Blog Overview", "No overview available.")})
        else:
            matched_topic = next((topic for topic in blog_topics if any(word in topic.lower() for word in user_query.split())), None)
            if matched_topic:
                return jsonify({"response": blog_posts.get(matched_topic, "No content found.")})
            return jsonify({"response": "No matching overview found."})
    
    if "latest post" in user_query:
        return jsonify({"response": f"The latest post is '{latest_post}'."})
    
    if any(phrase in user_query for phrase in ["recommend", "best post", "suggest"]):
       return jsonify({"response": "Please check recommendations on the blog."})

    if user_query.startswith("this is incorrect"):
        return jsonify({"response": "Please specify the correct topic."})
    
    # Handle user feedback correction
    if user_query in feedback:
        best_match = feedback[user_query]
    else:
        query_embedding = model.encode(user_query, convert_to_tensor=True)
        similarity_scores = util.pytorch_cos_sim(query_embedding, topic_embeddings)
        best_match_idx = similarity_scores.argmax().item()
        best_match = blog_topics[best_match_idx]
    
    return jsonify({"response": blog_posts.get(best_match, "No relevant content found.")})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
