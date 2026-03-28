import os
import requests
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from sentence_transformers import SentenceTransformer
import anthropic
import json
from datetime import datetime

load_dotenv()

# ── Clients ──────────────────────────────────────────────
qdrant = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)
claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
model = SentenceTransformer('all-MiniLM-L6-v2')

# ── Ensure collection exists ──────────────────────────────
collections = [c.name for c in qdrant.get_collections().collections]
if "jobs" not in collections:
    qdrant.create_collection(
        collection_name="jobs",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )
    print("✅ Created fresh 'jobs' collection")
else:
    print("✅ Using existing 'jobs' collection")

# ── Fetch REAL jobs from JSearch API (free tier) ──────────
def fetch_real_jobs(keyword="AI Engineer", location="India", num=10):
    print(f"\n🔍 Fetching real jobs for: {keyword} in {location}")
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    params = {"query": f"{keyword} in {location}", "num_pages": "1", "page": "1"}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    jobs = data.get("data", [])
    print(f"✅ Fetched {len(jobs)} real jobs from LinkedIn/Indeed")
    return jobs

# ── Claude AI enrichment ──────────────────────────────────
def enrich_job_with_claude(job):
    raw = f"""
    Title: {job.get('job_title', '')}
    Company: {job.get('employer_name', '')}
    Location: {job.get('job_city', '')} {job.get('job_country', '')}
    Description: {job.get('job_description', '')[:1000]}
    """
    message = claude.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=600,
        messages=[{
            "role": "user",
            "content": f"""Extract structured job info from this and return ONLY valid JSON:
{raw}

Return this exact JSON structure:
{{
  "post_id": "unique id based on company+title",
  "role": "job title",
  "company_name": "company",
  "location": "city, country",
  "primary_skills": "top 3 skills comma separated",
  "secondary_skills": "other skills",
  "must_have": "key requirement",
  "years_of_experience": "X years",
  "looking_for_college_students": "Yes/No",
  "intern": "Yes/No",
  "salary_package": "if mentioned else Not Disclosed",
  "email": "if found else Not Listed",
  "phone": "if found else Not Listed",
  "hiring_intent": "Active/Passive",
  "author_name": "recruiter if mentioned",
  "author_linkedin_url": "if found else Not Listed",
  "post_url": "job url",
  "date_posted": "date if available",
  "date_processed": "{datetime.now().strftime('%Y-%m-%d')}",
  "keyword_matched": "AI Engineer"
}}"""
        }]
    )
    try:
        return json.loads(message.content[0].text)
    except:
        return None

# ── Main agent loop ───────────────────────────────────────
def run_agent(keyword="AI Engineer", location="India"):
    jobs = fetch_real_jobs(keyword, location)
    unique_jobs = []
    
    for job in jobs:
        job_text = f"{job.get('job_title','')} {job.get('job_description','')[:300]}"
        vector = model.encode(job_text).tolist()
        
        # Semantic duplicate check
        results = qdrant.search("jobs", query_vector=vector, limit=1)
        if results and results[0].score > 0.85:
            print(f"⏭️  DUPLICATE SKIPPED: {job.get('job_title')}")
            continue
        
        # Enrich with Claude AI
        print(f"🤖 Enriching: {job.get('job_title')} @ {job.get('employer_name')}")
        enriched = enrich_job_with_claude(job)
        if not enriched:
            continue
        
        # Store in Qdrant
        point_id = abs(hash(job.get('job_id', job_text))) % (10**9)
        qdrant.upsert("jobs", points=[
            PointStruct(id=point_id, vector=vector, payload=enriched)
        ])
        unique_jobs.append(enriched)
        print(f"✅ STORED: {enriched['role']} @ {enriched['company_name']}")
    
    print(f"\n🏆 {len(unique_jobs)} unique jobs processed and stored in Qdrant!")
    return unique_jobs

if __name__ == "__main__":
    results = run_agent("AI Engineer", "India")
    print("\n📊 Sample enriched job:")
    if results:
        print(json.dumps(results[0], indent=2))
