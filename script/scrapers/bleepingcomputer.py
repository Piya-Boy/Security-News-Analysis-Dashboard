# Path: scrapers/bleepingcomputer.py
import aiohttp
import asyncio
import logging
from bs4 import BeautifulSoup
from config import NewsScraperConfig
import requests
class BleepingComputerScraper:
    def __init__(self):
        self.config = NewsScraperConfig(source='https://www.bleepingcomputer.com/news/security')
        self.session = None
        self.processed_titles = set()
        self.init_processed_titles()

    def init_processed_titles(self):
        # Fetch existing articles to avoid reprocessing
        response = requests.get(self.config.FLASK_SERVER_URL)
        if response.status_code == 200:
            articles = response.json()
            if isinstance(articles, list):
                self.processed_titles = {article['Title'] for article in articles}
            else:
                logging.error("Unexpected data format: articles is not a list.")
        else:
            logging.error(f"Error fetching initial data from Flask server: {response.status_code}")

    async def init_session(self):
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=self.config.TIMEOUT)
            self.session = aiohttp.ClientSession(timeout=timeout)

    async def close_session(self):
        if self.session:
            await self.session.close()

    async def fetch_page(self, url: str, retries: int = 3) -> str:
        # Fetch page content with retries
        for attempt in range(retries):
            try:
                async with self.session.get(url, headers=self.config.headers) as response:
                    if response.status == 200:
                        return await response.text()
                    await asyncio.sleep(1)
            except Exception as e:
                logging.error(f"Error fetching {url}: {e}")
                if attempt == retries - 1:
                    return None
                await asyncio.sleep(1)
        return None

    async def get_article_links(self, url: str) -> list:
        # Extract article links from the main page
        content = await self.fetch_page(url)
        if not content:
            return []
        soup = BeautifulSoup(content, 'html.parser')
        return [a['href'] for a in soup.select('ul#bc-home-news-main-wrap li h4 a')]

    async def get_article_details(self, url: str) -> dict:
        # Fetch and process article details
        content = await self.fetch_page(url)
        if not content:
            return None

        try:
            soup = BeautifulSoup(content, 'html.parser')
            title = soup.find('h1').text.strip() if soup.find('h1') else ""
            if title in self.processed_titles:
                return None
            date = soup.find('li', class_='cz-news-date').text.strip() if soup.find('li', class_='cz-news-date') else ""
            content = ' '.join([p.text for p in soup.select('div.articleBody p')])

            if not all([title, date, content]):
                return None

            category = self.config.classify_content(content)
            if not category:
                return None

            summary = await self.config.summarize_content(content)

            return {
                'Title': title,
                'Date': date,
                'Category': category,
                'Summary': summary,
                'Source': self.config.SOURCE,
            }

        except Exception as e:
            logging.error(f"Error processing {url}: {e}")
            return None

    async def process_articles_batch(self, links: list):
        # Process articles in batches
        tasks = []
        for i in range(0, len(links), self.config.BATCH_SIZE):
            batch = links[i:i + self.config.BATCH_SIZE]
            tasks = [self.get_article_details(link) for link in batch]
            results = await asyncio.gather(*tasks)
            valid_results = [r for r in results if r is not None]
            if valid_results:
                self.config.save_to_flask_server(valid_results, self.processed_titles)
            await asyncio.sleep(1)

    async def run(self, start_url: str, max_pages: int = 1):
        await self.init_session()
        try:
            current_url = start_url
            page_number = 1

            while current_url and page_number <= max_pages:
                logging.info(f"Processing page {page_number}")
                links = await self.get_article_links(current_url)
                if links:
                    await self.process_articles_batch(links)

                content = await self.fetch_page(current_url)
                if not content:
                    break

                soup = BeautifulSoup(content, 'html.parser')
                next_link = soup.find('a', {'aria-label': 'Next Page'})
                current_url = next_link['href'] if next_link else None

                page_number += 1
                await asyncio.sleep(2)

            logging.info(f"{self.config.SOURCE} Scraping completed.")
        except Exception as e:
            logging.error(f"Error during scraping: {e}")
        finally:
            await self.close_session()
        
# async def main():
#     scraper = BleepingComputerScraper()
#     await scraper.run(scraper.config.SOURCE, max_pages=3)

# if __name__ == "__main__":
#     asyncio.run(main())