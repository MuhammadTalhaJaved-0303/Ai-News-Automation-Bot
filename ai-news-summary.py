import os  
from crewai import Agent, Task, Crew, Process  
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_community.tools import DuckDuckGoSearchResults
from crewai.tools import tool  
import requests
import dotenv
import re 
from duckduckgo_search import DDGS
from datetime import datetime, date
from typing import List, Optional

import gspread
from google.oauth2.service_account import Credentials
from pydantic import BaseModel, Field

# Load .env file
dotenv.load_dotenv()

# Slack webhook URL
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# Google Sheet URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1YEiQga4bLDakihGTAp3fGoA8E4OWgvYJ_Eas3SMYEZs/edit?gid=0#gid=0"

# ------------------------- Pydantic Models for Structured Output -------------------------

class NewsItem(BaseModel):
    """A single news item."""
    title: str = Field(description="The title of the news article.")
    summary: str = Field(description="A concise summary of the news article, up to 5 lines long.")
    url: str = Field(description="The URL of the news article.")
    publication_date: date = Field(description="The publication date of the news article in YYYY-MM-DD format.")
    rating: Optional[int] = Field(description="A rating of the news article's relevance and importance from 1 to 10, where 10 is most important.", default=None)

class NewsReport(BaseModel):
    """A report containing a list of news items."""
    news_items: List[NewsItem] = Field(description="A list of news items found.")

# ------------------------- Slack Formatting + Sending -------------------------

def send_to_slack(message):
    """Send a message to Slack using the webhook URL"""
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json={"text": message})
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error sending message to Slack: {e}")
        return False

# ------------------------- DuckDuckGo Search Tool -------------------------

@tool("search news")
def search_news(query: str) -> str:
    """Search tool to get up-to-date news articles from the past day based on the query."""
    results = DDGS().news(keywords=query, safesearch="off", timelimit="d")
    return results

# ------------------------- Agent + Task Setup -------------------------

keywords = "AI, OpenAI, LLM, AI Agents"

researcher = Agent(  
    role="Senior News Researcher",  
    goal=f"Find the most relevant and recent news articles related to these keywords: {keywords}.",  
    backstory="""You are an expert technology news researcher with a talent for finding the most impactful stories. 
    Your goal is to use the 'search_news' tool to find key news items. 
    Focus on quality over quantity, ensuring each item is recent and highly relevant.""",  
    verbose=True,  
    model="gpt-4o-mini",
    tools=[search_news],  
)

analyst = Agent(
    role="Senior News Analyst",
    goal=f"Analyze each news article and provide a rating from 1 to 10 based on its relevance to the keywords: {keywords}, significance, and novelty.",
    backstory="""You are a seasoned technology analyst with a sharp eye for what's truly important in the AI space. 
    You can quickly assess the significance of a news story and assign it a clear, numerical rating from 1 to 10.
    Your ratings help prioritize what's most important to read.""",
    verbose=True,
    model="gpt-4o-mini",
    tools=[]
)

research_task = Task(  
    description=f"""Research the latest news, updates, and significant developments related to: {keywords}.
    Your final report should contain news items.
    Prioritize the most significant news from authoritative sources like company blogs, reputable tech news sites, and official announcements.
    Exclude non-English and duplicate articles.""",
    expected_output="""A JSON object adhering to the NewsReport schema.
    This object must contain a list of news items.
    Each item needs a title, a summary (up to 5 lines), a URL, and a publication date.""",
    agent=researcher,
    output_pydantic=NewsReport
)

analysis_task = Task(  
    description=f"""Analyze the list of news articles provided. For each article, provide a rating from 1 to 10.
    The rating should be based on:
    1.  Relevance to the keywords: {keywords}.
    2.  The significance of the news (e.g., major product launch, breakthrough research).
    3.  Novelty (is this new information or a rehash of old news?).
    
    Your final output should be the same list of news items, but with the rating included for each.""",
    expected_output="""A JSON object adhering to the NewsReport schema.
    This object must contain the same list of news items provided as input, but with a 'rating' field (an integer from 1 to 10) added to each item.""",
    agent=analyst,
    output_pydantic=NewsReport
)

news_crew = Crew(  
    agents=[researcher, analyst],  
    tasks=[research_task, analysis_task],  
    process=Process.sequential,  
    verbose=True,  
)

# ------------------------- Google Sheets Upload Function -------------------------

def get_existing_urls_from_sheet():
    """Fetches all existing URLs from the Google Sheet to avoid duplicates."""
    print("Fetching existing URLs from Google Sheet to prevent duplicates...")
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        print("Loading credentials...")
        creds = Credentials.from_service_account_file("ai-news-sheet-ea23a0541b63.json", scopes=scopes)
        print("Authorizing client...")
        client = gspread.authorize(creds)

        print("Opening sheet by URL...")
        sheet = client.open_by_url(SHEET_URL)
        worksheet = sheet.sheet1
        
        # URLs are in the 4th column
        print("Fetching URL column...")
        urls = set(worksheet.col_values(4))
        print(f"Found {len(urls)} existing URLs in the sheet.")
        return urls
    except Exception as e:
        print(f"An exception occurred in get_existing_urls_from_sheet: {e}")
        import traceback
        traceback.print_exc()
        return set()

def append_to_google_sheet(data_rows):
    """Appends data rows to the specified Google Sheet."""
    print(f"Attempting to upload {len(data_rows)} rows to Google Sheets.")
    if not data_rows:
        print("No data to upload. Skipping Google Sheets update.")
        return

    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file("ai-news-sheet-ea23a0541b63.json", scopes=scopes)
        client = gspread.authorize(creds)

        sheet = client.open_by_url(SHEET_URL)
        worksheet = sheet.sheet1

        print(f"Appending {len(data_rows)} rows to the worksheet...")
        for row in data_rows:
            print(f"  > Appending row: {row[:2]}...") # Log first two elements for brevity
            worksheet.append_row(row)

        print("Successfully uploaded to Google Sheets.")
    except Exception as e:
        print(f"Error uploading to Google Sheets: {e}")

# ------------------------- Execute Full Workflow -------------------------

if __name__ == "__main__":
    crew_output = news_crew.kickoff()
    result = crew_output.pydantic

    if result and result.news_items:
        print(f"Successfully found and analyzed {len(result.news_items)} news items.")

        existing_urls = get_existing_urls_from_sheet()
        
        new_items = [item for item in result.news_items if item.url not in existing_urls]

        if not new_items:
            print("No new news items to add. All fetched articles are already in the sheet.")
        else:
            print(f"Found {len(new_items)} new news items to be added.")
            # Google Sheets
            sheet_rows = []
            for item in new_items:
                sheet_rows.append([item.publication_date.strftime('%Y-%m-%d'), item.title, item.summary, item.url, item.rating])
            
            append_to_google_sheet(sheet_rows)

            # Slack
            slack_message = "*AI News Summary*\n\n"
            for item in new_items:
                slack_message += f"*Title:* {item.title}\n"
                slack_message += f"*Summary:* {item.summary}\n"
                slack_message += f"Rating: {item.rating}/10\n"
                slack_message += f"<{item.url}|Read More>  |  Published on: {item.publication_date.strftime('%Y-%m-%d')}\n"
                slack_message += "---\n"
            
            if send_to_slack(slack_message):
                print("Successfully sent to Slack!")
            else:
                print("Failed to send to Slack")
    else:
        print("No news items found by the crew.")
        if crew_output:
            print("Raw output from crew:", crew_output.raw)
            
