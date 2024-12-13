import pandas as pd
from django.utils import timezone
from datetime import timedelta
import re
from ingestion.models import Event

def extract_hashtags(text):
    """Extract hashtags from text."""
    if not isinstance(text, str):
        return []
    # Match hashtags that start with # and contain letters, numbers, and underscores
    hashtags = re.findall(r'#[\w\d]+', text.lower())
    return hashtags

def get_top_hashtags(time_range='1h'):
    """
    Get top hashtags from recent events.
    time_range: string indicating time window ('1h', '24h', '7d')
    """
    # Convert time_range to timedelta
    time_ranges = {
        '1h': timedelta(hours=1),
        '24h': timedelta(hours=24),
        '7d': timedelta(days=7)
    }
    delta = time_ranges.get(time_range, timedelta(hours=1))
    
    # Get recent events
    cutoff_time = timezone.now() - delta
    qs = Event.objects.filter(
        created_at__gte=cutoff_time
    ).order_by('-created_at')
    
    # Convert to DataFrame
    df = pd.DataFrame(list(qs.values('record', 'created_at')))
    
    if df.empty:
        return []
    
    # Extract hashtags from record text
    all_hashtags = []
    for record in df['record']:
        if isinstance(record, dict) and 'text' in record:
            hashtags = extract_hashtags(record['text'])
            all_hashtags.extend(hashtags)
    
    if not all_hashtags:
        return []
    
    # Create DataFrame of hashtags and count frequencies
    hashtag_df = pd.DataFrame(all_hashtags, columns=['hashtag'])
    top_hashtags = (hashtag_df['hashtag']
                   .value_counts()
                   .head(10)
                   .to_dict())
    
    # Return list of tuples (hashtag, count)
    return [(tag, count) for tag, count in top_hashtags.items()]

def get_trending_hashtags(time_range='1h', min_count=5):
    """
    Get hashtags that are trending (showing significant recent growth).
    """
    # Get current period
    current_hashtags = get_top_hashtags(time_range)
    
    # Get previous period for comparison
    time_ranges = {
        '1h': timedelta(hours=2),
        '24h': timedelta(hours=48),
        '7d': timedelta(days=14)
    }
    delta = time_ranges.get(time_range, timedelta(hours=2))
    
    cutoff_time = timezone.now() - delta
    qs = Event.objects.filter(
        created_at__gte=cutoff_time,
        created_at__lt=timezone.now() - delta/2
    ).order_by('-created_at')
    
    # Process previous period
    df_prev = pd.DataFrame(list(qs.values('record', 'created_at')))
    
    if df_prev.empty:
        return current_hashtags
    
    # Extract previous period hashtags
    prev_hashtags = []
    for record in df_prev['record']:
        if isinstance(record, dict) and 'text' in record:
            hashtags = extract_hashtags(record['text'])
            prev_hashtags.extend(hashtags)
    
    if not prev_hashtags:
        return current_hashtags
    
    # Calculate trending scores
    prev_counts = pd.Series(prev_hashtags).value_counts().to_dict()
    trending = []
    
    for hashtag, current_count in current_hashtags:
        prev_count = prev_counts.get(hashtag, 0)
        if current_count >= min_count:
            growth = (current_count - prev_count) / (prev_count + 1)  # +1 to avoid division by zero
            trending.append((hashtag, current_count, growth))
    
    # Sort by growth rate and return top 10
    return sorted(trending, key=lambda x: x[2], reverse=True)[:10] 