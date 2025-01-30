
Here is the complete content in markdown format:

# Flask Article Management API

## Overview

The provided code sets up a Flask web server that handles storing and retrieving articles in a JSON file (`db.json`). The server has two endpoints: one for retrieving articles and another for adding new ones.

## Installation and Usage

To set up and run this project, follow the steps below:

## 1. Installation
  

1.  **Clone the Repository**
```sh
git clone https://github.com/Piya-Boy/Security-News-Analysis-Dashboard.git
cd server
```
2.  **Create a Virtual Environment**

  

-  **Windows**:

```sh
python -m venv venv
venv\Scripts\activate
```
-  **macOS/Linux**:
```sh
python3 -m venv venv
source venv/bin/activate
```
3. **Install Dependencies**
   Install the required packages using `pip` and the `requirements.txt` file.
   ```sh
   pip install -r requirements.txt
   ```

### 2. Usage

1. **Create the `db.json` file**
   Ensure that the `db.json` file is created in the root directory. This file will store the articles.
   ```json
   {
       "articles": []
   }
   ```

2. **Run the Flask Application**
   To start the Flask application, run the following command:
   ```sh
   python app.py
   ```

3. **Access the Endpoints**
   - **GET /data**: Retrieve a list of articles.
     ```sh
     curl -X GET http://127.0.0.1:5000/data
     ```
   - **POST /data**: Add a new article by sending a JSON payload.
     ```sh
     curl -X POST -H "Content-Type: application/json" -d '{""}' http://127.0.0.1:5000/data
     ```
