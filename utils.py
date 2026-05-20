"""
Utility Functions
Helper functions for caching, validation, logging, and file operations.
"""

import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any
from config import (
    CACHE_DIR, CACHE_EXPIRY_HOURS, ENABLE_CACHE,
    MIN_TOPIC_LENGTH, MAX_TOPIC_LENGTH, LOG_FILE, LOG_LEVEL
)

# ============================================
# Logging Setup
# ============================================
def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ============================================
# Cache Functions
# ============================================
def get_cache_key(data: str) -> str:
    """Generate a cache key from input data."""
    return hashlib.md5(data.encode()).hexdigest()

def get_from_cache(key: str) -> Optional[Any]:
    """
    Retrieve data from cache if it exists and is not expired.
    
    Args:
        key: Cache key
        
    Returns:
        Cached data or None if not found/expired
    """
    if not ENABLE_CACHE:
        return None
    
    cache_file = CACHE_DIR / f"{key}.json"
    
    if not cache_file.exists():
        logger.debug(f"Cache miss: {key}")
        return None
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # Check expiry
        cached_time = datetime.fromisoformat(cache_data['timestamp'])
        expiry_time = cached_time + timedelta(hours=CACHE_EXPIRY_HOURS)
        
        if datetime.now() > expiry_time:
            logger.debug(f"Cache expired: {key}")
            cache_file.unlink()  # Delete expired cache
            return None
        
        logger.info(f"Cache hit: {key}")
        return cache_data['data']
    
    except Exception as e:
        logger.error(f"Error reading cache: {e}")
        return None

def save_to_cache(key: str, data: Any) -> None:
    """
    Save data to cache with timestamp.
    
    Args:
        key: Cache key
        data: Data to cache
    """
    if not ENABLE_CACHE:
        return
    
    cache_file = CACHE_DIR / f"{key}.json"
    
    try:
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        logger.debug(f"Cached data: {key}")
    
    except Exception as e:
        logger.error(f"Error saving to cache: {e}")

def clear_cache() -> int:
    """
    Clear all cached data.
    
    Returns:
        Number of files deleted
    """
    count = 0
    for cache_file in CACHE_DIR.glob("*.json"):
        cache_file.unlink()
        count += 1
    
    logger.info(f"Cleared {count} cache files")
    return count

# ============================================
# Validation Functions
# ============================================
def validate_topic(topic: str) -> tuple[bool, str]:
    """
    Validate research topic input.
    
    Args:
        topic: Research topic string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not topic or not topic.strip():
        return False, "Topic cannot be empty"
    
    topic = topic.strip()
    
    if len(topic) < MIN_TOPIC_LENGTH:
        return False, f"Topic must be at least {MIN_TOPIC_LENGTH} characters"
    
    if len(topic) > MAX_TOPIC_LENGTH:
        return False, f"Topic must be less than {MAX_TOPIC_LENGTH} characters"
    
    # Check for suspicious patterns
    suspicious_patterns = ['<script', 'javascript:', 'onerror=']
    if any(pattern in topic.lower() for pattern in suspicious_patterns):
        return False, "Topic contains invalid characters"
    
    return True, ""

# ============================================
# File Export Functions
# ============================================
def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename[:100]  # Limit length

def save_report(topic: str, report: str, feedback: str, format: str = 'md') -> Path:
    """
    Save research report to file.
    
    Args:
        topic: Research topic
        report: Report content
        feedback: Critic feedback
        format: Output format (md, txt, html)
        
    Returns:
        Path to saved file
    """
    from config import REPORTS_DIR
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = sanitize_filename(topic)
    filename = f"{timestamp}_{safe_topic}.{format}"
    filepath = REPORTS_DIR / filename
    
    try:
        if format == 'md':
            content = f"# Research Report: {topic}\n\n"
            content += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            content += "---\n\n"
            content += report
            content += f"\n\n---\n\n## 🧐 Critic Feedback\n\n{feedback}"
        
        elif format == 'txt':
            content = f"Research Report: {topic}\n"
            content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            content += "="*80 + "\n\n"
            content += report
            content += f"\n\n{'='*80}\n\nCritic Feedback\n\n{feedback}"
        
        elif format == 'html':
            content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Research Report: {topic}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
               max-width: 900px; margin: 40px auto; padding: 20px; 
               line-height: 1.6; background: #f5f5f5; }}
        .container {{ background: white; padding: 40px; border-radius: 8px; 
                     box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #ff8c32; border-bottom: 3px solid #ff8c32; padding-bottom: 10px; }}
        h2 {{ color: #333; margin-top: 30px; }}
        .meta {{ color: #666; font-size: 0.9em; margin-bottom: 30px; }}
        .feedback {{ background: #f0f9ff; border-left: 4px solid #50c878; 
                    padding: 20px; margin-top: 40px; border-radius: 4px; }}
        pre {{ background: #f4f4f4; padding: 15px; border-radius: 4px; 
              overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Research Report: {topic}</h1>
        <div class="meta">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        <div class="content">{report.replace(chr(10), '<br>')}</div>
        <div class="feedback">
            <h2>🧐 Critic Feedback</h2>
            {feedback.replace(chr(10), '<br>')}
        </div>
    </div>
</body>
</html>"""
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Report saved: {filepath}")
        return filepath
    
    except Exception as e:
        logger.error(f"Error saving report: {e}")
        raise

# ============================================
# Statistics Functions
# ============================================
def get_cache_stats() -> dict:
    """Get cache statistics."""
    cache_files = list(CACHE_DIR.glob("*.json"))
    total_size = sum(f.stat().st_size for f in cache_files)
    
    return {
        'total_files': len(cache_files),
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'cache_dir': str(CACHE_DIR)
    }

def get_reports_stats() -> dict:
    """Get reports statistics."""
    from config import REPORTS_DIR
    
    report_files = list(REPORTS_DIR.glob("*"))
    total_size = sum(f.stat().st_size for f in report_files)
    
    return {
        'total_reports': len(report_files),
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'reports_dir': str(REPORTS_DIR)
    }
