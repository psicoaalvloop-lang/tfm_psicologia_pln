from dotenv import load_dotenv
import os, re, time
import praw
import pandas as pd
from langdetect import detect, DetectorFactory

load_dotenv()
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
)

DetectorFactory.seed = 0
def es_es(t):
    try:
        return detect(t) == "es"
    except:
        return False

# Núcleo psicología/terapia + actitud/opinión (muy mínimos para la demo)
PSICO = re.compile(r"\b(psicolog\w*|terapia\w*|terapeuta\w*|psiquiatr\w*)\b", re.I)
ACTITUD = re.compile(r"\b(conf[ií]o|desconf[ií]o|dudo|sirve|no\s+sirve|funciona|no\s+funciona|miedo|dej[eé]|abandon|retom|volv)\w*", re.I)

QUERIES = ['"psicólogo"', '"ir al psicólogo"', 'terapia', 'terapeuta', 'psiquiatra']

rows = []

# 1) Buscar en TODO Reddit por queries en español
for q in QUERIES:
    for p in reddit.subreddit("all").search(q, sort="new", time_filter="year", limit=80):
        text = f"{p.title or ''} {p.selftext or ''}".strip()
        if len(text.split()) >= 10 and es_es(text) and PSICO.search(text) and ACTITUD.search(text):
            rows.append({
                "subreddit": str(p.subreddit),
                "id": p.id,
                "texto": text,
                "url": f"https://reddit.com{p.permalink}",
                "score": p.score
            })
    time.sleep(1.5)  # respeta API

# 2) Reforzar con algunos subs hispanos de alto volumen (sin r/psicologia ni r/saludmental)
SUBS_ES = ["spain", "mexico", "argentina", "chile", "uruguay", "colombia"]
for s in SUBS_ES:
    try:
        for p in reddit.subreddit(s).new(limit=120):
            text = f"{p.title or ''} {p.selftext or ''}".strip()
            if len(text.split()) >= 10 and es_es(text) and PSICO.search(text) and ACTITUD.search(text):
                rows.append({
                    "subreddit": s, "id": p.id, "texto": text,
                    "url": f"https://reddit.com{p.permalink}", "score": p.score
                })
        time.sleep(1.5)
    except Exception as e:
        print("saltado r/", s, "→", e)

df = pd.DataFrame(rows).drop_duplicates(subset=["texto"])
print("Textos relevantes (demo):", len(df))
if not df.empty:
    df.to_csv("reddit_psicologia_es_filtrado_demo.csv", index=False)
    print("Guardado: reddit_psicologia_es_filtrado_demo.csv")
