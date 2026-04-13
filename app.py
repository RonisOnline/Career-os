import streamlit as st
import feedparser
import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="Career OS", layout="wide")
st.title("🧠 Career OS — Stable Production Mode")

# -----------------------
# JOB FETCH
# -----------------------
def get_jobs():
    feed = feedparser.parse("https://remoteok.com/remote-jobs.rss")

    jobs = []
    for e in feed.entries[:5]:  # KEEP SMALL (prevents token/rate issues)
        jobs.append({
            "title": e.title,
            "description": e.summary[:250]
        })
    return jobs

# -----------------------
# OPENAI BATCH SCORING (SAFE)
# -----------------------
def score_jobs(jobs):
    prompt = f"""
You are a job ranking AI.

Score jobs based on:
- autonomy
- clarity
- career growth
- low chaos

Return STRICT JSON:

{{
  "results": [
    {{
      "title": "string",
      "score": 0-100,
      "reason": "short sentence",
      "chaos": "low|medium|high"
    }}
  ]
}}

Jobs:
{json.dumps(jobs)}
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return json.loads(res.choices[0].message.content)["results"]

# -----------------------
# CACHED EXECUTION (CRITICAL FIX)
# -----------------------
@st.cache_data(ttl=3600)  # runs once per hour
def cached_scoring():
    jobs = get_jobs()
    return score_jobs(jobs)

# -----------------------
# RUN (NO MULTIPLE CALLS)
# -----------------------
st.write("Fetching latest job rankings...")

scored = cached_scoring()

if not scored:
    st.error("No data returned. Try again later.")
    st.stop()

scored = sorted(scored, key=lambda x: x["score"], reverse=True)

best = scored[0]
top = scored[:5]
avoid = scored[-2:]

# -----------------------
# UI
# -----------------------
st.subheader("🔥 BEST JOB")

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
