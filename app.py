import streamlit as st
import feedparser
import os
import json
from openai import OpenAI, RateLimitError

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="Career OS Ultra Stable", layout="wide")
st.title("🧠 Career OS — Ultra Stable Mode")

# -----------------------
# FREE JOB FETCH (NO AI HERE)
# -----------------------
def get_jobs():
    feed = feedparser.parse("https://remoteok.com/remote-jobs.rss")

    jobs = []
    for e in feed.entries[:3]:  # SMALL = safe
        jobs.append({
            "title": e.title,
            "description": e.summary[:200]
        })
    return jobs


jobs = get_jobs()

st.subheader("📡 Live Jobs (No AI cost)")
for j in jobs:
    st.write("###", j["title"])
    st.write(j["description"])
    st.divider()

# -----------------------
# SESSION CACHE FOR AI RESULTS
# -----------------------
if "scored" not in st.session_state:
    st.session_state.scored = None

# -----------------------
# AI FUNCTION (ONLY RUNS ON BUTTON)
# -----------------------
def score_jobs(jobs):
    prompt = f"""
You are a job ranking system.

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
# BUTTON CONTROLS AI CALL
# -----------------------
st.subheader("🧠 AI Ranking Control")

if st.button("Run AI Ranking (uses 1 API call)"):
    try:
        st.session_state.scored = score_jobs(jobs)
    except RateLimitError:
        st.error("Rate limit hit — wait 1 minute and try again.")

# -----------------------
# DISPLAY AI RESULTS
# -----------------------
if st.session_state.scored:
    scored = sorted(st.session_state.scored, key=lambda x: x["score"], reverse=True)

    best = scored[0]
    top = scored[:3]
    avoid = scored[-2:]

    st.subheader("🔥 BEST JOB")
    st.markdown(f"### {best['title']}")
    st.write(best["reason"])
    st.metric("Score", best["score"])
    st.write("Chaos:", best["chaos"])

    st.divider()

    st.subheader("🔥 TOP JOBS")
    for job in top:
        st.markdown(f"### {job['title']}")
        st.write(job["reason"])
        st.write(job["score"])
        st.write(job["chaos"])
        st.divider()

    st.subheader("🚫 AVOID")
    for job in avoid:
        st.write(job["title"], job["score"], job["chaos"])
