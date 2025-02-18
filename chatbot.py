import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import uuid
import time

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/chat": {"origins": "*", "allow_headers": ["Content-Type"]}})

# Set API Key for Gemini
GOOGLE_API_KEY = 'AIzaSyA1Rnv5FsdF5Ex77cJEbg_-cCA7tMcFDt4'
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize the model and chat
model = genai.GenerativeModel('gemini-pro')
app.chat = model.start_chat(history=[])

# Define chatbot context
CONTEXT = """You are NOVA, a proactive and adaptable customer service agent for Nexobotics. Your role is to guide users, particularly business owners, on how Nexobotics can transform their customer service by handling all customer interactions efficiently and attentively while maximizing customer satisfaction..."""  # (Context remains the same)

# Google Sheets Authentication
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Open the Google Sheet
sheet = client.open("Chatbot Conversations").worksheet("Chats")  # Replace with your sheet name

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    data = request.json
    message = data.get("message")
    session_id = data.get("sessionId")  # Get session ID from frontend

    if not message:
        return jsonify({'error': 'Message is required'}), 400

    # Generate a new session ID if it's not provided
    if not session_id:
        session_id = str(uuid.uuid4())

    try:
        # Generate AI response
        response = app.chat.send_message(f"{CONTEXT}\nUser: {message}")
        ai_response = response.text

        # Timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

        # Append to Google Sheets
        sheet.append_row([session_id, message, ai_response, timestamp])

        return jsonify({'response': ai_response, 'sessionId': session_id})

    except Exception as e:
        print(f"Error processing message: {str(e)}")  # For debugging
        return jsonify({'error': 'An error occurred processing your request'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))  # Render uses the PORT environment variable
    app.run(host='0.0.0.0', port=port)
