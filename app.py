import os
from flask import Flask, render_template, request
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from mistralai.client import MistralClient

app = Flask(__name__)

# Load environment variables and handle API key
load_dotenv()
api_key = os.getenv("MISTRAL_API_KEY")
if not api_key:
    api_key = input("API Key not found in .env. Please enter your MISTRAL_API_KEY: ")
    if not api_key:
        raise ValueError("API key is required to proceed.")
client = MistralClient(api_key=api_key)

def extract_article_text(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        article_text = ' '.join([para.get_text() for para in paragraphs])
        if len(article_text) < 50:
            raise ValueError("Extracted text is too short to summarize")
        return article_text
    except requests.RequestException as e:
        raise Exception(f"Error fetching URL: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error during extraction: {str(e)}")

def summarize_text(text, max_length, language):
    try:
        if len(text) < 50:
            raise ValueError("Input is too short to summarize")
        prompt = f"Summarize the following text in approximately {max_length} words in {language}: {text}"
        response = client.chat(
            model="mistral-large",
            messages=[{"role": "user", "content": prompt}]
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except ValueError as e:
        raise Exception(str(e))
    except Exception as e:
        raise Exception(f"Error generating summary: {str(e)}")

@app.route("/", methods=["GET", "POST"])
def index():
    summary = None
    if request.method == "POST":
        try:
            input_type = request.form.get("input_type")
            max_length = int(request.form.get("max_length", 100))
            language = request.form.get("language", "English")
            if input_type == "text":
                text = request.form.get("text_input", "").strip()
            elif input_type == "url":
                url = request.form.get("url_input", "").strip()
                text = extract_article_text(url)
            else:
                text = ""
            if text:
                summary = summarize_text(text, max_length, language)
        except Exception as e:
            summary = f"Error: {str(e)}"
    return render_template("index.html", summary=summary)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)