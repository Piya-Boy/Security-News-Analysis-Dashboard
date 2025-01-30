import random
import json
import requests
import logging
from transformers import pipeline
import os

# Configure logging
logging.basicConfig(
    filename='scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# User-Agent list
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.198 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.198 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.198 Safari/537.36",
]

class NewsScraperConfig:
    BATCH_SIZE = 5
    TIMEOUT = 30
    FLASK_SERVER_URL = "https://piyamianglae.pythonanywhere.com/data"

    def __init__(self, source):
        self.SOURCE = source
        self.headers = {
            "User-Agent": random.choice(USER_AGENTS)
        }
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

        attack_types_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'attack_types.json'))
        with open(attack_types_path, 'r') as f:
            self.attack_types = json.load(f)

    def classify_content(self, content: str) -> str:
        """Classify the content into attack types based on keywords."""
        content_lower = content.lower()
        for category, keywords in self.attack_types.items():
            if any(keyword in content_lower for keyword in keywords):
                return category
        return None

    async def summarize_content(self, content: str) -> str:
        """Summarize the given content."""
        try:
            if len(content) > 1024:
                content = content[:1024]
            summary = self.summarizer(content, max_length=130, min_length=50, do_sample=False)
            return summary[0]["summary_text"]
        except Exception as e:
            print(f"Summarization failed: {e}")
            return "Could not summarize content."

    def save_to_flask_server(self, articles: list, processed_titles: set):
        """
        Save a list of articles to the Flask server.
        :param articles: List of article dictionaries.
        :param processed_titles: Set of already processed article titles.
        """
        if not articles:
            return
        for article in articles:
            if article and article['Title'] not in processed_titles:
                try:
                    response = requests.post(self.FLASK_SERVER_URL, json=article)
                    if response.status_code == 201:
                        processed_titles.add(article['Title'])
                    elif response.status_code == 409:
                        logging.warning(f"Conflict error saving article to Flask server: {response.status_code}")
                    else:
                        logging.error(f"Error saving article to Flask server: {response.status_code}")
                except Exception as e:
                    logging.error(f"Failed to connect to Flask server: {e}")