import os
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv('DEEPSEEK_API_KEY')

# Allow frontend to communicate with backend
app = Flask(__name__)
CORS(app)

DEEPSEEK_API_URL = "https://api.deepseek.ai/v1/completion"

# Route to generate love letter using DeepSeek API
@app.route('/generate-love-letter', methods=['POST'])
def generate_letter():
    data = request.json
    
    # Mandatory parameters
    sender_name = data.get("sender_name").strip()
    receipient_name = data.get("receipient_name").strip()
    confession_type = data.get("confession_type", "").strip().lower()
    length_preference = data.get("length_preference", "").strip().lower()
    
    # Optional parameters
    fav_song = data.get("fav_song")
    meet = data.get("meet")
    relationship_status = data.get("relationship_status")
    time_together = data.get("time_together")
    special_memory = data.get("special_memory")
    love_reasons = data.get("love_reasons")
    favourite_things = data.get("favourite_things")
    
    # Letter mood and tone
    letter_mood = data.get("letter_mood")
    letter_tone = data.get("letter_tone")
    
    # Checking required fields
    if not sender_name or not receipient_name or not confession_type:
        return jsonify({"error": "Missing required fields."}), 400
    
    # Prepare DeepSeek API prompt based on confession_type
    if confession_type == "confessing":
        prompt = f"Write a confession letter from sender: {sender_name} to receipient: {receipient_name} with length preference {length_preference}, {letter_mood} mood and {letter_tone} tone."
    elif confession_type == "professing":
        prompt = f"Write a heartfelt love letter from sender: {sender_name},to receipient: {receipient_name} with length preference {length_preference}, {letter_mood} mood and {letter_tone} tone."
    
    # Add optional parameters to prompt
    if fav_song:
        prompt += f" Include a witty line from the receipient's favourite song: {fav_song}."
    if meet:
        prompt += f" Where they first met: {meet}."
    if relationship_status:
        prompt += f" Relationship status: {relationship_status}."
    if time_together:
        prompt += f" Time together: {time_together}."
    if special_memory:
        prompt += f" A special memory: {special_memory}."
    if love_reasons:
        prompt += f" Reasons you love them: {love_reasons}."
    if favourite_things:
        prompt += f" Mention their favourite things: {favourite_things}."
        
    # Call DeepSeek API
    payload = {
        "mode": "deepseek_chat",
        "message": [{"role": "user", "content": prompt}],
        "temperature": 1.5,
        "max_tokens": 400 if length_preference == 'long' else (200 if length_preference == 'medium' else 100)
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "content-type": "application/json"
    }
    
    # Send request to DeepSeek
    response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers)
    response_data = response.json()
    
    # Extract response from DeepSeek
    if "choices" in response_data and response_data["choices"]:
        letter = response_data["choices"][0]["content"]
        return jsonify({"letter": letter})
    
    return jsonify({"error": "Failed to generate love letter."}), 500

# Export the love letter to a PNG card
@app.route('/export_png', methods=['POST'])
def export_png():
    data = request.json
    letter_text = data.get("letter", "").strip()
    card_choice = data.get("card_choice", "card1").strip()
    
    if not letter_text:
        return jsonify({"error": "Missing love letter content."}), 400

    card_template_path = f"cards/{card_choice}.png"
    
    if not os.path.exists(card_template_path):
        return jsonify({"error": "Selected card template does not exist."}), 400
    
    # Load card template
    image = Image.open(card_template_path)
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except IOError:
        font = ImageFont.load_default()
    
    text_position = (50, 50)
    text_color = (0, 0, 0)
    max_width = image.width - 100
    wrapped_text = wrap_text(letter_text, font, max_width)
    draw.multiline_text(text_position, wrapped_text, font=font, fill=text_color)
    
    output_path = "final_card.png"
    image.save(output_path)
    
    return send_file(output_path, as_attachment=True)

# Function to wrap text based on max width
def wrap_text(text, font, max_width):
    lines = []
    words = text.split()
    while words:
        line = ""
        while words and font.getsize(line + words[0])[0] <= max_width:
            line += words.pop(0) + " "
        lines.append(line)
    return "\n".join(lines)

@app.route('/')
def index():
    return send_file("static/index.html")

# Error handling
@app.errorhandler(404)
def page_not_found(error):
    return jsonify({"error": "Page not found."}), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({"error": "Internal server error."}), 500

# Standard for running Python scripts
if __name__ == "__main__":
    app.run(debug=True)