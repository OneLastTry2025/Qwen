# Qwen Automation and API Server

This project provides a backend server that acts as a robust, automated bridge to the Qwen website. It uses Playwright to manage a persistent, authenticated browser session, allowing you to interact with Qwen's features through a simple API.

## Features

*   **Persistent Browser Session**: Launches a single browser instance on startup and maintains the session, avoiding slow, repeated logins.
*   **Concurrent Request Handling**: Manages a pool of browser tabs to handle multiple API requests simultaneously.
*   **Conversational Context**: Supports continuing existing conversations or starting new ones via a `chat_id`.
*   **Simple REST API**: Exposes a `/chat` endpoint to send prompts and receive responses.
*   **Functional Frontend**: Includes a clean, functional HTML/CSS/JS frontend to interact with the API.
*   **Feature Discovery**: Includes a `feature_finder.py` script to help you explore the Qwen UI and find selectors for new features.

## How It Works

1.  **Authentication (`receive_auth_state.py`):** A one-time setup step where you use a Chrome extension to save your logged-in session from `chat.qwen.ai` into a `storage_state.json` file.
2.  **API Server (`api_server.py`):** A Quart-based asynchronous server that:
    *   Launches a headless Chromium browser on startup.
    *   Loads the session from `storage_state.json`.
    *   Manages a pool of browser pages (tabs) to handle concurrent requests.
    *   Listens for POST requests on `/chat`.
    *   Automates the process of sending the prompt on a page from the pool and scraping the response.
3.  **Frontend (`index.html`):** A simple web interface that communicates with the `/chat` endpoint of the local API server.

## Setup & Usage

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## How to Use

1.  **Capture a HAR file:**
    *   Go to the target website.
    *   Open your browser's Developer Tools (F12 or Ctrl+Shift+I) and go to the "Network" tab.
    *   Check the "Preserve log" box.
    *   Perform the action that triggers the API call you want to mimic (e.g., log in, fetch data).
    *   Right-click on the network log and select "Save all as HAR with content". Save it as `my_api.har`.

2.  **List Available Requests:**
    *   Run the script with the `--list` or `-l` flag to see all captured requests and their indices. You can use `-f` to filter for a specific API path.

    ```bash
    # List all requests
    python -m har_mimic.main my_api.har --list
    
    # List only requests containing "v1/user/profile" in the URL
    python -m har_mimic.main my_api.har -l -f "v1/user/profile" 
    ```
    *   **Example Output:**
        ```
        Available requests in the HAR file:
        [023] GET 200 - https://api.example.com/v1/user/profile
        [024] POST 401 - https://api.example.com/v1/user/settings
        ...
        ```

3.  **Replay a Specific Request:**
    *   Once you've identified the index (e.g., `23`), use the `-i` flag to replay it.

    ```bash
    python -m har_mimic.main my_api.har -i 23
    ```
    *   The script will print the reconstructed request details, the replay status, and the decoded response from the server.

4.  **Generate a cURL Command:**
    *   To get a cURL command for testing in the terminal or sharing, use the `--curl` or `-c` flag.

    ```bash
    python -m har_mimic.main my_api.har -i 23 --curl
    ```
    *   **Example Output:**
        ```
        cURL Command:
        curl 'https://api.example.com/v1/user/profile' -X 'GET' -H 'sec-ch-ua: "Chromium";v="120", "Not?A_Brand";v="8"' -H 'Authorization: Bearer eyJhbGciOi...' ... --cookie 'session_id=abc123xyz' --insecure
        ```