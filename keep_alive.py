from flask import Flask
from ai_news_summary import main  # This is your main logic

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ AI News Bot is Live."

@app.route('/run')
def run():
    main()
    return "✅ News fetched and sent."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
