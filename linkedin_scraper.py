import os
import re
import requests
import json
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from sentence_transformers import SentenceTransformer
from datetime import datetime
from collections import Counter

load_dotenv()

qdrant = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)
model = SentenceTransformer('all-MiniLM-L6-v2')

collections = [c.name for c in qdrant.get_collections().collections]
if "jobs" not in collections:
    qdrant.create_collection(
        collection_name="jobs",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )
    print("Created fresh jobs collection")
else:
    print("Using existing jobs collection")

def fetch_real_jobs(keyword="AI Engineer", location="India"):
    print(f"Fetching real jobs for: {keyword} in {location}")
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    params = {"query": f"{keyword} in {location}", "num_pages": "1", "page": "1"}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    jobs = data.get("data", [])
    print(f"Fetched {len(jobs)} real jobs!")
    return jobs

def enrich_job(job, keyword="AI Engineer"):
    title = job.get('job_title', '') or ''
    company = job.get('employer_name', '') or ''
    city = job.get('job_city', '') or ''
    state = job.get('job_state', '') or ''
    country = job.get('job_country', '') or ''
    parts = [p for p in [city, state, country] if p]
    location = ', '.join(parts) if parts else 'Location Not Listed'
    desc = job.get('job_description', '') or ''
    desc_lower = desc.lower()

    all_skills = ['python','java','javascript','sql','react','node','aws','docker',
                  'kubernetes','ml','ai','tensorflow','pytorch','langchain','qdrant',
                  'mongodb','postgresql','fastapi','flask','django','git','llm','nlp']
    found_skills = [s for s in all_skills if s in desc_lower]
    primary = ', '.join(found_skills[:3]) if found_skills else 'Not Listed'
    secondary = ', '.join(found_skills[3:6]) if len(found_skills) > 3 else 'Not Listed'

    exp_match = re.search(r'(\d+)\+?\s*years?', desc_lower)
    experience = f"{exp_match.group(1)}+ years" if exp_match else 'Not Specified'

    sal_match = re.search(r'[\$\u20b9]\s*[\d,]+', desc)
    salary = sal_match.group(0) if sal_match else 'Not Disclosed'

    email_match = re.search(r'[\w.-]+@[\w.-]+\.\w+', desc)
    email = email_match.group(0) if email_match else 'Not Listed'

    intent_score = 0
    if any(w in desc_lower for w in ['immediately','urgent','asap']):
        intent_score += 4
    if any(w in desc_lower for w in ['now hiring','actively hiring']):
        intent_score += 3
    if any(w in desc_lower for w in ['looking for','we need']):
        intent_score += 2
    if any(w in desc_lower for w in ['opening','opportunity','role']):
        intent_score += 1
    hiring_intent = f"Score {intent_score}/10 - {'Hot' if intent_score >= 6 else 'Warm' if intent_score >= 3 else 'Passive'}"

    is_intern = 'Yes' if any(w in desc_lower for w in ['intern','internship']) else 'No'
    is_student = 'Yes' if any(w in desc_lower for w in ['fresher','college','graduate','entry level']) else 'No'

    return {
        "post_id": f"{company}-{title}".replace(' ', '-').lower()[:50],
        "role": title,
        "company_name": company,
        "location": location,
        "primary_skills": primary,
        "secondary_skills": secondary,
        "must_have": found_skills[0] if found_skills else 'Not Listed',
        "years_of_experience": experience,
        "looking_for_college_students": is_student,
        "intern": is_intern,
        "salary_package": salary,
        "email": email,
        "phone": "Not Listed",
        "hiring_intent": hiring_intent,
        "author_name": company,
        "author_linkedin_url": "Not Listed",
        "post_url": job.get('job_apply_link', 'Not Listed') or 'Not Listed',
        "date_posted": job.get('job_posted_at_datetime_utc', 'Not Listed') or 'Not Listed',
        "date_processed": datetime.now().strftime('%Y-%m-%d'),
        "keyword_matched": keyword
    }

def run_agent(keyword="AI Engineer", location="India"):
    jobs = fetch_real_jobs(keyword, location)
    unique_jobs = []
    for job in jobs:
        desc = job.get('job_description', '') or ''
        job_text = f"{job.get('job_title', '')} {desc[:300]}"
        vector = model.encode(job_text).tolist()
        results = qdrant.query_points("jobs", query=vector, limit=1).points
        if results and results[0].score > 0.85:
            print(f"DUPLICATE SKIPPED: {job.get('job_title')}")
            continue
        enriched = enrich_job(job, keyword)
        point_id = abs(hash(job.get('job_id', job_text))) % (10**9)
        qdrant.upsert("jobs", points=[
            PointStruct(id=point_id, vector=vector, payload=enriched)
        ])
        unique_jobs.append(enriched)
        print(f"STORED: {enriched['role']} @ {enriched['company_name']}")
    print(f"\nDONE! {len(unique_jobs)} unique jobs stored in Qdrant!")
    return unique_jobs

if __name__ == "__main__":
    from sheets_writer import write_jobs_to_sheet

    print("🤖 LinkedIn Job Scraper Agent")
    print("="*50)
    user_input = input("Enter job keywords (comma separated): ")
    keywords = [k.strip() for k in user_input.split(",")]
    location = input("Enter location : ")

    all_results = []
    for keyword in keywords:
        print(f"\n{'='*50}")
        print(f"Searching for: {keyword}")
        print(f"{'='*50}")
        results = run_agent(keyword, location)
        all_results.extend(results)

    if all_results:
        print(f"\nTotal unique jobs found: {len(all_results)}")
        print("Writing all jobs to Google Sheets...")
        write_jobs_to_sheet(all_results)
        print("✅ Done!")

        # Skill Gap Analysis
        print(f"\n{'='*50}")
        print("📊 SKILL GAP ANALYSIS")
        print(f"{'='*50}")
        all_skills = []
        for job in all_results:
            skills = job.get('primary_skills', '') + ',' + job.get('secondary_skills', '')
            all_skills.extend([s.strip() for s in skills.split(',') if s.strip() != 'Not Listed'])

        skill_counts = Counter(all_skills).most_common(10)
        print(f"\n🔥 Top 10 Most In-Demand Skills:")
        for skill, count in skill_counts:
            bar = '█' * count
            print(f"  {skill:<15} {bar} ({count} jobs)")

        print(f"\n✅ Most Critical Skill: {skill_counts[0][0].upper()}")
        print(f"📈 Total Jobs Analyzed: {len(all_results)}")