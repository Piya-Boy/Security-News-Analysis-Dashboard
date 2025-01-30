# Path: scraperss/threatpost.py
import aiohttp
import asyncio
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from config import NewsScraperConfig
import requests
class ThreatPostScraper:
    def __init__(self):
        self.config = NewsScraperConfig(source='https://threatpost.com/category/malware-2/')
        self.session = None
        self.processed_titles = set()
        self.processed_links = set()  # Set to keep track of processed article links
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
        # Find the links to the articles > o-row > c-card__col-title > c-card__title in h2
        article_tags = soup.find_all('h2', class_='c-card__title')
        links = [tag.a.get('href') for tag in article_tags if tag.a and tag.a.get('href')]

        return links

    async def get_article_details(self, url: str) -> dict:
        if url in self.processed_links:
            return None  # Skip if the link has already been processed
        self.processed_links.add(url)  # Mark the link as processed

        content = await self.fetch_page(url)
        if not content:
            return None

        try:
            soup = BeautifulSoup(content, 'html.parser')

            # Find the title
            title_tag = soup.find('h1', class_='c-article__title')
            title = title_tag.get_text(strip=True) if title_tag else None

            # Find the date
            date_tag = soup.find('div', class_='c-article__time').find('time')
            date = date_tag.get_text(strip=True) if date_tag else None
            # convert to datetime object
            try:
                date = datetime.strptime(date, '%B %d, %Y %I:%M %p').strftime('%B %d, %Y')
            except ValueError:
                date = datetime.strptime(date, '%B %d, %Y%I:%M %p').strftime('%B %d, %Y')

            # Find the content
            content_tag = soup.find('div', class_='c-article__content')
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

    async def fetch_more_articles(self, current_page: int) -> str:
        # Fetch more articles through AJAX request
        try:
            payload = {
                'action': 'loadmore',
                'query': '%7B%22category_name%22%3A%22malware-2%22%2C%22error%22%3A%22%22%2C%22m%22%3A%22%22%2C%22p%22%3A0%2C%22post_parent%22%3A%22%22%2C%22subpost%22%3A%22%22%2C%22subpost_id%22%3A%22%22%2C%22attachment%22%3A%22%22%2C%22attachment_id%22%3A0%2C%22name%22%3A%22%22%2C%22pagename%22%3A%22%22%2C%22page_id%22%3A0%2C%22second%22%3A%22%22%2C%22minute%22%3A%22%22%2C%22hour%22%3A%22%22%2C%22day%22%3A0%2C%22monthnum%22%3A0%2C%22year%22%3A0%2C%22w%22%3A0%2C%22tag%22%3A%22%22%2C%22cat%22%3A40931%2C%22tag_id%22%3A%22%22%2C%22author%22%3A%22%22%2C%22author_name%22%3A%22%22%2C%22feed%22%3A%22%22%2C%22tb%22%3A%22%22%2C%22paged%22%3A0%2C%22meta_key%22%3A%22%22%2C%22meta_value%22%3A%22%22%2C%22preview%22%3A%22%22%2C%22s%22%3A%22%22%2C%22sentence%22%3A%22%22%2C%22title%22%3A%22%22%2C%22fields%22%3A%22%22%2C%22menu_order%22%3A%22%22%2C%22embed%22%3A%22%22%2C%22category__in%22%3A%5B%5D%2C%22category__not_in%22%3A%5B%5D%2C%22category__and%22%3A%5B%5D%2C%22post__in%22%3A%5B%5D%2C%22post__not_in%22%3A%5B%5D%2C%22post_name__in%22%3A%5B%5D%2C%22tag__in%22%3A%5B%5D%2C%22tag__not_in%22%3A%5B%5D%2C%22tag__and%22%3A%5B%5D%2C%22tag_slug__in%22%3A%5B%5D%2C%22tag_slug__and%22%3A%5B%5D%2C%22post_parent__in%22%3A%5B%5D%2C%22post_parent__not_in%22%3A%5B%5D%2C%22author__in%22%3A%5B%5D%2C%22author__not_in%22%3A%5B%5D%2C%22search_columns%22%3A%5B%5D%2C%22post_type%22%3A%5B%22post%22%2C%22tp_ebooks%22%2C%22tp_webinars%22%2C%22tp_whitepapers%22%5D%2C%22ignore_sticky_posts%22%3Afalse%2C%22suppress_filters%22%3Afalse%2C%22cache_results%22%3Atrue%2C%22update_post_term_cache%22%3Atrue%2C%22update_menu_item_cache%22%3Afalse%2C%22lazy_load_term_meta%22%3Atrue%2C%22update_post_meta_cache%22%3Atrue%2C%22posts_per_page%22%3A10%2C%22nopaging%22%3Afalse%2C%22comments_per_page%22%3A%2250%22%2C%22no_found_rows%22%3Afalse%2C%22order%22%3A%22DESC%22%7D',
                'page': current_page
            }
            async with self.session.post(self.config.AJAX_URL, data=payload, headers=self.config.headers) as response:
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
            logging.info("Fetching initial page...")
            page_content = await self.fetch_page(start_url)
            if not page_content:
                logging.error("Failed to fetch the initial page.")
                return

            soup = BeautifulSoup(page_content, 'html.parser')
            all_links = set()  # Set to keep track of all fetched links
            current_page = 1

            while current_page < 10:  # Limit to 10 pages for demonstration purposes
                # Fetch article links from the current page
                links = await self.get_article_links(soup)
                new_links = set(links) - all_links  # Filter only new links

                if new_links:
                    logging.info(f"Found new links on page {current_page}: {len(new_links)}")
                    await self.process_articles_batch(list(new_links))
                    all_links.update(new_links)  # Add new links to the set of fetched links
                else:
                    logging.info("No new links found on this page.")

                # Check if there is a "Load more" button
                load_more_button = soup.find('button', id='load_more_archive')
                if load_more_button:
                    logging.info(f"Clicking 'Load more' button (page {current_page})")
                    current_page += 1

                    # Simulate "Load more" button click by sending POST request to AJAX URL
                    page_content = await self.fetch_more_articles(current_page)
                    if not page_content:
                        logging.error("Failed to load the next page.")
                        break
                    soup = BeautifulSoup(page_content, 'html.parser')

                    await asyncio.sleep(1)  # Add delay to avoid being blocked
                else:
                    logging.info("No 'Load more' button found.")
                    break

            logging.info(f"{self.config.SOURCE} Scraping completed.")
        except Exception as e:
            logging.error(f"Error during scraping: {e}")
        finally:
            await self.close_session()

async def main():
    scraper = ThreatPostScraper()
    await scraper.run(scraper.config.SOURCE)

if __name__ == "__main__":
    asyncio.run(main())