from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)
CORS(app, resources={r"/chatbot": {"origins": "https://goddesign14b.blogspot.com"}})

# Load chatbot model
model = SentenceTransformer("all-MiniLM-L6-v2")
blog_topics = ["Introduction", "Exploring faith and science", "COSMOS", "The Garden of Eden"]
topic_embeddings = model.encode(blog_topics, convert_to_tensor=True)

@app.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.json
    user_query = data.get("query", "")

    if not user_query:
        return jsonify({"error": "No query provided"}), 400

    query_embedding = model.encode(user_query, convert_to_tensor=True)
    similarity_scores = util.pytorch_cos_sim(query_embedding, topic_embeddings)
    best_match_idx = similarity_scores.argmax().item()
    best_match = blog_topics[best_match_idx]

    return jsonify({"response": best_match})

if __name__ == "__main__":
    port = 5000
    app.run(host="0.0.0.0", port=port)
