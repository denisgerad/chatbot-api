import os
from flask import Flask, request, jsonify
import json
import re
from transformers import pipeline
from flask_cors import CORS

app = Flask(__name__)
# Allow requests from your Blogger site
CORS(app, resources={r"/chatbot/*": {"origins": "https://goddesign14b.blogspot.com"}})

# Load summarization model (Force CPU to avoid CUDA issues)
summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device=-1)

# Get the absolute path for the file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  
FILE_PATH = os.path.join(BASE_DIR, "blog.txt")  

# Function to load and split text into sections
def load_text_sections():
    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            text = f.read().strip()
    except UnicodeDecodeError:
        with open(FILE_PATH, "r", encoding="ISO-8859-1") as f:
            text = f.read().strip()

    sections = {}
    current_section = None
    section_content = []
    headers_list = []

    # Improved regex to detect headers (Handles numbers, punctuation, etc.)
    header_pattern = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\s\-\:\.\,\!\?]+$")

    for line in text.split("\n"):
        line = line.strip()
        if header_pattern.match(line):  # If line matches a header pattern
            headers_list.append(line)  # Store headers for listing posts
            if current_section:
                sections[current_section] = " ".join(section_content).strip()
                section_content = []
            current_section = line  # New section starts
        elif current_section:
            section_content.append(line)

    # Store last section
    if current_section and section_content:
        sections[current_section] = " ".join(section_content).strip()

    return sections, headers_list

# Load the blog content
text_sections, headers_list = load_text_sections()

# Function to process user query
def process_query(query):
    query = query.lower()

    # Handle list posts and topics request
    if "list posts" in query or "list topics" in query:
        return "**Available Posts:**\n" + "\n".join(headers_list)

    # Handle latest post request
    if "latest post" in query:
        return f"**Latest Post:** {headers_list[-1]}" if headers_list else "No posts available."

    # Find matching section for content summary
    for section in text_sections:
        if section.lower() in query:  # Match section name in query
            content = text_sections[section]

            # Limit input length to avoid model errors
            max_input_tokens = 512
            content_tokens = content.split()[:max_input_tokens]  # Limit input to 512 tokens
            content = " ".join(content_tokens)

            # Adjust summary length based on content size
            input_length = len(content.split())
            max_length = min(int(0.5 * input_length), 200)
            min_length = min(int(0.2 * input_length), max_length - 10)  # Ensure min_length < max_length

            # Summarize and return
            summary = summarizer(content, max_length=max_length, min_length=min_length)[0]["summary_text"]
            return f"**{section} Summary:**\n{summary}"

    return "Section not found. Please check your query."

# Chatbot route for handling POST requests
@app.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.json
    user_query = data.get("query", "").strip().lower()

    # Response logic based on the user query
    if user_query in ["hi", "hello"]:
        return jsonify({"response": "Hi, How may I help you?"})

    if user_query in ["thank you", "thanks"]:
        return jsonify({"response": "You're welcome! If you have any suggestions or comments, please feel free to share."})

    # List posts
    if "list posts" in user_query or "list topics" in user_query:
        return jsonify({"response": "**Available Posts:**\n" + "\n".join(headers_list)})

    # Latest post
    if "latest post" in user_query:
        return jsonify({"response": f"**Latest Post:** {headers_list[-1]}" if headers_list else "No posts available."})

    # Overview or summary of blog or specific topic
    if "overview" in user_query or "summary" in user_query or "explain" in user_query:
        if "blog" in user_query:
            return jsonify({"response": text_sections.get("Blog Overview", "No overview available.")})
        else:
            matched_topic = next((topic for topic in headers_list if any(word in topic.lower() for word in user_query.split())), None)
            if matched_topic:
                return jsonify({"response": text_sections.get(matched_topic, "No content found.")})
            return jsonify({"response": "No matching overview found."})

    # Handle feedback or correction
    return jsonify({"response": process_query(user_query)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    #app.run(host="0.0.0.0", port=port)
