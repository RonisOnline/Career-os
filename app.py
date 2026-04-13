import streamlit as st
import feedparser
import os
import json
import time
from openai import OpenAI, RateLimitError

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="Career OS", layout="wide")
st.title("🧠 Career OS — Stable Mode")

# -----------------------
# JOB INGESTION (SMALL + CLEAN)
# -----------------------
def get_jobs():
    feed = feedparser.parse("https://remoteok.com/remote-jobs.rss")

    jobs = []
    for e in feed.entries[:6]:  # keep small to avoid limits
        jobs.append({
            "title": e.title,
            "description": e.summary[:300]  # truncate to reduce tokens
        })
    return jobs

# -----------------------
# BATCH SCORING (1 API CALL)
# -----------------------
def score_jobs_batch(jobs):

    prompt = f"""
You are a job ranking system.

User prefers:
- structured roles
- autonomy
- career growth
- low chaos environments

Return STRICT JSON:

{{
  "results": [
    {{
      "title": "job title",
      "score": 0-100,
      "reason": "one sentence",
      "chaos": "low | medium | high"
    }}
  ]
}}

Jobs:
{json.dumps(jobs)}
"""

    for attempt in range(3):
        try:
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )

            return json.loads(res.choices[0].message.content)["results"]

        except RateLimitError:
            time.sleep(3)

    return []

# -----------------------
# RUN
# -----------------------
jobs = get_jobs()
scored = score_jobs_batch(jobs)

if not scored:
    st.error("API limit hit — try refreshing in a minute.")
    st.stop()

scored = sorted(scored, key=lambda x: x["score"], reverse=True)

best = scored[0]
top = scored[:5]
avoid = scored[-2:]

# -----------------------
# UI
# -----------------------
st.subheader("🔥 BEST JOB TODAY")

st.markdown(f"### {best['title']}")
st.write(best["reason"])
st.metric("Score", best["score"])
st.write("Chaos:", best["chaos"])

st.divider()

st.subheader("🔥 TOP JOBS")

for job in top:
    st.markdown(f"### {job['title']}")
    st.write(f"Score: {job['score']}")
    st.write(job["reason"])
    st.write("Chaos:", job["chaos"])
    st.divider()

st.subheader("🚫 AVOID")

for job in avoid:
    st.write(f"❌ {job['title']} — {job['score']} — {job['chaos']}")
