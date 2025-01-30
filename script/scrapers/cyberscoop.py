# Path: scraperss/cyberscoop.py
import aiohttp
import asyncio
import logging
from bs4 import BeautifulSoup
import requests
from config import NewsScraperConfig

class CyberscoopScraper:
    def __init__(self):
        self.config = NewsScraperConfig(source='https://cyberscoop.com/news/threats/cybercrime/')
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

    async def get_article_links(self, soup: BeautifulSoup) -> list:
        # Find the links to the articles within the main div
        article_tags = soup.find_all('a', class_='post-item__title-link')
        links = [tag['href'] for tag in article_tags]
        return links

    async def get_article_details(self, url: str) -> dict:
        # Fetch and process article details
        content = await self.fetch_page(url)
        if not content:
            return None

        try:
            soup = BeautifulSoup(content, 'html.parser')

            # Find the title
            title_tag = soup.find('h1', class_='single-article__title')
            title = title_tag.get_text(strip=True) if title_tag else None

            # Find the date
            date_tag = soup.find('p', class_='single-article__date')
            date = date_tag.get_text(strip=True) if date_tag else None

            # Find the content
            content_tag = soup.find('div', class_='has-drop-cap')
            content = content_tag.get_text(strip=True) if content_tag else None

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
        tasks = []
        for i in range(0, len(links), self.config.BATCH_SIZE):
            batch = links[i:i + self.config.BATCH_SIZE]
            tasks = [self.get_article_details(link) for link in batch]
            results = await asyncio.gather(*tasks)
            valid_results = [r for r in results if r is not None]
            if valid_results:
                self.config.save_to_flask_server(valid_results, self.processed_titles)
            await asyncio.sleep(1)

    async def fetch_nonce_and_object_id(self, soup):
        """Extracts the nonce and object ID from the HTML content."""
        try:
            button = soup.find('button', class_='js-load-more')
            nonce = button['data-nonce']
            object_id = button['data-object-id']
            return nonce, object_id
        except Exception as e:
            logging.error(f"Error extracting nonce and object ID: {e}")
            return None, None

    async def fetch_more_articles(self, current_page, nonce, object_id):
        """Fetches additional articles via AJAX request."""
        try:
            ajax_url = self.config.SOURCE
            payload = {
                'nonce': nonce,
                'action': 'sng-load-pagination-data',
                'context': 'archive-post-items',
                'wp_template': 'archive-post-items',
                'markup_append_id': 'archive-post-items',
                'page': current_page,
                'posts_per_page': 10,
                'object_id': object_id,
                'object_type': 'term',
            }
            async with self.session.post(ajax_url, data=payload) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logging.error(f"Failed to load more articles: {response.status}")
                    return None
        except Exception as e:
            logging.error(f"Error fetching more articles: {e}")
            return None

    async def run(self, start_url: str):
        await self.init_session()
        try:
            # Step 1: Fetch the initial page to extract nonce and object ID
            initial_page_content = await self.fetch_page(start_url)
            if not initial_page_content:
                logging.error("Failed to fetch the initial page.")
                return

            soup = BeautifulSoup(initial_page_content, 'html.parser')
            nonce, object_id = await self.fetch_nonce_and_object_id(soup)
            if not nonce or not object_id:
                logging.error("Failed to extract nonce or object ID.")
                return

            # Step 2: Collect all article links by simulating "Load more" button clicks
            all_links = set()
            current_page = 1
            while current_page < 10:  # Limit to 10 pages for demonstration purposes
                logging.info(f"Fetching articles from page {current_page}...")
                articles_html = await self.fetch_more_articles(current_page, nonce, object_id)
                if not articles_html:
                    break

                soup = BeautifulSoup(articles_html, 'html.parser')
                links = await self.get_article_links(soup)
                if not links:
                    break
                all_links.update(links)

                next_button = soup.find('button', class_='js-load-more')
                if not next_button:
                    logging.info("No more articles to load.")
                    break

                current_page += 1
                await asyncio.sleep(1)  # Prevent server overload

            # Step 3: Process all collected article links
            logging.info(f"Processing {len(all_links)} articles...")
            await self.process_articles_batch(list(all_links))

            logging.info(f"{self.config.SOURCE} Scraping completed.")
        except Exception as e:
            logging.error(f"Error during scraping: {e}")
        finally:
            await self.close_session()

async def main():
    scraper = CyberscoopScraper()
    await scraper.run(scraper.config.SOURCE)

if __name__ == "__main__":
    asyncio.run(main())