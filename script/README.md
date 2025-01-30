
# Cybersecurity News Scraper

## Overview

This project consists of web scrapers designed to collect and process articles from various cybersecurity news sources. The scrapers use natural language processing (NLP) techniques to classify and summarize the content of the articles. The collected data is then sent to a Flask server for storage and further analysis.

### Key Technologies Used

- **Python**: The main programming language used for developing the scrapers.
- **aiohttp**: For asynchronous HTTP requests.
- **requests**: For making HTTP requests.
- **BeautifulSoup**: For parsing HTML content.
- **transformers**: For NLP tasks, specifically for summarization using pre-trained models.
- **torch**: For running the NLP models.
- **Flask**: The backend server where the collected data is stored.
- **Logging**: For tracking the activities and errors during the scraping process.

## Installation

To set up and run this project, follow the steps below:

1. **Clone the Repository**

   ```sh
   git clone https://github.com/Piya-Boy/Security-News-Analysis-Dashboard.git
   cd script
   ```

2. **Create a Virtual Environment**

   It's recommended to use a virtual environment to manage dependencies.

   - **Windows**:
     ```sh
     python -m venv venv
     venv\Scripts\activate
     ```
   
   - **macOS/Linux**:
     ```sh
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install Dependencies**

   Install the required packages using `pip` and the `requirements.txt` file.

   ```sh
   pip install -r requirements.txt
   ```

4. **Prepare Configuration**

   Ensure that you have an `attack_types.json` file in the root directory. This file contains the keywords for classifying the content.

   Example content of `attack_types.json`:
   ```json


   {
       "ransomware": ["ransomware", "ransom", "encryption attack", "decrypt key"],
       "malware": ["malware", "virus", "trojan", "worm"],
       "phishing": ["phishing", "spear phishing", "social engineering"],
       "data breach": ["data breach", "leak", "exposed data"],
       "ddos": ["ddos", "denial of service", "traffic flood"],
       "vulnerability": ["vulnerability", "exploit", "zero-day", "security flaw"]
   }
   ```

## Usage

1. **Run the Scrapers**

   To start the scraping process, run the `main.py` script. This script initializes and runs all the scrapers sequentially.

   ```sh
   python main.py
   ```

   The `main.py` script will output the status of each scraper, indicating which source is currently being processed and whether the process is successful or if any errors occurred.

2. **Check the Logs**

   The logs are saved in `scraper.log` for tracking the activities and any errors that occur during the scraping process.

3. **Access the Collected Data**

   The collected data is sent to a Flask server specified in the configuration. You can access and analyze the data from there.

## Contributing

If you would like to contribute to this project, please fork the repository and submit a pull request with your changes. Make sure to follow the coding standards and include appropriate tests.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
