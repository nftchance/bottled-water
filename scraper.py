import anthropic
import json
import os
import re

from dotenv import load_dotenv
from hashlib import md5
from playwright.sync_api import sync_playwright, PlaywrightContextManager
from urllib.parse import urljoin, urlparse, urlunparse

from config import CONFIG

class Scraper:
    def __init__(self, cache_dir='./cache'):
        self.client = anthropic.Anthropic(api_key=CONFIG['ANTHROPIC_API_KEY'])
        self.xhr_calls = {}
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def _get_cache_path(self, url, suffix=''):
        return os.path.join(self.cache_dir, md5((url + suffix).encode()).hexdigest() + '.json')

    def _cache_exists(self, url, suffix=''):
        return os.path.exists(self._get_cache_path(url, suffix))

    def _read_cache(self, url, suffix=''):
        with open(self._get_cache_path(url, suffix), 'r') as f:
            return json.load(f)

    def _write_cache(self, url, data, suffix=''):
        with open(self._get_cache_path(url, suffix), 'w') as f:
            json.dump(data, f)

    def intercept_route(self, route):
        """intercept all requests and abort blocked ones"""
        if route.request.resource_type in CONFIG['BLOCK_RESOURCE_TYPES']:
            return route.abort()
        if any(key in route.request.url for key in CONFIG['BLOCK_RESOURCE_NAMES']):
            return route.abort()
        return route.continue_()

    def intercept_response(self, response):
        """capture all background requests and save them"""
        if response.request.resource_type == "xhr":
            base_url = response.request.url
            self.xhr_calls[base_url] = response
        return response

    def get_relative_xhr_calls(self, base_url):
        """Get XHR calls relative to the given base URL"""
        relative_calls = {}
        for url, response in self.xhr_calls.items():
            relative_url = url.replace(base_url, '')
            relative_calls[relative_url] = response
        return relative_calls

    def get_url(self, url: str) -> str:
        """
        Format a potentially malformed Twitter URL into the proper format.
        """
        tweet_id_pattern = r'^(\d{10,25})$'
        username_pattern = r'^@?(\w{1,15})$'

        tweet_id_match = re.match(tweet_id_pattern, url)
        if tweet_id_match:
            return f"https://x.com/i/web/status/{tweet_id_match.group(1)}"

        username_match = re.match(username_pattern, url)
        if username_match:
            return f"https://x.com/{username_match.group(1)}"

        parsed_url = urlparse(url)

        if not parsed_url.scheme:
            parsed_url = parsed_url._replace(scheme="https")

        if not parsed_url.netloc or parsed_url.netloc not in ['x.com', 'twitter.com']:
            parsed_url = parsed_url._replace(netloc="x.com")

        if parsed_url.path.startswith('/twitter.com/'):
            parsed_url = parsed_url._replace(path=parsed_url.path.replace('/twitter.com', '', 1))

        if not parsed_url.path.startswith('/'):
            parsed_url = parsed_url._replace(path='/' + parsed_url.path)

        formatted_url = urlunparse(parsed_url)

        return formatted_url

    def get_selector(
        self, 
        pw: PlaywrightContextManager, 
        url: str,
        selector: str
    ):
        """Get the selector from the page using Playwright"""
        browser = pw.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()
        page.route("**/*", self.intercept_route)
        page.on("response", self.intercept_response)
        page.goto(url)
        page.wait_for_selector(selector)

    def tweet(self, url: str) -> dict:
        """
        Scrape a single tweet page for Tweet thread e.g.:
        https://x.com/nftchance/status/1823923769183772993
        Return parent tweet, reply tweets and recommended tweets
        """
        scrape_url = self.get_url(url)
        
        if self._cache_exists(scrape_url):
            print(f"Using cached data for {scrape_url}")
            return self._read_cache(scrape_url)
        
        with sync_playwright() as pw:
            self.get_selector(pw, scrape_url, '[data-testid="tweet"]')
            tweet_calls = [f for f in self.get_relative_xhr_calls(scrape_url).values() if "TweetResultByRestId" in f.url]
            for xhr in tweet_calls:
                data = xhr.json()
                result = data['data']['tweetResult']['result']
                self._write_cache(scrape_url, result)
                return result

    def profile(self, url: str) -> dict:
        """
        Scrape a single profile page for profile info e.g.:
        https://x.com/nftchance
        Return profile info
        """
        scrape_url = self.get_url(url)
        
        if self._cache_exists(scrape_url):
            print(f"Using cached data for {scrape_url}")
            return self._read_cache(scrape_url)
        
        with sync_playwright() as pw:
            self.get_selector(pw, scrape_url, '[data-testid="primaryColumn"]')
            tweet_calls = [f for f in self.get_relative_xhr_calls(scrape_url).values() if "UserByScreenName" in f.url]
            for xhr in tweet_calls:
                data = xhr.json()
                result = data['data']['user']['result']
                self._write_cache(scrape_url, result)
                return result
            
    def call(self, url: str) -> dict:
        """
        Determine if the URL is a tweet or profile and call the appropriate function
        """
        scrape_url = self.get_url(url)
        
        if self._cache_exists(scrape_url):
            print(f"Using cached data for {scrape_url}")
            return self._read_cache(scrape_url)
        
        if scrape_url.startswith('https://x.com/i/web/status/'):
            return self.tweet(scrape_url)
        elif scrape_url.startswith('https://x.com/'):
            return self.profile(scrape_url)
        else:
            raise ValueError(f"Invalid URL: {scrape_url}")


    def _extract(self, data: dict) -> dict:
        """
        Extract tweet data from the scraped page
        """
        extracted = {}
        if isinstance(data, dict):
            # extracted['text'] = data['legacy']['full_text']
            extracted['retweets'] = data['legacy']['retweet_count']
            extracted['likes'] = data['legacy']['favorite_count']
            extracted['replies'] = data['legacy']['reply_count']
            extracted['quotes'] = data['legacy']['quote_count']
            extracted['user'] = {
                'followers': data['core']['user_results']['result']['legacy']['followers_count'],
                'following': data['core']['user_results']['result']['legacy']['friends_count'],
                'tweets': data['core']['user_results']['result']['legacy']['statuses_count'],
                'verified': data['core']['user_results']['result']['legacy']['verified'],
                'name': data['core']['user_results']['result']['legacy']['name'],
                'screen_name': data['core']['user_results']['result']['legacy']['screen_name'],
            }
             
        return extracted

    def analyze(self, url: str) -> dict:
        """
        Analyze the provided data using Claude
        """
        scrape_url = self.get_url(url)
        analysis_cache_suffix = '_analysis'

        if self._cache_exists(scrape_url, analysis_cache_suffix):
            print(f"Using cached analysis for {scrape_url}")
            return self._read_cache(scrape_url, analysis_cache_suffix)

        tweet_data = self.tweet(scrape_url)
        extracted_data = self._extract(tweet_data)

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20240620",
                system="Provide a score out of 100 (100 being definitely botted) and a short explanation on whether you believe the provided twitter metrics reflect having been botted:",
                messages=[
                    {"role": "user", "content": [{
                        "type": "text",
                        "text": json.dumps(extracted_data, indent=2)
                    }]}
                ],
                max_tokens=1000,
                temperature=0.5
            )

            text = message.content[0].text
            score_match = re.search(r'Score: (\d+)/100', text)
            score = int(score_match.group(1)) if score_match else None
            explanation = text.split("Explanation:", 1)[-1].strip()

            analysis_result = {
                "score": score,
                "explanation": explanation
            }

            self._write_cache(scrape_url, analysis_result, analysis_cache_suffix)

            return analysis_result
        except Exception as e:
            print(f"An error occurred during analysis: {str(e)}")
            return {"score": None, "explanation": f"Error in analysis: {str(e)}"}