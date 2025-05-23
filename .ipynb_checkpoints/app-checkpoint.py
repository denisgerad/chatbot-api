from flask import Flask, request, jsonify
import json
import re
from sentence_transformers import SentenceTransformer, util
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
# Allow requests from your Blogger site
CORS(app, resources={r"/chatbot/*": {"origins": "https://goddesign14b.blogspot.com"}})

# Load blog posts
def load_blog_posts():
    try:
        with open("blog_posts2.txt", "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open("blog_posts2.txt", "r", encoding="ISO-8859-1") as f:
            content = f.read()

    sections = content.strip().split("\n\n")  # Split by paragraphs
    blog_data = {}
    
    for section in sections:
        lines = section.strip().split("\n")
        title = lines[0].strip()
        content_without_post_number = "\n".join([line for line in lines[1:] if not line.startswith("Post number:")]).strip()
        blog_data[title] = content_without_post_number

    return blog_data

# Load data and model
blog_posts = load_blog_posts()
blog_topics = list(blog_posts.keys())
model = SentenceTransformer("all-MiniLM-L6-v2")
topic_embeddings = model.encode(blog_topics, convert_to_tensor=True)

@app.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.json
    user_query = data.get("query", "").strip().lower()
    
    if user_query in ["hi", "hello"]:
        return jsonify({"response": "Hi, How may I help you?"})
    if user_query in ["thank you", "thanks"]:
        return jsonify({"response": "Thank you for your time and please feel free to share comments, suggestions."})
    
    # Find best topic match
    query_embedding = model.encode(user_query, convert_to_tensor=True)
    similarity_scores = util.pytorch_cos_sim(query_embedding, topic_embeddings)
    best_match_idx = similarity_scores.argmax().item()
    best_match = blog_topics[best_match_idx]
    
    return jsonify({"response": blog_posts.get(best_match, "No relevant content found.")})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
