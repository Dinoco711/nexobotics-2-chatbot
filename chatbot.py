import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from google.oauth2.service_account import Credentials
import gspread
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/chat": {"origins": "*", "allow_headers": ["Content-Type"]}})

# Set Google API Key from environment variable (DO NOT HARD-CODE IT)
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise Exception("GOOGLE_API_KEY is missing from environment variables.")
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize the AI model
model = genai.GenerativeModel('gemini-pro')
app.chat = model.start_chat(history=[])

# Define chatbot context
CONTEXT = """You are NOVA, a proactive and adaptable customer service agent for Nexobotics..."""  # Keep the rest of your context

# Google Sheets setup
SHEET_NAME = "Chatbot Conversations"  # Change to your Google Sheet name
SHEET_TAB_NAME = "Chats"  # Change to your sheet tab name

# Load credentials from environment variable
GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS_JSON')
if not GOOGLE_CREDENTIALS_JSON:
    raise Exception("GOOGLE_CREDENTIALS_JSON is missing from environment variables.")

try:
    credentials_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
except json.JSONDecodeError:
    raise Exception("GOOGLE_CREDENTIALS_JSON is not a valid JSON string.")

# Authenticate with Google Sheets using the service account credentials
try:
    creds = Credentials.from_service_account_info(
        credentials_dict,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    creds.refresh(Request())  # Force authentication refresh
except RefreshError:
    raise Exception("Could not refresh Google API credentials. Check your permissions.")

# Authorize and access the Google Sheet
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).worksheet(SHEET_TAB_NAME)

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    message = request.json.get('message')
    if not message:
        return jsonify({'error': 'Message is required'}), 400

    try:
        # Send the message to the AI model and get the response
        response = app.chat.send_message(f"{CONTEXT}\nUser: {message}")
        
        # Append the conversation (user message and AI response) to Google Sheets
        sheet.append_row([message, response.text])
        
        return jsonify({'response': response.text})
    except Exception as e:
        print(f"Error processing message: {str(e)}")  # For debugging
        return jsonify({'error': 'An error occurred processing your request'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))  # Render uses the PORT environment variable
    app.run(host='0.0.0.0', port=port)
