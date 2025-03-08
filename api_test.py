"""
import requests

url = "https://chatbot-api-uqqf.onrender.com/chatbot"
response = requests.get(url)

data = {"message": "Hello, chatbot!"}  # Sample data

response = requests.post(url, json=data)  # Use POST instead of GET

print("Status Code:", response.status_code)
print("Response:", response.text)
"""
"""
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def hello():
    return "Hello, World!"

if __name__ == '__main__':
    app.run(debug=True)
"""
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/chatbot/*": {"origins": "https://chatbot-api-uqqf.onrender.com/chatbot"}})

@app.route("/chatbot")
def get_data():
    return {"message": "List topics"}

if __name__ == '__main__':
    app.run(debug=True)