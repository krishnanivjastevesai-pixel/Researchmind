"""
Research History Management Module
Handles loading, filtering, and managing past research reports.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from config import REPORTS_DIR
from utils import logger


def load_research_history() -> List[Dict]:
    """
    Load all research reports from the reports directory.
    
    Returns:
        List of report metadata dictionaries
    """
    history = []
    
    try:
        for report_file in REPORTS_DIR.glob("*.md"):
            try:
                # Parse filename: YYYYMMDD_HHMMSS_topic.md
                filename = report_file.stem
                parts = filename.split('_', 2)
                
                if len(parts) >= 3:
                    date_str = parts[0]
                    time_str = parts[1]
                    topic = parts[2].replace('_', ' ')
                    
                    # Parse datetime
                    timestamp = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                    
                    # Read file to extract score if available
                    with open(report_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Try to extract critic score
                    score = extract_score_from_content(content)
                    
                    # Get file size
                    file_size = report_file.stat().st_size / 1024  # KB
                    
                    history.append({
                        'id': filename,
                        'topic': topic,
                        'timestamp': timestamp,
                        'date_str': timestamp.strftime('%Y-%m-%d %H:%M'),
                        'relative_time': get_relative_time(timestamp),
                        'score': score,
                        'filepath': str(report_file),
                        'size_kb': round(file_size, 2),
                        'favorite': False  # Can be extended with metadata file
                    })
            
            except Exception as e:
                logger.warning(f"Failed to parse report file {report_file}: {e}")
                continue
        
        # Sort by timestamp (newest first)
        history.sort(key=lambda x: x['timestamp'], reverse=True)
        
        logger.info(f"Loaded {len(history)} reports from history")
        return history
    
    except Exception as e:
        logger.error(f"Error loading research history: {e}")
        return []


def extract_score_from_content(content: str) -> Optional[float]:
    """
    Extract critic score from report content.
    
    Args:
        content: Report markdown content
        
    Returns:
        Score as float or None if not found
    """
    import re
    
    # Look for patterns like "Score: 8/10" or "Score: 8.5/10"
    patterns = [
        r'\*\*Score:\*\*\s*(\d+\.?\d*)/10',
        r'Score:\s*(\d+\.?\d*)/10',
        r'Score:\s*(\d+\.?\d*)\s*/\s*10',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    
    return None


def get_relative_time(timestamp: datetime) -> str:
    """
    Convert timestamp to relative time string.
    
    Args:
        timestamp: Datetime object
        
    Returns:
        Relative time string (e.g., "2 hours ago")
    """
    now = datetime.now()
    delta = now - timestamp
    
    seconds = delta.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    else:
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"


def filter_history(
    history: List[Dict],
    query: Optional[str] = None,
    min_score: Optional[float] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    favorites_only: bool = False
) -> List[Dict]:
    """
    Filter research history based on criteria.
    
    Args:
        history: List of report metadata
        query: Search query for topic
        min_score: Minimum score filter
        date_from: Start date filter
        date_to: End date filter
        favorites_only: Show only favorites
        
    Returns:
        Filtered list of reports
    """
    filtered = history.copy()
    
    # Filter by query
    if query:
        query_lower = query.lower()
        filtered = [
            r for r in filtered
            if query_lower in r['topic'].lower()
        ]
    
    # Filter by score
    if min_score is not None:
        filtered = [
            r for r in filtered
            if r['score'] is not None and r['score'] >= min_score
        ]
    
    # Filter by date range
    if date_from:
        filtered = [r for r in filtered if r['timestamp'] >= date_from]
    
    if date_to:
        filtered = [r for r in filtered if r['timestamp'] <= date_to]
    
    # Filter favorites
    if favorites_only:
        filtered = [r for r in filtered if r['favorite']]
    
    return filtered


def delete_report(report_id: str) -> bool:
    """
    Delete a research report by ID.
    
    Args:
        report_id: Report filename (without extension)
        
    Returns:
        True if deleted successfully
    """
    try:
        report_file = REPORTS_DIR / f"{report_id}.md"
        
        if report_file.exists():
            report_file.unlink()
            logger.info(f"Deleted report: {report_id}")
            return True
        else:
            logger.warning(f"Report not found: {report_id}")
            return False
    
    except Exception as e:
        logger.error(f"Error deleting report {report_id}: {e}")
        return False


def load_report_content(report_id: str) -> Optional[str]:
    """
    Load the full content of a report.
    
    Args:
        report_id: Report filename (without extension)
        
    Returns:
        Report content or None if not found
    """
    try:
        report_file = REPORTS_DIR / f"{report_id}.md"
        
        if report_file.exists():
            with open(report_file, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            logger.warning(f"Report not found: {report_id}")
            return None
    
    except Exception as e:
        logger.error(f"Error loading report {report_id}: {e}")
        return None


def get_history_stats(history: List[Dict]) -> Dict:
    """
    Calculate statistics from research history.
    
    Args:
        history: List of report metadata
        
    Returns:
        Dictionary with statistics
    """
    if not history:
        return {
            'total_reports': 0,
            'avg_score': 0.0,
            'total_size_mb': 0.0,
            'topics_count': 0
        }
    
    scores = [r['score'] for r in history if r['score'] is not None]
    total_size = sum(r['size_kb'] for r in history) / 1024  # Convert to MB
    
    return {
        'total_reports': len(history),
        'avg_score': round(sum(scores) / len(scores), 2) if scores else 0.0,
        'total_size_mb': round(total_size, 2),
        'topics_count': len(set(r['topic'] for r in history))
    }


def export_all_reports(format: str = 'zip') -> Optional[Path]:
    """
    Export all reports in a single archive.
    
    Args:
        format: Export format ('zip' or 'tar')
        
    Returns:
        Path to exported archive or None if failed
    """
    import zipfile
    import tarfile
    from datetime import datetime
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == 'zip':
            archive_path = REPORTS_DIR.parent / f"all_reports_{timestamp}.zip"
            
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for report_file in REPORTS_DIR.glob("*.md"):
                    zipf.write(report_file, report_file.name)
        
        elif format == 'tar':
            archive_path = REPORTS_DIR.parent / f"all_reports_{timestamp}.tar.gz"
            
            with tarfile.open(archive_path, 'w:gz') as tarf:
                for report_file in REPORTS_DIR.glob("*.md"):
                    tarf.add(report_file, arcname=report_file.name)
        
        else:
            logger.error(f"Unsupported export format: {format}")
            return None
        
        logger.info(f"Exported all reports to: {archive_path}")
        return archive_path
    
    except Exception as e:
        logger.error(f"Error exporting reports: {e}")
        return None
