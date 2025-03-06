from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer, util
from flask_cors import CORS

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

@app.route("/blog-content", methods=["GET"])
def get_blog_content():
    try:
        with open("blog_posts1.txt", "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open("blog_posts1.txt", "r", encoding="ISO-8859-1") as f:
            content = f.read()

    return jsonify({"blogContent": content})


def load_blog_topics():
    try:
        with open("blog_posts1.txt", "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open("blog_posts1.txt", "r", encoding="ISO-8859-1") as f:
            content = f.read()

    lines = content.strip().split("\n\n")  # Split by empty lines (paragraphs)

    topics = []
    for paragraph in lines:
        first_line = paragraph.strip().split("\n")[0]  # Take the first line
        topics.append(first_line.strip())

    return topics

# ✅ Load blog topics once at startup
blog_topics = load_blog_topics()

if not blog_topics:
    raise ValueError("❌ Error: No topics found! Make sure 'blog_posts1.txt' is not empty.")

# ✅ Load sentence transformer model once at startup
model = SentenceTransformer("all-MiniLM-L6-v2")
topic_embeddings = model.encode(blog_topics, convert_to_tensor=True)

@app.route("/", methods=["POST"])
def chatbot_response():
    data = request.json
    user_message = data.get("userMessage", "")
    return jsonify({"response": f"Received: {user_message}"})

    # ✅ Encode user query
    query_embedding = model.encode(user_query, convert_to_tensor=True)

    # ✅ Compute similarity scores
    similarity_scores = util.pytorch_cos_sim(query_embedding, topic_embeddings)

    # ✅ Find the most relevant topic
    best_match_idx = similarity_scores.argmax().item()
    best_match = blog_topics[best_match_idx]

    return jsonify({"response": best_match})

if __name__ == '__main__':
    app.run(debug=True)
