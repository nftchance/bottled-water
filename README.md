# 💧 Bottled Water

Scrape Twitter profiles and tweets to analyze them for the presence of botted engagement and activity.

```ml
bottled-water
├─ scraper — "Playwright-based Twitter scraper"
├─ cache — "Local caching system for scraped data and analysis results"
├─ config — "Configuration for resource blocking and other settings"
└─ main — "Entry point for running the analysis"
```

The general interaction patterns is as follows:

```ml
bottled-water
├─ install - "pip install -r requirements.txt"
├─ configuration - "Create a .env file with the following contents: ANTHROPIC_API_KEY="
└─ run - "python main.py"
```

An example execution of the scripts will result in:

```json
{
  "score": 10,
  "explanation": "These metrics do not strongly suggest botting activity. Here's why:\n\n1. The engagement ratios (likes, replies, retweets, quotes) seem organic and relatively low compared to the user's follower count. Botted accounts often have inflated engagement numbers.\n\n2. The follower to following ratio (4213:235) is reasonable and doesn't indicate artificial inflation of followers.\n\n3. The tweet count (5562) is substantial and suggests a long-term, active account rather than a newly created bot account.\n\n4. The username and screen name appear genuine and personalized, not randomly generated as many bot accounts are.\n\n5. While the account isn't verified, this alone doesn't indicate botting.\n\n6. The engagement on this particular tweet (15 likes, 4 replies) is modest and realistic for an account of this size.\n\nOverall, these metrics appear to reflect natural, organic activity rather than botted behavior. The low score of 10/100 accounts for the small possibility that some subtle botting could be occurring, but there are no clear red flags in the provided data."
}
```
