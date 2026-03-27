import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

load_dotenv()
client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
model = SentenceTransformer('all-MiniLM-L6-v2')

print("✅ Using existing 'jobs' collection")

# Test semantic similarity (WINNING FEATURE)
job1 = "AI Engineer Mumbai Python ML required 3+ years experience"  
job2 = "ML Developer Bombay seeking Python experts"

vec1 = model.encode(job1).tolist()
vec2 = model.encode(job2).tolist()

client.upsert("jobs", [{"id": 999, "vector": vec1, "payload": {"title": job1}}])
results = client.search("jobs", query_vector=vec2, limit=1)
print(f"✅ QDRANT VICTORY! Similarity: {results[0].score:.3f}")