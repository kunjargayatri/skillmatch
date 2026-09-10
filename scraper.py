import os, re, time, sqlite3, requests, pandas as pd
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
BASE = "https://internshala.com/internships/{}-internship/page-{}"

def clean(text):
    text = (text or "").replace("Actively hiring", " ")
    return re.sub(r"\s+", " ", text).strip(" ·|-")

def title_from_url(url):
    slug = url.rstrip("/").split("/")[-1]
    return slug.replace("-", " ").strip().title()

def get_skills(url):
    """Visit one listing's detail page and extract its skills text."""
    if not url:
        return ""
    try:
        soup = BeautifulSoup(requests.get(url, headers=HEADERS, timeout=15).text, "html.parser")
        block = soup.select_one(".skills_container")          # try known container first
        if block:
            s = clean(block.get_text(" ", strip=True))
            if s:
                return s
        text = soup.get_text(" ", strip=True)                 # fallback: search whole page
        m = re.search(r"Skill\s*\(s\)\s*required[:\s]*(.{0,250})", text, re.I)
        return clean(m.group(1)) if m else ""
    except Exception:
        return ""

def scrape(keyword="machine-learning", pages=3):
    new_rows = []
    for p in range(1, pages + 1):
        r = requests.get(BASE.format(keyword, p), headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"[!] Page {p} blocked ({r.status_code}) — stopping"); break
        cards = BeautifulSoup(r.text, "html.parser").select(".individual_internship")
        print(f"[{keyword}] page {p}: {len(cards)} cards")
        for c in cards:
            link = c.select_one("a")
            href = link["href"] if (link and link.has_attr("href")) else ""
            url = "https://internshala.com" + href if href.startswith("/") else href
            t_el = c.select_one(".profile") or c.select_one("h3") or c.select_one("h2")
            title = clean(t_el.get_text(strip=True)) if t_el else ""
            if not title:
                title = title_from_url(url) if url else ""    # bulletproof fallback
            comp_el = c.select_one(".company_name")
            company = clean(comp_el.get_text(strip=True)) if comp_el else ""
            st_el = c.select_one(".stipend")
            stipend = clean(st_el.get_text(strip=True)) if st_el else ""
            if url:
                new_rows.append({"title": title, "company": company,
                                 "stipend": stipend, "skills": "", "url": url})
        time.sleep(2)

    df = pd.DataFrame(new_rows).drop_duplicates(subset=["url"])
    print(f"{len(df)} new listings. Fetching skills from detail pages (~1 sec each)...")
    skills = []
    for i, u in enumerate(df["url"], 1):
        skills.append(get_skills(u))
        if i % 10 == 0:
            print(f"  {i}/{len(df)} done")
        time.sleep(1)
    df["skills"] = skills

    old = pd.read_sql("SELECT * FROM jobs", sqlite3.connect("jobs.db")) if os.path.exists("jobs.db") else pd.DataFrame()
    merged = pd.concat([old, df]).drop_duplicates(subset=["url"]).reset_index(drop=True)
    merged.to_sql("jobs", sqlite3.connect("jobs.db"), if_exists="replace", index=False)
    withskills = int((merged["skills"].fillna("").str.len() > 0).sum())
    print(f"✅ Total unique listings: {len(merged)} | with skills data: {withskills}")

if __name__ == "__main__":
    scrape("data-science")