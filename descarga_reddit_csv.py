#descarga_reddit_csv.py
import os, csv, time
from datetime import datetime, timezone
from dotenv import load_dotenv
import praw

# 1) Cargar credenciales
load_dotenv()
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
)

# 2) CONFIGURA AQUÍ
SUBREDDITS = ["AskReddit"]  # ej.: ["Endometriosis", "TwoXChromosomes", "AskDocs"]
MODO = "new"                 # "hot" | "new" | "top"
LIMITE = 200                 # cuántos posts por subreddit (empieza con 100–200)
SALIDA = "posts_reddit.csv"  # nombre del CSV

# 3) Preparar CSV
campos = ["id","created_utc","subreddit","author","title","score",
          "num_comments","url","selftext"]
f = open(SALIDA, "w", newline="", encoding="utf-8")
w = csv.DictWriter(f, fieldnames=campos)
w.writeheader()

# 4) Descargar
for sub in SUBREDDITS:
    s = reddit.subreddit(sub)
    if MODO == "hot":
        generador = s.hot(limit=LIMITE)
    elif MODO == "top":
        generador = s.top(limit=LIMITE)
    else:
        generador = s.new(limit=LIMITE)

    for post in generador:
        w.writerow({
            "id": post.id,
            "created_utc": datetime.fromtimestamp(post.created_utc, tz=timezone.utc).isoformat(),
            "subreddit": str(post.subreddit),
            "author": str(post.author) if post.author else None,
            "title": post.title,
            "score": post.score,
            "num_comments": post.num_comments,
            "url": post.url,
            "selftext": post.selftext,
        })
        time.sleep(0.2)  # ser amable con la API

f.close()
print(f"Listo ✅ Guardado en: {SALIDA}")
