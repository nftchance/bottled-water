from flask import Flask, request, jsonify

from config import CONFIG
from scraper import Scraper 

app = Flask(__name__)
scraper = Scraper()

@app.route('/')
def analyze_tweet():
    tweet_id = request.args.get('id')
    analyze = request.args.get('analyze', default=False, type=bool)

    if not tweet_id:
        return jsonify({"error": "No tweet ID provided"}), 400

    print(tweet_id)
    
    try:
        result = scraper.call(tweet_id)
        if analyze:
            return scraper.analyze(tweet_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=CONFIG['PORT'])