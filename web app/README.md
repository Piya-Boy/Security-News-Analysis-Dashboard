
# Cybersecurity News Scraper & Security News Analysis Dashboard

## Overview
**Security News Analysis Dashboard**: A Streamlit-based dashboard for analyzing and visualizing cybersecurity news articles. It fetches data from the Flask API and provides interactive insights into trends and distributions of cybersecurity threats.

---

## Key Technologies Used
### Security News Analysis Dashboard
- **Streamlit**: For building the interactive web dashboard.
- **Pandas**: For data manipulation and analysis.
- **Plotly**: For creating interactive visualizations.
- **NLTK**: For natural language processing tasks (e.g., tokenization, stopwords).
- **Requests**: For fetching data from the API.
- **Datetime**: For handling date and time operations.

---

## Installation

To set up and run this project, follow the steps below:

1. **Clone the Repository**

   ```sh
   git clone https://github.com/Piya-Boy/Security-News-Analysis-Dashboard.git
   cd web app
   ```

2. **Create a Virtual Environment**

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

   ```sh
   pip install -r requirements.txt
   ```


---

## Usage
### Security News Analysis Dashboard
1. **Run the Dashboard**
   ```sh
   streamlit run app.py
   ```

2. **Filters**:
   - Use the sidebar to filter data by **Month**, **Year**, and **Attack Type**.
   - The dashboard dynamically updates based on the selected filters.

3. **Visualizations**:
   - **Attack Types Trend**: Shows the trend of attack types over time.
   - **Attack Types Distribution**: Displays the distribution of attack types.
   - **Yearly Attacks**: Visualizes the number of attacks per year.

4. **Download Data**:
   - Use the sidebar to download the dataset in CSV, JSON, or Excel format.

---

## API Integration

The dashboard fetches data from an API hosted at `https://piyamianglae.pythonanywhere.com/data`. Ensure the API is accessible and returns data in the expected format.

---

## Contributing

If you would like to contribute to this project, please fork the repository and submit a pull request with your changes. Make sure to follow the coding standards and include appropriate tests.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## Screenshots

![Dashboard Screenshot](https://img5.pic.in.th/file/secure-sv1/logos02edf0d066b19226.png)  
*Example of the Security News Analysis Dashboard.*

---
