# archivo: reddit_psicologia_es_hispanos.py
from dotenv import load_dotenv
import os, re, time
import praw
import pandas as pd
from langdetect import detect, DetectorFactory

# --- 0) Autenticación ---
load_dotenv()
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
)

# --- 1) Utilidades de idioma ---
DetectorFactory.seed = 0
def es_es(t: str) -> bool:
    try:
        return detect(t) == "es"
    except Exception:
        return False

# --- 2) Patrones (en español) ---
PSICO = re.compile(r"\b(psicolog\w*|terapia\w*|terapeuta\w*|psiquiatr\w*)\b", re.I)
ACTITUD = re.compile(
    r"\b(conf[ií]o|desconf[ií]o|dudo|sirve|no\s+sirve|funciona|no\s+funciona|miedo|dej[eé]|abandon|retom|volv)\w*",
    re.I,
)
CONSULTA = re.compile(
    r"\b(necesit[oa]\s+ayuda|no\s+sé\s+qué\s+hacer|me\s+siento|me\s+cuesta|no\s+puedo|tengo\s+tdah|diagnostic\w*|tipo\s+de\s+terapia|ir\s+a\s+terapia)\b",
    re.I,
)

# --- 3) Solo subreddits hispanos ---
SUBS_HISPANOS = [
    # Países / comunidades grandes
    "spain", "mexico", "argentina", "chile", "uruguay", "colombia", "peru", "venezuela",
    # Temáticos en español (añade/quita a tu gusto)
    "PsicologiaES", "SaludMental", "ansiedadES", "depresionES"
]

# --- 4) Recolección ---
rows = []
for s in SUBS_HISPANOS:
    try:
        for p in reddit.subreddit(s).new(limit=200):
            text = f"{p.title or ''} {p.selftext or ''}".strip()
            if len(text.split()) < 10:
                continue
            if not es_es(text):
                continue
            if not PSICO.search(text):
                continue

            match_actitud = bool(ACTITUD.search(text))
            match_consulta = bool(CONSULTA.search(text))
            if not (match_actitud or match_consulta):
                continue

            rows.append({
                "subreddit": str(p.subreddit),
                "id": p.id,
                "score": p.score,
                "url": f"https://reddit.com{p.permalink}",
                "texto": text,
                "tipo": "consulta" if match_consulta else "actitud/opinion"
            })
        time.sleep(1.5)  # respeta límites
    except Exception as e:
        print(f"Saltado r/{s} → {e}")

# --- 5) Guardado ---
df = pd.DataFrame(rows).drop_duplicates(subset=["texto"])
print("Textos relevantes:", len(df))

if not df.empty:
    df.to_csv("reddit_psicologia_hispanos.csv", index=False, encoding="utf-8-sig")
    print("Guardado: reddit_psicologia_hispanos.csv")

    # Subconjunto: consultas/ayuda personal
    df_consultas = df[df["tipo"] == "consulta"]
    if not df_consultas.empty:
        df_consultas.to_csv("reddit_psicologia_hispanos_consultas.csv", index=False, encoding="utf-8-sig")
        print("Guardado: reddit_psicologia_hispanos_consultas.csv")
