import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
import re

# Load the environment variables
load_dotenv()
token = os.getenv("GITHUB_TOKEN")

# Initialize the OpenAI client
endpoint = "https://models.inference.ai.azure.com"
model_name = "gpt-4o"
client = OpenAI(base_url=endpoint, api_key=token)

# Sample product/business data
products = {
    "laptop": {
        "name": "X100 Pro Laptop",
        "price": "$1200",
        "availability": "In stock",
        "features": "16GB RAM, 1TB SSD, Intel i7 Processor"
    },
    "phone": {
        "name": "ZPhone Max",
        "price": "$799",
        "availability": "Limited stock",
        "features": "128GB storage, 12MP Camera, 5G enabled"
    }
}

# Function to detect tone based on the question
def detect_tone(question):
    # Define words associated with certain tones
    empathetic_keywords = ["broken", "problem", "issue", "not working", "delay"]
    urgent_keywords = ["urgent", "immediately", "asap", "help now", "fast", "quick"]

    # Check for keywords in the question to determine tone
    if any(word in question.lower() for word in empathetic_keywords):
        return "empathetic"
    elif any(word in question.lower() for word in urgent_keywords):
        return "urgent"
    else:
        return "helpful"

# Function to get response from GPT-4o model
def ask_customer_support(question, tone="helpful"):
    system_message = "You are a helpful customer support assistant for an e-commerce store."
    
    if tone == "empathetic":
        system_message = "You are an empathetic customer support assistant. Be understanding and kind."
    elif tone == "urgent":
        system_message = "You are an urgent customer support assistant. Respond quickly and decisively."

    # Check if question relates to product data
    product_response = ""
    for product_key, product_info in products.items():
        if re.search(rf'\b{product_key}\b', question.lower()):
            product_response = (f"Our {product_info['name']} is priced at {product_info['price']}. "
                                f"Features: {product_info['features']}. "
                                f"Availability: {product_info['availability']}.")
            break

    # If product data was found, include it in the response
    if product_response:
        question += f"\n\n{product_response}"

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": question}
        ],
        temperature=0.7,
        max_tokens=500,
        model=model_name
    )
    
    return response.choices[0].message.content


# Initialize the Flask app
app = Flask(__name__, template_folder=str(Path(__file__).parent / 'templates'))

# Main route for the UI
@app.route('/')
def home():
    return render_template('index.html')

# API route to get chatbot responses
@app.route('/get_response', methods=['POST'])
def get_bot_response():
    data = request.json
    user_message = data.get("message")
    tone = detect_tone(user_message)
    bot_response = ask_customer_support(user_message, tone)
    return jsonify({"response": bot_response})

if __name__ == '__main__':
    app.run(debug=True)