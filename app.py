import streamlit as st
import feedparser
import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="Career OS Elite", layout="wide")
st.title("🧠 Career OS — Batch Mode (Stable)")

# -----------------------
# JOB INGESTION
# -----------------------
def get_jobs():
    feed = feedparser.parse("https://remoteok.com/remote-jobs.rss")

    jobs = []
    for e in feed.entries[:10]:  # reduced for stability
        jobs.append({
            "title": e.title,
            "description": e.summary
        })
    return jobs

# -----------------------
# BATCH AI SCORING (1 CALL)
# -----------------------
def score_jobs_batch(jobs):
    prompt = f"""
You are a career job scoring system.

User wants:
- structured roles
- autonomy
- career growth
- avoid chaotic / vague roles

Return STRICT JSON in this format:

{{
  "results": [
    {{
      "title": "...",
      "score": 0-100,
      "reason": "one sentence",
      "chaos": "low | medium | high"
    }}
  ]
}}

Jobs:
{json.dumps(jobs, indent=2)}
"""

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return json.loads(res.choices[0].message.content)["results"]

# -----------------------
# LOAD DATA
# -----------------------
jobs = get_jobs()

# run batch scoring (ONLY ONE API CALL)
scored = score_jobs_batch(jobs)

# sort by score
scored = sorted(scored, key=lambda x: x["score"], reverse=True)

best = scored[0]
top = scored[:5]
avoid = scored[-3:]

# -----------------------
# UI
# -----------------------
st.subheader("🔥 BEST JOB TODAY")

st.markdown(f"### {best['title']}")
st.write(best["reason"])
st.metric("Score", best["score"])
st.write(f"Chaos: {best['chaos']}")

st.divider()

st.subheader("🔥 TOP JOBS")

for job in top:
    st.markdown(f"### {job['title']}")
    st.write(f"Score: {job['score']}")
    st.write(job["reason"])
    st.write(f"Chaos: {job['chaos']}")
    st.divider()

st.subheader("🚫 AVOID")

for job in avoid:
    st.write(f"❌ {job['title']} — {job['score']} — {job['chaos']}")
