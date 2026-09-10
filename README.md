🎯 SkillMatch — Resume-to-Internship Matching Engine
Upload a resume (or pick a demo profile) → get ranked internship matcheswith an exact list of missing skills.

Live app:  https://skillmatch-gayatri.streamlit.app

Problem
Students can't tell which of hundreds of listings actually fit them —and never learn which skills to acquire next.

How it works
Data: 199+ live listings scraped from Internshala (BeautifulSoup),including per-listing skill requirements from detail pages → SQLite (jobs.db)
Ranking (hybrid): score = 0.6 × semantic similarity (MiniLM embeddings, cosine) + 0.4 × exact skill overlap — with missing-skills shown per match
Frontend: Streamlit (PDF resume parsing via pypdf, Plotly skills-demand chart)
API: FastAPI POST /match with auto-generated interactive docs,input validation via Pydantic
Stack
Python · sentence-transformers · SQLite · pandas · Streamlit · Plotly · FastAPI

Engineering notes
Word-boundary regex skill matching (fixed the classic javascript → javafalse positive)
Detail-page scraping with fallback title extraction for HTML drift
@st.cache_data for one-time DB reads; job vectors encoded once and cached
Future work
Learning-to-rank with click feedback · FAISS index · implicit-skill map (Django ⇒ Python)
