
# 📰 Ai-News-Automation-Bot

A Python-based automation tool that fetches the latest AI news twice daily, summarizes it using the Perplexity API, rates it for small business relevance, and stores the results in Google Sheets.

---

## 📌 Features

- ✅ Scrapes AI news from top tech sites: 
- 🧠 Uses **OPEN AI API** for smart, concise summaries
- 🔍 Rates each news item (1–10) for small business relevance
- 🗓️ Automatically runs twice daily (via [cron-job.org](https://cron-job.org/))
- 📊 Saves news data to **Google Sheets** with:
  - Date
  - Title
  - Summary
  - URL
  - Relevance rating
- 🛠 Built with **Python + CrewAI + Flask**, ready to deploy on **Render** or **Replit**

---


---

## ⚙️ Tech Stack

- **Python 3.10+**
- Crew Ai
- **Flask** (lightweight backend)
- **Open AI API** for AI-powered summarization
- **Google Sheets API** for data storage
- **BeautifulSoup + requests** for scraping
- **Cron-job.org** or **GCP Cloud Scheduler** for scheduling

---

## 🧪 How It Works

1. **Scrape**: Gets latest articles from the web
2. **Summarize**: Calls Perplexity API with article link or content
3. **Rate**: Adds a 1–10 rating based on relevance to small businesses
4. **Save**: Uploads to Google Sheets

---

## 📄 Deployment Options

- 🔸 **Render**: Serverless deployment with CRON setup
- 🔸 **Replit + cron-job.org**:
- 🔐 All secrets handled via environment variables and secure base64-encoded credentials

---

## ✅ To-Do / Future Enhancements

- [ ] Add Telegram/Slack notifications
- [ ] Dashboard to browse recent summaries
- [ ] More granular rating using sentiment/keywords
- [ ] UI for non-dev users

---

---

## 🙋‍♂️ Author

**Muhammad Talha Javed**  
