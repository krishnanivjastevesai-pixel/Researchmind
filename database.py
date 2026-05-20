"""
Database Module
Handles all database operations using Supabase PostgreSQL.
Falls back to file-based storage if database is not available.
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
from utils import logger

# Try to import psycopg2, but don't fail if not available
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    logger.warning("psycopg2 not installed, using file-based storage only")


def get_db_connection():
    """Get database connection."""
    if not DB_AVAILABLE:
        return None
    
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.info("DATABASE_URL not set, using file-based storage")
            return None
        
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


def save_report_to_db(topic: str, report: str, feedback: str, score: float = None, 
                      model: str = None, temperature: float = None, 
                      report_length: str = None) -> bool:
    """Save report to database."""
    conn = get_db_connection()
    if not conn:
        logger.info("Database not available, report saved to file only")
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reports (topic, report_content, feedback, score, 
                               model_used, temperature, report_length)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (topic, report, feedback, score, model, temperature, report_length))
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Report saved to database: {topic}")
        return True
    except Exception as e:
        logger.error(f"Failed to save report to database: {e}")
        if conn:
            conn.close()
        return False


def load_reports_from_db(limit: int = 100) -> List[Dict]:
    """Load reports from database."""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, topic, score, created_at, model_used, 
                   temperature, report_length
            FROM reports
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))
        
        reports = []
        for row in cursor.fetchall():
            reports.append({
                'id': str(row['id']),
                'topic': row['topic'],
                'score': float(row['score']) if row['score'] else None,
                'timestamp': row['created_at'],
                'date_str': row['created_at'].strftime('%Y-%m-%d %H:%M'),
                'relative_time': get_relative_time(row['created_at']),
                'model': row['model_used'],
                'temperature': float(row['temperature']) if row['temperature'] else None,
                'report_length': row['report_length'],
                'favorite': False
            })
        
        cursor.close()
        conn.close()
        logger.info(f"Loaded {len(reports)} reports from database")
        return reports
    except Exception as e:
        logger.error(f"Failed to load reports from database: {e}")
        if conn:
            conn.close()
        return []


def get_report_by_id(report_id: str) -> Optional[Dict]:
    """Get full report content by ID."""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT topic, report_content, feedback, score, created_at
            FROM reports
            WHERE id = %s
        """, (report_id,))
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            # Format as markdown
            content = f"# Research Report: {row['topic']}\n\n"
            content += f"**Generated:** {row['created_at'].strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            content += "---\n\n"
            content += row['report_content']
            if row['feedback']:
                content += f"\n\n---\n\n## 🧐 Critic Feedback\n\n{row['feedback']}"
            
            return content
        return None
    except Exception as e:
        logger.error(f"Failed to get report: {e}")
        if conn:
            conn.close()
        return None


def delete_report_from_db(report_id: str) -> bool:
    """Delete report from database."""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reports WHERE id = %s", (report_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        
        if deleted:
            logger.info(f"Report deleted from database: {report_id}")
        return deleted
    except Exception as e:
        logger.error(f"Failed to delete report: {e}")
        if conn:
            conn.close()
        return False


def search_reports(query: str = None, min_score: float = None, limit: int = 50) -> List[Dict]:
    """Search reports by topic and/or score."""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        sql = """
            SELECT id, topic, score, created_at, model_used
            FROM reports
            WHERE 1=1
        """
        params = []
        
        if query:
            sql += " AND topic ILIKE %s"
            params.append(f'%{query}%')
        
        if min_score is not None:
            sql += " AND score >= %s"
            params.append(min_score)
        
        sql += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(sql, params)
        
        reports = []
        for row in cursor.fetchall():
            reports.append({
                'id': str(row['id']),
                'topic': row['topic'],
                'score': float(row['score']) if row['score'] else None,
                'timestamp': row['created_at'],
                'relative_time': get_relative_time(row['created_at']),
                'model': row['model_used'],
                'favorite': False
            })
        
        cursor.close()
        conn.close()
        return reports
    except Exception as e:
        logger.error(f"Search failed: {e}")
        if conn:
            conn.close()
        return []


def get_history_stats_from_db() -> Dict:
    """Get statistics from database."""
    conn = get_db_connection()
    if not conn:
        return {
            'total_reports': 0,
            'avg_score': 0.0,
            'total_size_mb': 0.0,
            'topics_count': 0
        }
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                AVG(score) as avg_score,
                COUNT(DISTINCT topic) as unique_topics
            FROM reports
        """)
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return {
            'total_reports': row['total'] if row else 0,
            'avg_score': round(float(row['avg_score']), 2) if row and row['avg_score'] else 0.0,
            'total_size_mb': 0.0,  # Not tracking in DB
            'topics_count': row['unique_topics'] if row else 0
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        if conn:
            conn.close()
        return {
            'total_reports': 0,
            'avg_score': 0.0,
            'total_size_mb': 0.0,
            'topics_count': 0
        }


def get_relative_time(timestamp: datetime) -> str:
    """Convert timestamp to relative time."""
    now = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
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
        return timestamp.strftime('%Y-%m-%d')


def is_database_available() -> bool:
    """Check if database is available."""
    if not DB_AVAILABLE:
        return False
    
    conn = get_db_connection()
    if conn:
        conn.close()
        return True
    return False
