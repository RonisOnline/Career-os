import streamlit as st
import feedparser
import os
import json
import sqlite3
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="Career OS Elite", layout="wide")

st.title("🧠 Career OS — Elite Mode (Chaos Detector Enabled)")

# -----------------------
# MEMORY
# -----------------------
conn = sqlite3.connect("memory.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS saved_jobs (title TEXT)""")
c.execute("""CREATE TABLE IF NOT EXISTS disliked_jobs (title TEXT)""")

def save_job(title):
    c.execute("INSERT INTO saved_jobs VALUES (?)", (title,))
    conn.commit()

def dislike_job(title):
    c.execute("INSERT INTO disliked_jobs VALUES (?)", (title,))
    conn.commit()

def get_disliked():
    c.execute("SELECT title FROM disliked_jobs")
    return [r[0] for r in c.fetchall()]

# -----------------------
# CHAOS DETECTOR (NEW)
# -----------------------
CHAOS_KEYWORDS = [
    "fast-paced", "wear many hats", "multiple priorities",
    "self-starter", "no two days are the same", "ambiguity",
    "ad hoc", "startup environment", "jack of all trades",
    "unstructured", "rapidly changing", "dynamic environment"
]

def detect_chaos(text):
    text_lower = text.lower()

    score = 0
    hits = []

    for kw in CHAOS_KEYWORDS:
        if kw in text_lower:
            score += 1
            hits.append(kw)

    if score <= 1:
        level = "🟢 Low Chaos"
        penalty = 0
    elif score <= 3:
        level = "🟡 Medium Chaos"
        penalty = 10
    else:
        level = "🔴 High Chaos"
        penalty = 25

    return level, penalty, hits

# -----------------------
# JOB INGESTION
# -----------------------
def get_jobs():
    feed = feedparser.parse("https://remoteok.com/remote-jobs.rss")

    jobs = []
    for e in feed.entries[:25]:
        jobs.append({
            "title": e.title,
            "description": e.summary
        })
    return jobs

# -----------------------
# AI SCORING
# -----------------------
def score_job(job):
    prompt = f"""
You are a career filtering system.

User wants:
- structured roles
- autonomy
- career growth
- NOT chaotic admin environments

Job:
{job['title']}
{job['description']}

Return STRICT JSON:
{{
  "score": 0-100,
  "reason": "one sentence",
  "risk": "low | medium | high"
}}
"""

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        return json.loads(res.choices[0].message.content)
    except:
        return {"score": 50, "reason": "parse error", "risk": "medium"}

# -----------------------
# LOAD + FILTER MEMORY
# -----------------------
jobs = get_jobs()
disliked = get_disliked()

filtered_jobs = [j for j in jobs if j["title"] not in disliked]

scored = []

for job in filtered_jobs:

    chaos_level, penalty, hits = detect_chaos(job["description"])

    result = score_job(job)

    # APPLY CHAOS PENALTY
    result["score"] = max(0, result["score"] - penalty)
    result["chaos"] = chaos_level
    result["chaos_hits"] = hits

    scored.append((job, result))

scored.sort(key=lambda x: x[1]["score"], reverse=True)

top = scored[:5]
best = top[0]
avoid = scored[-5:]

# -----------------------
# UI
# -----------------------
st.subheader("🔥 BEST JOB TODAY")

st.markdown(f"### {best[0]['title']}")
st.write(best[1]["reason"])
st.metric("Score", best[1]["score"])
st.write(best[1]["chaos"])

st.divider()

st.subheader("🔥 TOP 5 JOBS")

for job, score in top:
    with st.container():
        st.markdown(f"### {job['title']}")
        st.write(f"Score: {score['score']}")
        st.write(score["reason"])
        st.write(score["chaos"])

        if score["chaos_hits"]:
            st.caption("⚠️ Chaos signals: " + ", ".join(score["chaos_hits"]))

        col1, col2 = st.columns(2)

        with col1:
            if st.button("👍 Save", key="save_" + job["title"]):
                save_job(job["title"])
                st.success("Saved")

        with col2:
            if st.button("👎 Hide", key="hide_" + job["title"]):
                dislike_job(job["title"])
                st.warning("Hidden")

        st.divider()

st.subheader("🚫 AVOID THESE")

for job, score in avoid:
    st.write(f"❌ {job['title']} — {score['score']} — {score['chaos']}")
