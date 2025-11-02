# archivo: reddit_psicologia_es_hispanos_fino.py
from dotenv import load_dotenv
import os, re, time, math
import praw
import pandas as pd
from langdetect import detect, DetectorFactory
from datetime import datetime, timezone, timedelta

# ----------------------------
# 0) CONFIGURACIÓN (TOCA AQUÍ)
# ----------------------------
SUBS_HISPANOS = [
    "spain","mexico","argentina","chile","uruguay","colombia","peru","venezuela",
    "PsicologiaES","SaludMental","ansiedadES","depresionES"
    # añade o quita
]

# Límite de posts por subreddit
POSTS_PER_SUB = 200  # baja a 100 si quieres ir más rápido

# Ventana temporal: solo posts de los últimos N días (None = sin filtro)
LAST_N_DAYS = 14  # TOCA AQUÍ. Pon None si no quieres filtrar por fecha

# Filtros de contenido
MIN_WORDS = 30           # sube/baja para exigir más contenido
REQUIRE_FIRST_PERSON = True
MIN_SCORE = 0            # p.ej. 1 o 2 si quieres señal social
MIN_COMMENTS = 0         # p.ej. 3 para evitar posts sin interacción
REQUIRE_SELFPOST = True  # descarta enlaces sin selftext

# Flairs deseados (case-insensitive). Vacío = no filtrar por flair.
# Útil si algunos subreddits usan flairs como "Ayuda", "Consejo", "Salud mental", etc.
ALLOWED_FLAIRS = []  # p.ej.: ["Ayuda", "Consejo", "Consejos", "Consulta"]

# Palabras/frases que quieres excluir explícitamente (negativas)
NEGATIVOS = re.compile(
    r"\b(mem(es|e)|shitpost|pol[ií]tica|noticia|periodismo|promo|promoci[oó]n|encuesta|tarea|deberes|universidad|examen|oferta|descuento|c[oó]digo)\b",
    re.I
)

# ----------------------------
# 1) Autenticación
# ----------------------------
load_dotenv()
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
)

# ----------------------------
# 2) Utilidades de idioma
# ----------------------------
DetectorFactory.seed = 0

def es_es(t: str) -> bool:
    # Heurística: langdetect + atajo por diacríticos y palabras muy españolas
    try:
        if detect(t) == "es":
            return True
    except Exception:
        pass
    # Plan B: if tiene tildes comunes y stopwords muy españolas
    return bool(re.search(r"[áéíóúñ¿¡]", t)) and bool(re.search(r"\b(que|como|para|esto|estoy|tengo|porque|por qué)\b", t, re.I))

# ----------------------------
# 3) Patrones (más finos)
# ----------------------------
PSICO = re.compile(
    r"\b(psicolog\w*|psicoterap\w*|terapia\w*|terapeuta\w*|psiquiatr\w*|ansiedad|depresi[oó]n|tdah|trastorn\w+|trauma|toc|fobia|mindfulness|cognitiv\w+|conductual|tcc)\b",
    re.I
)

ACTITUD = re.compile(
    r"\b(conf[ií]o|desconf[ií]o|dudo|sirve|no\s+sirve|funciona|no\s+funciona|miedo|dej[eé]|abandon|retom|volv|me\s+ha\s+ayudado|no\s+me\s+sirvi[oó])\w*",
    re.I,
)

CONSULTA = re.compile(
    r"\b(necesit[oa]\s+ayuda|no\s+sé\s+qué\s+hacer|me\s+siento|me\s+cuesta|no\s+puedo|tengo\s+tdah|diagnostic\w*|tipo\s+de\s+terapia|ir\s+a\s+terapia|recomiendan\s+terapeuta|busco\s+psic[oó]logo)\b",
    re.I,
)

# 1ª persona fuerte (reduce noticias/debates impersonales)
FIRST_PERSON = re.compile(
    r"\b(yo|me|mi|mis|conmigo|estoy|siento|tengo|no\s+puedo|no\s+sé|me\s+ayuda|me\s+cuesta)\b",
    re.I
)

