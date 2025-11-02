from dotenv import load_dotenv
import os, praw

# Cargar tus claves desde el .env
load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
)

print("Solo lectura:", reddit.read_only)

# Prueba con algunos subreddits en español
for s in ["psicologia", "saludmental", "spain"]:
    print(f"\n--- r/{s} ---")
    try:
        for p in reddit.subreddit(s).new(limit=3):
            print("•", p.title)
    except Exception as e:
        print("error en", s, "→", e)
