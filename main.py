import json
import scraper

if __name__ == "__main__":
    scraper = scraper.Scraper()
    
    tweet_id = "1823923769183772993"
    response = scraper.call(tweet_id)
    analysis = scraper.analyze(tweet_id)

    print(json.dumps(analysis, indent=4))