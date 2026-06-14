import json
import os
from ingestion import fetch_recent_reviews

def main():
    # Test fetching 10 weeks of data
    print("Testing Play Store Ingestion (10 week window)...")
    data = fetch_recent_reviews("com.nextbillion.groww", weeks_back=10)
    
    raw_file = "raw_reviews.json"
    normalized_file = "normalized_reviews.json"
    
    # Save Raw to JSON
    with open(raw_file, 'w', encoding='utf-8') as f:
        json.dump(data["raw"], f, indent=2, ensure_ascii=False)
        
    # Save Normalized to JSON
    with open(normalized_file, 'w', encoding='utf-8') as f:
        json.dump(data["normalized"], f, indent=2, ensure_ascii=False)
        
    print(f"Successfully saved {len(data['raw'])} raw reviews to {raw_file}")
    print(f"Successfully saved {len(data['normalized'])} normalized reviews to {normalized_file}")
    
    # Print a quick sample of normalized
    if data["normalized"]:
        print("\nSample Normalized Review:")
        print(json.dumps(data["normalized"][0], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    # Ensure we run from the correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
