import re, sqlite3
from sentence_transformers import SentenceTransformer, util

print("Loading embedding model (first run downloads ~80MB — please wait)...")
model = SentenceTransformer("all-MiniLM-L6-v2")
SKILLS = ["python","sql","pandas","numpy","machine learning","deep learning","nlp",
          "generative ai","llm","rag","prompt engineering","langchain","pytorch",
          "django","fastapi","flask","react","javascript","node.js","html","css",
          "git","excel","communication","marketing","power bi","docker","aws",
          "data analysis","java","c++","android","figma","digital marketing",
          "content writing","seo","social media"]

def parse_skills(text):
    """Word-boundary matching: 'javascript' no longer triggers 'java'."""
    t = text.lower()
    found = set()
    for s in SKILLS:
        if re.search(r"(?<![\w.#])" + re.escape(s) + r"(?![\w.#])", t):
            found.add(s)
    return found

def load_jobs():
    return sqlite3.connect("jobs.db").execute(
        "SELECT rowid, title, company, stipend, skills, url FROM jobs").fetchall()

_cache = None   # encode all jobs ONCE and reuse — never recompute per query

def _job_vectors():
    global _cache
    if _cache is None:
        jobs = load_jobs()
        texts = [(t or "") + " " + (sk or "") for _, t, _, _, sk, _ in jobs]
        _cache = (jobs, model.encode(texts, normalize_embeddings=True))
    return _cache

def rank_jobs(resume_text, top_k=10):
    jobs, jvecs = _job_vectors()
    rvec = model.encode(resume_text, normalize_embeddings=True)
    have = parse_skills(resume_text)
    out = []
    for (jid, title, company, stipend, skills, url), jv in zip(jobs, jvecs):
        job_skills = parse_skills(skills)
        overlap = len(have & job_skills) / max(len(job_skills), 1)
        sem = max(0.0, util.cos_sim(rvec, jv).item())
        score = round(100 * (0.6 * sem + 0.4 * overlap), 1)
        out.append({"score": score, "title": title, "company": company,
                    "stipend": stipend, "url": url,
                    "missing": sorted(job_skills - have)})
    out.sort(key=lambda x: -x["score"])
    return out[:top_k]

if __name__ == "__main__":
    tests = {
        "AI STUDENT": "Skills: Python, SQL, pandas, machine learning, deep learning, "
                      "NLP, prompt engineering, Git. Projects: sentiment analysis with "
                      "scikit-learn, LLM chatbot with prompt engineering, data pipeline "
                      "using SQL and pandas.",
        "WEB STUDENT": "Skills: JavaScript, React, HTML, CSS, Node.js, Django, Git. "
                       "Projects: e-commerce frontend in React, college event website, "
                       "blog backend with Django and SQLite.",
        "NON-TECH STUDENT": "Skills: MS Excel, communication, marketing, PowerPoint. "
                            "Managed college fest social media, grew it to 2,000 followers.",
    }
    for name, resume in tests.items():
        print(f"\n===== Top 3 matches for {name} =====")
        for j in rank_jobs(resume, 3):
            print(f"{j['score']}%  {j['title']} @ {j['company']}"
                  f" | missing: {', '.join(j['missing']) or 'none'}")