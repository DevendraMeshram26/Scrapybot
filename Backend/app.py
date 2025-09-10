from flask import Flask, request, jsonify, send_from_directory, session
from flask_session import Session
import os
from selenium_scraper import scrape_data
import requests
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')

# Configure Flask-Session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_session')
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

# Initialize Flask-Session
Session(app)

# Make sure session directory exists
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

LLAMA_API_URL = os.getenv('LLAMA_API_URL')
API_KEY = os.getenv('API_KEY')

if not all([LLAMA_API_URL, API_KEY]):
    raise ValueError("Missing API configuration")

@app.route('/')
def serve_frontend():
    return app.send_static_file('index.html')

def get_answer_from_llama3(query, context):
    messages = [
        {
            "role": "system",
            "content": f"""You are a knowledgeable assistant that provides accurate information based on webpage content.

Context from the webpage:
{context}

Follow these guidelines strictly:
1. ONLY answer using information from the provided context
2. If you can't find relevant information in the context, say "I cannot answer this question based on the provided webpage content"
3. If the context seems irrelevant or unclear, say "The webpage content may not be relevant to your question"
4. When quoting information, mention the specific section (H1, P, LI, etc.)
5. Keep answers clear and well-structured
6. If the question is about numbers, dates, or specific facts, only state them if they appear exactly in the context"""
        },
        {"role": "user", "content": f"Based on the webpage content, {query}"}
    ]

    try:
        response = requests.post(
            LLAMA_API_URL,
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": "llama3-8b-8192",
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 200,
                "top_p": 0.9
            },
            timeout=30
        )
        response.raise_for_status()
        
        return response.json()["choices"][0]["message"]["content"]
    except requests.RequestException as e:
        raise Exception(f"LLaMA API error: {str(e)}")

def get_website_summary(context):
    messages = [
        {
            "role": "system",
            "content": f"""You are a helpful assistant that summarizes webpage content.
            
Context from the webpage:
{context}

Provide a brief 2-3 sentence summary of what this website or webpage is about.
Include the main topic and key points only."""
        },
        {"role": "user", "content": "Please summarize this webpage content."}
    ]

    try:
        response = requests.post(
            LLAMA_API_URL,
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": "llama3-8b-8192",
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 150,
                "top_p": 0.9
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.RequestException as e:
        raise Exception(f"LLaMA API error: {str(e)}")

def truncate_content(text, max_chars=12000):
    """Truncate text while preserving complete sentences"""
    if len(text) <= max_chars:
        return text
        
    # Find the last period before max_chars
    truncated = text[:max_chars]
    last_period = truncated.rfind('.')
    
    if last_period != -1:
        return text[:last_period + 1]
    return truncated

@app.route('/scrape', methods=['POST'])
def scrape_url():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        print("Starting scraping...")
        scraped_data = scrape_data(url)
        print(f"Scraping completed. Data length: {len(scraped_data) if scraped_data else 0}")
        
        if not scraped_data or scraped_data.startswith("Error"):
            return jsonify({'error': 'Could not extract content from the provided URL'}), 400

        truncated_data = truncate_content(scraped_data)
        
        print("Getting website summary...")
        summary = get_website_summary(truncated_data)
        print("Summary generated")
        
        # Store in session
        session['scraped_data'] = truncated_data
        session['current_url'] = url
        session.modified = True
        
        return jsonify({
            'message': 'Website scraped successfully!',
            'summary': summary,
            'source_url': url,
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    query = data.get('query')
    
    if not query:
        return jsonify({'error': 'No question provided'}), 400

    scraped_data = session.get('scraped_data')
    current_url = session.get('current_url')
    
    if not scraped_data:
        return jsonify({'error': 'Please scrape a website first'}), 400

    try:
        truncated_data = truncate_content(scraped_data)
        answer = get_answer_from_llama3(query, truncated_data)
        
        return jsonify({
            'answer': answer,
            'source_url': current_url,
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(Exception)
def handle_error(error):
    print(f"Error occurred: {str(error)}")  # Add logging
    return jsonify({'error': str(error)}), 500

if __name__ == "__main__":
    app.run(debug=True)
