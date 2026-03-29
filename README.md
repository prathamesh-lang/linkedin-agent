# 🤖 LinkedIn Job Scraper Agent
> Built for **Lyzr x Qdrant Hackathon — Track 2**

An intelligent job scraping agent that fetches real job listings, semantically deduplicates them using **Qdrant vector search**, enriches them with AI-extracted metadata, and writes everything to a **Google Sheet** automatically.

---

## 🚀 What It Does

1. **Fetches real jobs** from JSearch API (LinkedIn-powered)
2. **Semantically deduplicates** using Qdrant + sentence embeddings — no duplicate jobs ever stored
3. **Enriches each job** with skills, experience, salary, hiring intent, and more
4. **Writes 18 columns** of structured data to Google Sheets automatically

---

## 🧠 Tech Stack

| Tool | Purpose |
|------|---------|
| [JSearch API](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) | Fetch real LinkedIn job listings |
| [Qdrant](https://qdrant.tech/) | Semantic vector deduplication |
| [Sentence Transformers](https://www.sbert.net/) | Generate embeddings (`all-MiniLM-L6-v2`) |
| [Google Sheets API](https://developers.google.com/sheets) | Auto-write enriched job data |
| Python + dotenv | Core agent logic |

---

## 📁 Project Structure

```
linkedin-agent/
├── linkedin_scraper.py   # Main agent — fetch, deduplicate, enrich
├── sheets_writer.py      # Writes enriched jobs to Google Sheet
├── test_qdrant.py        # Test Qdrant dedup connection
├── credentials.json      # Google Sheets API credentials (not committed)
├── .env                  # API keys (not committed)
└── README.md
```

---

## ⚙️ Setup

### 1. Clone the repo
```bash
git clone https://github.com/prathamesh-lang/linkedin-agent.git
cd linkedin-agent
```

### 2. Install dependencies
```bash
pip install requests python-dotenv qdrant-client sentence-transformers google-auth google-auth-oauthlib google-api-python-client
```

### 3. Create your `.env` file
```env
RAPIDAPI_KEY=your_jsearch_rapidapi_key
QDRANT_URL=your_qdrant_cluster_url
QDRANT_API_KEY=your_qdrant_api_key
GOOGLE_SHEET_ID=your_google_sheet_id
```

### 4. Add Google Sheets credentials
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Enable **Google Sheets API**
- Download `credentials.json` and place it in the project root

### 5. Run the agent
```bash
python linkedin_scraper.py
```

---

## 🔍 How Deduplication Works

Every job is converted into a **384-dimension vector** using `all-MiniLM-L6-v2`. Before storing, the agent queries Qdrant for the nearest neighbor. If similarity score > **0.85**, the job is skipped as a duplicate.

```
DUPLICATE SKIPPED: Expert, AI Engineering
DUPLICATE SKIPPED: Senior Machine Learning Engineer
DONE! 0 unique jobs stored in Qdrant!
```

This means even if the same job is posted with slightly different wording, it gets caught. ✅

---

## 📊 Google Sheet Output (18 Columns)

| Column | Description |
|--------|-------------|
| post_id | Unique job identifier |
| role | Job title |
| company_name | Employer |
| location | City, State, Country |
| primary_skills | Top 3 skills from description |
| secondary_skills | Skills 4–6 |
| must_have | Single most critical skill |
| years_of_experience | Extracted from description |
| looking_for_college_students | Yes/No |
| intern | Yes/No |
| salary_package | Extracted if mentioned |
| email | Contact email if listed |
| phone | Contact phone if listed |
| hiring_intent | Active / Passive |
| author_name | Company name |
| author_linkedin_url | LinkedIn URL if available |
| post_url | Direct apply link |
| date_posted | Original posting date |

---

## 🎥 Demo

> Watch the full demo on Loom: `[link coming soon]`

---

## 👨‍💻 Author

**Prathamesh** — [@prathamesh-lang](https://github.com/prathamesh-lang)

Built with ❤️ for the Lyzr x Qdrant Hackathon 2026
