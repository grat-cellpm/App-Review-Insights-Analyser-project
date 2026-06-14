import datetime
from google_play_scraper import Sort, reviews
import emoji
from langdetect import detect, LangDetectException

def fetch_recent_reviews(app_id: str = "com.nextbillion.groww", target_count: int = 300) -> dict:
    """
    Fetches the most recent reviews from the Google Play Store for the specified app
    until the target_count of normalized reviews is reached.
    
    Args:
        app_id: The package name of the app on the Play Store.
        target_count: Number of normalized reviews to fetch.
        
    Returns:
        A dict containing 'raw' and 'normalized' review lists.
    """
    all_raw_reviews = []
    all_normalized_reviews = []
    continuation_token = None
    
    # We fetch in chunks of 200 (max allowed by the scraper)
    count_per_batch = 200
    
    print(f"Fetching {target_count} normalized reviews for {app_id}...")
    
    while True:
        result, continuation_token = reviews(
            app_id,
            lang='en', # fetch english reviews
            country='in', # default to India
            sort=Sort.NEWEST, # We need newest to stop early based on date
            count=count_per_batch,
            continuation_token=continuation_token
        )
        
        if not result:
            break
            
        # Filter and append
        reached_target = False
        
        for r in result:
            if len(all_normalized_reviews) < target_count:
                # Add to raw reviews, but serialize datetimes
                r_raw = dict(r)
                if 'at' in r_raw and r_raw['at']:
                    r_raw['at'] = r_raw['at'].isoformat()
                if 'repliedAt' in r_raw and r_raw['repliedAt']:
                    r_raw['repliedAt'] = r_raw['repliedAt'].isoformat()
                all_raw_reviews.append(r_raw)
                
                text = r.get('content', '')
                if not text:
                    continue
                
                # Rule 1: Less than 8 words
                if len(text.split()) < 8:
                    continue
                
                # Rule 2: Contains emojis
                if emoji.emoji_count(text) > 0:
                    continue
                    
                # Rule 3: Not in English
                try:
                    if detect(text) != 'en':
                        continue
                except LangDetectException:
                    # If language detection fails (e.g. only numbers), skip
                    continue
                
                # Normalize the review data: keep only rating and text
                all_normalized_reviews.append({
                    'rating': r['score'],
                    'text': text
                })
            else:
                reached_target = True
                break
                
        # If we hit the target count, we stop paginating
        if reached_target or not continuation_token:
            break
            
    print(f"Fetched {len(all_raw_reviews)} raw reviews.")
    print(f"Kept {len(all_normalized_reviews)} normalized reviews.")
    return {"raw": all_raw_reviews, "normalized": all_normalized_reviews}
