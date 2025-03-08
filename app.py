from flask import Flask, request, jsonify
import json
import re
from sentence_transformers import SentenceTransformer, util
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/chatbot/*": {"origins": "https://goddesign14b.blogspot.com"}})

# Load blog posts
def load_blog_posts():
    try:
        with open("blog_posts2.txt", "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open("blog_posts2.txt", "r", encoding="ISO-8859-1") as f:
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

@app.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.json
    user_query = data.get("query", "").strip().lower()
    
    if user_query in ["hi", "hello"]:
        return jsonify({"response": "Hi, How may I help you?"})
    if user_query in ["thank you", "thanks"]:
        return jsonify({"response": "You're welcome! Let me know if you have any other questions."})
    
    if "list topics" in user_query:
        return jsonify({"response": "Here are the available topics:\n" + "\n".join(f" - {topic}" for topic in blog_topics)})
    
    if "overview" in user_query:
        if "blog" in user_query:
            return jsonify({"response": blog_posts.get("Blog Overview", "No overview available.")})
        else:
            matched_topic = next((topic for topic in blog_topics if any(word in topic.lower() for word in user_query.split())), None)
            if matched_topic:
                return jsonify({"response": blog_posts.get(matched_topic, "No content found.")})
            return jsonify({"response": "No matching overview found."})
    
    if "latest post" in user_query:
        return jsonify({"response": f"The latest post is '{latest_post}'."})
    
    if "recommend" in user_query:
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
