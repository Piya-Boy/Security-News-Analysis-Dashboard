import asyncio
from .bleepingcomputer import BleepingComputerScraper
from .cyberscoop import CyberscoopScraper
from .krebsonsecurity import KrebsonSecurityScraper
from .threatpost import ThreatPostScraper

__all__ = [
    "BleepingComputerScraper",
    "KrebsonSecurityScraper",
    "ThreatPostScraper",
    "CyberscoopScraper"
]

async def run_scrapers():
    # Initialize the scrapers
    scrapers = [
        BleepingComputerScraper(),
        CyberscoopScraper(),
        KrebsonSecurityScraper(),
        ThreatPostScraper()
    ]

    # Run the scrapers one by one and show which one is currently working
    for scraper in scrapers:
        print(f"Starting scraper for {scraper.config.SOURCE}...")
        try:
            await scraper.run(scraper.config.SOURCE)  # Assuming each scraper has an async 'run' method
            print(f"Scraper {scraper.config.SOURCE} completed successfully")
        except Exception as e:
            print(f"Scraper {scraper.config.SOURCE} failed with exception: {e}")

if __name__ == "__main__":
    asyncio.run(run_scrapers())