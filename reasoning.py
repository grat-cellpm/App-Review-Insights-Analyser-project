import json
import re
import os
import pandas as pd
from sentence_transformers import SentenceTransformer
import umap
import hdbscan
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Step 1: PII Scrubbing
def scrub_pii(text: str) -> str:
    # Basic regex for phone numbers (Indian/General)
    phone_pattern = re.compile(r'\b(?:\+?91[\-\s]?)?[6789]\d{9}\b')
    # Basic regex for emails
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    
    text = phone_pattern.sub('[PHONE_REMOVED]', text)
    text = email_pattern.sub('[EMAIL_REMOVED]', text)
    return text

# Step 2 & 3: Embeddings & Clustering
def cluster_reviews(reviews: list[dict], min_cluster_size=5) -> list[dict]:
    """
    Takes a list of normalized review dicts, generates embeddings, 
    reduces dimensionality, and clusters them.
    Returns the reviews with 'cluster_id' attached.
    """
    if not reviews:
        return []
        
    texts = [r['text'] for r in reviews]
    
    print("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print(f"Generating embeddings for {len(texts)} reviews...")
    embeddings = model.encode(texts, show_progress_bar=True)
    
    print("Reducing dimensionality with UMAP...")
    # UMAP parameters can be tuned. We use a smaller n_neighbors for smaller datasets.
    n_neighbors = min(15, len(texts) - 1)
    if n_neighbors < 2:
        n_neighbors = 2
        
    reducer = umap.UMAP(n_neighbors=n_neighbors, n_components=5, metric='cosine', random_state=42)
    reduced_embeddings = reducer.fit_transform(embeddings)
    
    print("Clustering with HDBSCAN...")
    clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, metric='euclidean')
    cluster_labels = clusterer.fit_predict(reduced_embeddings)
    
    for i, review in enumerate(reviews):
        review['cluster_id'] = int(cluster_labels[i])
        
    return reviews

# Step 4: LLM Summarization
def summarize_clusters(reviews_with_clusters: list[dict]) -> list[dict]:
    """
    Sends each valid cluster to Gemini to extract themes, ideas, and quotes.
    Returns a list of cluster summaries.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Warning: GROQ_API_KEY not found. Skipping summarization.")
        return []
        
    client = Groq(api_key=api_key)
    
    # Group reviews by cluster
    clusters = {}
    for r in reviews_with_clusters:
        cid = r['cluster_id']
        if cid == -1:
            continue # Skip noise
        if cid not in clusters:
            clusters[cid] = []
        clusters[cid].append(r['text'])
        
    summaries = []
    
    print(f"Summarizing {len(clusters)} valid clusters with Gemini...")
    for cid, texts in clusters.items():
        # Limit the number of texts sent to the LLM to avoid token limits (sample top 50 if huge)
        sample_texts = texts[:50]
        
        prompt = f"""
You are an expert product manager analyzing app reviews. I have grouped the following user reviews into a distinct cluster because they share a common theme.

Reviews:
{json.dumps(sample_texts, indent=2)}

Task:
1. Identify the core 'Theme Name' (3-5 words).
2. Propose 1-2 actionable product ideas or fixes to address the feedback.
3. Extract 2-3 short, highly representative verbatim quotes EXACTLY as they appear in the reviews above. Do not alter the text of the quotes.

Return the response strictly as a JSON object matching this schema:
{{
  "theme_name": "string",
  "actionable_ideas": ["string"],
  "representative_quotes": ["string"]
}}
        """
        
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are an expert product manager analyzing app reviews. Return the response strictly as a JSON object."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            text_resp = response.choices[0].message.content
            # Simple extraction of JSON from response text (handling markdown code blocks if any)
            if "```json" in text_resp:
                text_resp = text_resp.split("```json")[1].split("```")[0].strip()
            elif "```" in text_resp:
                text_resp = text_resp.split("```")[1].strip()
                
            summary_data = json.loads(text_resp)
            summary_data['cluster_id'] = cid
            summary_data['review_count'] = len(texts)
            summaries.append(summary_data)
            print(f"Processed cluster {cid}: {summary_data.get('theme_name')}")
        except Exception as e:
            print(f"Failed to summarize cluster {cid}: {e}")
            
    # Sort by review count descending
    summaries.sort(key=lambda x: x.get('review_count', 0), reverse=True)
    return summaries

def process_phase_3(input_filepath: str, output_filepath: str):
    print(f"Loading normalized reviews from {input_filepath}...")
    with open(input_filepath, 'r', encoding='utf-8') as f:
        reviews = json.load(f)
        
    # Step 1
    for r in reviews:
        r['text'] = scrub_pii(r['text'])
        
    # Steps 2 & 3
    # Use min_cluster_size=10, assuming there are enough reviews. Adjust if dataset is small.
    min_size = min(10, max(3, len(reviews) // 10)) if len(reviews) < 100 else 10
    clustered_reviews = cluster_reviews(reviews, min_cluster_size=min_size)
    
    # Step 4
    cluster_summaries = summarize_clusters(clustered_reviews)
    
    output_data = {
        "total_reviews_processed": len(reviews),
        "total_clusters_found": len(cluster_summaries),
        "clusters": cluster_summaries
    }
    
    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    print(f"Phase 3 output saved to {output_filepath}.")

if __name__ == "__main__":
    process_phase_3("sample_reviews.json", "reasoning_output.json")