# ----------------------------
# 4) Recolección
# ----------------------------
rows = []
now = datetime.now(timezone.utc)
min_created = None
if isinstance(LAST_N_DAYS, (int, float)) and LAST_N_DAYS > 0:
    min_created = now - timedelta(days=LAST_N_DAYS)

for s in SUBS_HISPANOS:
    try:
        sub = reddit.subreddit(s)
        for p in sub.new(limit=POSTS_PER_SUB):
            # Fecha
            if min_created is not None:
                created_dt = datetime.fromtimestamp(p.created_utc, tz=timezone.utc)
                if created_dt < min_created:
                    continue

            title = p.title or ""
            selftext = p.selftext or ""
            text = f"{title} {selftext}".strip()

            if REQUIRE_SELFPOST and not selftext.strip():
                continue

            # Flair (si se usa)
            flair = (getattr(p, "link_flair_text", None) or "").strip()
            if ALLOWED_FLAIRS:
                if not flair or not any(f.lower() in flair.lower() for f in ALLOWED_FLAIRS):
                    continue

            # Longitud
            if len(text.split()) < MIN_WORDS:
                continue

            # Idioma
            if not es_es(text):
                continue

            # Exclusiones explícitas
            if NEGATIVOS.search(text):
                continue

            # Núcleo de psicología
            if not PSICO.search(text):
                continue

            # Señales de actitud/consulta
            match_actitud = bool(ACTITUD.search(text))
            match_consulta = bool(CONSULTA.search(text))

            # 1ª persona (si se exige)
            if REQUIRE_FIRST_PERSON and not FIRST_PERSON.search(text):
                # si no hay 1ª persona, pero sí una consulta clara, lo dejamos pasar
                if not match_consulta:
                    continue

            # Señal social mínima
            if p.score < MIN_SCORE or p.num_comments < MIN_COMMENTS:
                continue

            tipo = "consulta" if match_consulta else ("actitud/opinion" if match_actitud else "otro")

            rows.append({
                "subreddit": str(p.subreddit),
                "id": p.id,
                "created_utc": datetime.fromtimestamp(p.created_utc, tz=timezone.utc).isoformat(),
                "author": str(p.author) if p.author else None,
                "score": p.score,
                "num_comments": p.num_comments,
                "flair": flair,
                "url": f"https://reddit.com{p.permalink}",
                "titulo": title,
                "texto": selftext.strip(),
                "tipo": tipo,
            })
        time.sleep(1.5)  # respeta límites
    except Exception as e:
        print(f"Saltado r/{s} → {e}")

# ----------------------------
# 5) Guardado
# ----------------------------
df = pd.DataFrame(rows)

if df.empty:
    print("No se encontraron posts tras los filtros.")
else:
    # Desduplicar por id (más seguro que por texto)
    df = df.drop_duplicates(subset=["id"]).reset_index(drop=True)

    # Orden sugerido: más recientes y con más comentarios
    def sort_key(row):
        try:
            t = datetime.fromisoformat(row["created_utc"])
        except Exception:
            t = datetime(1970,1,1,tzinfo=timezone.utc)
        # Combina frescura y participación
        return (t, row.get("num_comments", 0), row.get("score", 0))

    df = df.sort_values(by=["created_utc","num_comments","score"], ascending=[False, False, False])

    print("Textos relevantes:", len(df))
    out_all = "reddit_psicologia_hispanos_fino.csv"
    df.to_csv(out_all, index=False, encoding="utf-8-sig")
    print(f"Guardado: {out_all}")

    # Subconjunto: consultas/ayuda personal
    df_consultas = df[df["tipo"] == "consulta"]
    if not df_consultas.empty:
        out_cons = "reddit_psicologia_hispanos_fino_consultas.csv"
        df_consultas.to_csv(out_cons, index=False, encoding="utf-8-sig")
        print(f"Guardado: {out_cons}")
