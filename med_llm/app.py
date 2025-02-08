from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from llm import QA, ConversationBufferMemory

app = Flask(__name__)
# Enable CORS for all routes and origins
CORS(app, resources={r"/*": {"origins": "*", "allow_headers": "*", "methods": ["GET", "POST", "OPTIONS"]}})

# Initialize memory
memory = ConversationBufferMemory()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    question = request.json.get('question')  # Changed from form to json
    response = QA(question, memory)
    return jsonify({'answer': response})

if __name__ == '__main__':
    app.run(debug=True)