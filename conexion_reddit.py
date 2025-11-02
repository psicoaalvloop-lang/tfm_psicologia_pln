import os
from dotenv import load_dotenv
import praw

load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

print("¿Conexión solo lectura?:", reddit.read_only)

for post in reddit.subreddit("psychology").hot(limit=5):
    print("-", post.title)
