import io, sqlite3, pandas as pd, streamlit as st, plotly.express as px
from pypdf import PdfReader
from engine import rank_jobs, parse_skills

st.set_page_config(page_title="SkillMatch", page_icon="🎯", layout="wide")
st.title("🎯 SkillMatch")
st.caption("Find internships that match your skills — and see exactly what you're missing")

@st.cache_data   # read the DB once, not on every click — a real optimization
def load_stats():
    con = sqlite3.connect("jobs.db")
    df = pd.read_sql("SELECT title, skills FROM jobs", con)
    con.close()
    return df

df = load_stats()
st.sidebar.metric("Internships indexed", len(df))
st.sidebar.caption("Live listings → SQLite → embedding-based matching")

# ---------- skills demand chart (horizontal, hover-friendly) ----------
skill_counts = (df["skills"].fillna("")
                .apply(parse_skills).explode()
                .value_counts().head(10)
                .sort_values())   # smallest→largest, so the biggest bar sits on top
fig = px.bar(x=skill_counts.values, y=skill_counts.index, orientation="h",
             labels={"x": "Number of listings asking for it", "y": ""})
fig.update_layout(title="Most in-demand skills across listings",
                  height=430, margin=dict(l=10, r=10, t=50, b=10))
with st.expander("📊 What skills are companies actually asking for?"):
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")

# ---------- six demo students ----------
DEMO = {
    "🤖 AI/ML student": (
        "Skills: Python, SQL, pandas, machine learning, deep learning, NLP, "
        "prompt engineering, Git. Projects: sentiment analysis with scikit-learn, "
        "LLM chatbot with prompt engineering, data pipeline using SQL and pandas."),
    "🌐 Web development student": (
        "Skills: JavaScript, React, HTML, CSS, Node.js, Django, Git. Projects: "
        "e-commerce frontend in React, college event website, blog backend with "
        "Django and SQLite."),
    "📊 Data analytics student": (
        "Skills: SQL, Excel, Power BI, pandas, data analysis, statistics. "
        "Projects: sales dashboard in Power BI for a retail dataset, customer "
        "churn analysis using Excel and pandas."),
    "📣 Marketing student (B.Com)": (
        "Skills: MS Excel, communication, marketing, PowerPoint, social media. "
        "Managed college fest social media page, grew it to 2,000 followers; "
        "coordinated a 50-member volunteer team."),
    "🎨 UI/UX design student": (
        "Skills: Figma, HTML, CSS, communication, content writing. Projects: "
        "redesigned the college fest booking app in Figma, built landing pages "
        "with HTML and CSS, usability testing with 20 students."),
    "✍️ Content & SEO student": (
        "Skills: content writing, SEO, social media, communication, marketing. "
        "Wrote 40+ articles for the college magazine website, ran an Instagram "
        "page to 5,000 followers, keyword research for blogs."),
}
choice = st.radio("Choose a resume:", ["🧪 Try a demo student", "📄 Upload a PDF"])
text = ""
if choice == "📄 Upload a PDF":
    file = st.file_uploader("Resume (PDF)", type="pdf")
    if file:
        text = " ".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(file.read())).pages)
        if len(text.strip()) < 100:
            st.error("Couldn't read this PDF — it may be a scanned image. Try a text-based PDF.")
else:
    who = st.selectbox("Pick a student:", list(DEMO.keys()))
    text = DEMO[who]

if text:
    st.success("Skills detected: " + (", ".join(sorted(parse_skills(text))) or "none"))
    st.subheader("Top matches")
    for j in rank_jobs(text):
        with st.container(border=True):
            st.markdown(f"### {j['title']} · {j['company']}")
            st.progress(int(min(j["score"], 100)), text=f"{j['score']}% match")
            st.write(f"💰 {j['stipend'] or 'Stipend not listed'}")
            if j["missing"]:
                st.warning("📚 Missing skills: " + ", ".join(j["missing"]))
            else:
                st.success("You cover every skill we detected — apply now! 🎉")
            if j["url"]:
                st.link_button("View listing →", j["url"])