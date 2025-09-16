# Nova: The Conversational Analytics Bot

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Slack-4A154B?style=for-the-badge&logo=slack&logoColor=white" alt="Slack">
  <img src="https://img.shields.io/badge/Google_Gemini-8E75B7?style=for-the-badge&logo=google-gemini&logoColor=white" alt="Google Gemini">
  <img src="https://img.shields.io/badge/Pytest-0A9B0A?style=for-the-badge&logo=pytest&logoColor=white" alt="Pytest">
</p>

## Overview

Nova is an intelligent, conversational Slack bot that serves as the user-friendly frontend for the Lyra analytics platform. Built with the Python Slack Bolt SDK and powered by Google's Gemini API, Nova understands natural language queries, fetches data from the Lyra backend, and delivers insightful, AI-generated analysis directly to users in Slack. Its modular architecture allows for easy extension and maintenance of its various analytical capabilities.

## Key Features

- **LLM-Powered Command Routing**: Uses Google Gemini for Natural Language Understanding (NLU) to interpret user requests and route them to the correct analytical function.
- **Fact-Grounded AI Generation**: Employs a two-step AI process: first, it fetches structured data from the Lyra API, then it uses that data as context for the LLM to generate a reliable, factual summary.
- **Context-Aware Conversations**: Maintains conversation context within Slack threads, allowing for natural follow-up questions.
- **Modular Architecture**: Each core feature (monthly review, influencer analysis, strategic planning) is encapsulated in its own module for high cohesion and low coupling.
- **Prescriptive Analytics**: Goes beyond reporting by providing strategic budget allocation plans with its "Plan" feature, complete with Excel exports.
- **Comprehensive Test Suite**: Uses `pytest` and mocking to ensure the reliability of each module and its interactions with external APIs.

## Technology Stack

- **Core Framework**: Slack Bolt SDK for Python
- **AI / LLM**: Google Gemini API
- **HTTP Requests**: `requests` library (to communicate with Lyra)
- **Data Handling**: Pandas
- **Excel Generation**: openpyxl
- **Testing**: Pytest, Pytest-Mock

---

## Getting Started

Follow these instructions to set up and run the Nova Slack bot on your local machine using Socket Mode.

### Prerequisites

- Python 3.9+
- `pip` and `venv`
- A Slack workspace where you have permissions to create and install an app.
- The Lyra backend service must be running and accessible.

### 1. Clone the Repository

git clone https://github.com/Arvin-BrandInfluencer/NOVA-Slack.git
cd NOVA-Slack

### 2. Set up a Virtual Environment
For macOS/Linux
python3 -m venv venv
source venv/bin/activate

For Windows
python -m venv venv
.\venv\Scripts\activate

### 3. Install Dependencies

pip install -r requirements.txt

### 4. Configure Your Slack App

Go to api.slack.com/apps and create a new app.
Enable Socket Mode.

Navigate to OAuth & Permissions and add the following Bot Token Scopes:
app_mentions:read
chat:write
commands
files:write
groups:history
im:history
mpim:history
users:read

Install the app to your workspace and copy the Bot User OAuth Token (starts with xoxb-).

Go back to Basic Information, scroll down to App-Level Tokens, and generate a new token with the connections:write scope. Copy this token (starts with xapp-).

### 5. Configure Environment Variables

Create a .env file in the root directory and populate it with your credentials and the URL of your running Lyra backend.

 .env.example

Get this from your Slack App's "OAuth & Permissions" page.
SLACK_BOT_TOKEN="xoxb-your-bot-token"

Generate this from your Slack App's "Basic Information" page under "App-Level Tokens".
SLACK_APP_TOKEN="xapp-your-app-level-token"

Your Google Gemini API Key.
GOOGLE_API_KEY="your-google-api-key"

 The base URL where your Lyra backend service is running.
BASE_API_URL="http://127.0.0.1:10000"

### 6. Run the Application
Once the dependencies are installed and the environment variables are set, you can start the bot.

python main.py
