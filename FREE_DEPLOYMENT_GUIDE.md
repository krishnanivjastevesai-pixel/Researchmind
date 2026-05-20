# 🚀 ResearchMind - FREE Deployment Guide

Complete step-by-step guide to deploy ResearchMind for FREE with database.

---

## 🎯 Overview

We'll deploy using **100% FREE services**:
- **Streamlit Cloud** - FREE hosting (unlimited public apps)
- **Supabase** - FREE PostgreSQL database (500MB storage)
- **GitHub** - FREE code hosting

**Total Cost: $0/month** ✅

---

## 📋 Prerequisites

- GitHub account (free)
- Streamlit Cloud account (free)
- Supabase account (free)
- Groq API key (free)
- Tavily API key (free)

---

## 🗄️ Part 1: Database Setup (Supabase)

### Step 1: Create Supabase Account

1. Go to [supabase.com](https://supabase.com)
2. Click **"Start your project"**
3. Sign up with GitHub (recommended)
4. Verify your email

### Step 2: Create New Project

1. Click **"New Project"**
2. Fill in details:
   - **Name:** `researchmind`
   - **Database Password:** Create a strong password (save it!)
   - **Region:** Choose closest to you
   - **Pricing Plan:** FREE (default)
3. Click **"Create new project"**
4. Wait 2-3 minutes for setup

### Step 3: Create Database Tables

1. In Supabase dashboard, click **"SQL Editor"** (left sidebar)
2. Click **"New query"**
3. Copy and paste this SQL:

```sql
-- Create reports table
CREATE TABLE IF NOT EXISTS reports (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    topic TEXT NOT NULL,
    report_content TEXT NOT NULL,
    feedback TEXT,
    score DECIMAL(3,1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    file_path TEXT,
    file_size_kb DECIMAL(10,2),
    model_used TEXT,
    temperature DECIMAL(3,2),
    report_length TEXT
);

-- Create index for faster searches
CREATE INDEX IF NOT EXISTS idx_reports_topic ON reports(topic);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_score ON reports(score DESC);

-- Create cache table
CREATE TABLE IF NOT EXISTS cache (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    cache_key TEXT UNIQUE NOT NULL,
    cache_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create index for cache lookups
CREATE INDEX IF NOT EXISTS idx_cache_key ON cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at);

-- Create settings table
CREATE TABLE IF NOT EXISTS user_settings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT DEFAULT 'default' UNIQUE,
    model TEXT DEFAULT 'llama-3.3-70b-versatile',
    temperature DECIMAL(3,2) DEFAULT 0.0,
    report_length TEXT DEFAULT 'Medium',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default settings
INSERT INTO user_settings (user_id) VALUES ('default')
ON CONFLICT (user_id) DO NOTHING;

-- Create function to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers
CREATE TRIGGER update_reports_updated_at BEFORE UPDATE ON reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_settings_updated_at BEFORE UPDATE ON user_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

4. Click **"Run"** (or press Ctrl+Enter)
5. You should see: **"Success. No rows returned"**

### Step 4: Get Database Credentials

1. Click **"Settings"** (left sidebar)
2. Click **"Database"**
3. Scroll to **"Connection string"**
4. Copy the **"URI"** (looks like: `postgresql://postgres:[YOUR-PASSWORD]@...`)
5. **Save this!** You'll need it later

**Your database is ready!** ✅

---

## 📁 Part 2: Prepare Code for Deployment

### Step 1: Create Database Module

Create a new file `database.py`:

```python
"""
Database Module
Handles all database operations using Supabase PostgreSQL.
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from utils import logger

def get_db_connection():
    """Get database connection."""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.warning("DATABASE_URL not set, using file-based storage")
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
                'report_length': row['report_length']
            })
        
        cursor.close()
        conn.close()
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
            return {
                'topic': row['topic'],
                'report': row['report_content'],
                'feedback': row['feedback'],
                'score': float(row['score']) if row['score'] else None,
                'created_at': row['created_at']
            }
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
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Report deleted: {report_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete report: {e}")
        if conn:
            conn.close()
        return False

def search_reports(query: str, min_score: float = None) -> List[Dict]:
    """Search reports by topic."""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        sql = """
            SELECT id, topic, score, created_at
            FROM reports
            WHERE topic ILIKE %s
        """
        params = [f'%{query}%']
        
        if min_score is not None:
            sql += " AND score >= %s"
            params.append(min_score)
        
        sql += " ORDER BY created_at DESC LIMIT 50"
        
        cursor.execute(sql, params)
        
        reports = []
        for row in cursor.fetchall():
            reports.append({
                'id': str(row['id']),
                'topic': row['topic'],
                'score': float(row['score']) if row['score'] else None,
                'timestamp': row['created_at'],
                'relative_time': get_relative_time(row['created_at'])
            })
        
        cursor.close()
        conn.close()
        return reports
    except Exception as e:
        logger.error(f"Search failed: {e}")
        if conn:
            conn.close()
        return []

def get_relative_time(timestamp: datetime) -> str:
    """Convert timestamp to relative time."""
    now = datetime.now(timestamp.tzinfo)
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
    else:
        return timestamp.strftime('%Y-%m-%d')
```

### Step 2: Update requirements.txt

Add database dependency:

```txt
# Database
psycopg2-binary>=2.9.9
```

### Step 3: Create .streamlit/config.toml

Create folder `.streamlit` and file `config.toml`:

```toml
[theme]
primaryColor = "#ff8c32"
backgroundColor = "#0a0a0f"
secondaryBackgroundColor = "#1a1a1f"
textColor = "#e8e4dc"
font = "sans serif"

[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = true
```

### Step 4: Create .gitignore

```
.env
.venv/
__pycache__/
*.pyc
.cache/
logs/
reports/
*.log
.DS_Store
*.pdf
.streamlit/secrets.toml
```

---

## 🐙 Part 3: Push to GitHub

### Step 1: Initialize Git (if not already)

```bash
git init
git add .
git commit -m "Initial commit - ResearchMind v2.0"
```

### Step 2: Create GitHub Repository

1. Go to [github.com](https://github.com)
2. Click **"+"** → **"New repository"**
3. Name: `researchmind`
4. Description: "AI-powered research assistant"
5. **Public** (required for free Streamlit hosting)
6. **Don't** initialize with README (you already have one)
7. Click **"Create repository"**

### Step 3: Push Code

```bash
git remote add origin https://github.com/YOUR_USERNAME/researchmind.git
git branch -M main
git push -u origin main
```

**Your code is on GitHub!** ✅

---

## ☁️ Part 4: Deploy to Streamlit Cloud

### Step 1: Sign Up for Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"Sign up"**
3. **Sign in with GitHub** (recommended)
4. Authorize Streamlit

### Step 2: Deploy Your App

1. Click **"New app"**
2. Select:
   - **Repository:** `YOUR_USERNAME/researchmind`
   - **Branch:** `main`
   - **Main file path:** `app.py`
3. Click **"Advanced settings"**

### Step 3: Add Secrets

In the **Secrets** section, paste this (replace with your actual values):

```toml
# API Keys
GROQ_API_KEY = "your_groq_api_key_here"
TAVILY_API_KEY = "your_tavily_api_key_here"

# Database
DATABASE_URL = "postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres"

# Model Settings
GROQ_MODEL = "llama-3.3-70b-versatile"
MODEL_TEMPERATURE = "0.0"
MAX_SEARCH_RESULTS = "5"
ENABLE_CACHE = "true"
```

**Important:** Replace:
- `your_groq_api_key_here` with your actual Groq key
- `your_tavily_api_key_here` with your actual Tavily key
- `DATABASE_URL` with your Supabase connection string

### Step 4: Deploy!

1. Click **"Deploy!"**
2. Wait 2-5 minutes
3. Your app will be live at: `https://YOUR_USERNAME-researchmind-app-xxxxx.streamlit.app`

**Your app is LIVE!** 🎉

---

## ✅ Part 5: Verify Deployment

### Test Checklist

1. **Open your app URL**
   - App loads successfully ✅
   - No error messages ✅

2. **Test Research**
   - Enter a topic
   - Click "Run Research Pipeline"
   - Wait for completion
   - Report generates successfully ✅

3. **Test Database**
   - Go to History tab
   - Report appears in history ✅
   - Search works ✅
   - Filter works ✅

4. **Test Downloads**
   - Download Markdown ✅
   - Download TXT ✅
   - Download PDF ✅

5. **Test Settings**
   - Change model ✅
   - Adjust temperature ✅
   - Settings persist ✅

---

## 🔧 Part 6: Maintenance & Monitoring

### Monitor Your App

1. **Streamlit Cloud Dashboard**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click on your app
   - View logs, metrics, and status

2. **Supabase Dashboard**
   - Go to [supabase.com](https://supabase.com)
   - Click on your project
   - View database usage, queries, and storage

### Update Your App

When you make changes:

```bash
git add .
git commit -m "Description of changes"
git push
```

Streamlit Cloud will **automatically redeploy** in 1-2 minutes!

### Check Logs

If something goes wrong:

1. **Streamlit Cloud:**
   - App dashboard → "Logs" tab
   - See real-time application logs

2. **Supabase:**
   - Project dashboard → "Logs" tab
   - See database queries and errors

---

## 💰 Free Tier Limits

### Streamlit Cloud (FREE)
- ✅ Unlimited public apps
- ✅ 1GB RAM per app
- ✅ Shared CPU
- ✅ Auto-sleep after inactivity (wakes on visit)
- ✅ Community support

### Supabase (FREE)
- ✅ 500MB database storage
- ✅ 2GB bandwidth per month
- ✅ 50,000 monthly active users
- ✅ 500MB file storage
- ✅ Community support

### Groq (FREE)
- ✅ 14,400 requests per day
- ✅ 30 requests per minute
- ✅ All models available

### Tavily (FREE)
- ✅ 1,000 searches per month
- ✅ All features included

**Total: $0/month for moderate usage** ✅

---

## 🚨 Troubleshooting

### Issue: "Module not found"
**Solution:**
- Check `requirements.txt` has all dependencies
- Redeploy from Streamlit Cloud dashboard

### Issue: "Database connection failed"
**Solution:**
- Verify `DATABASE_URL` in secrets
- Check Supabase project is active
- Test connection string locally

### Issue: "API rate limit"
**Solution:**
- Wait a few minutes
- Check API usage in dashboards
- Consider upgrading if needed

### Issue: "App is slow"
**Solution:**
- Streamlit Cloud apps sleep after inactivity
- First visit after sleep takes 10-20 seconds
- Subsequent visits are fast

### Issue: "Can't see history"
**Solution:**
- Check database connection
- Verify tables were created
- Check Supabase logs

---

## 🎯 Post-Deployment Checklist

- [ ] App is live and accessible
- [ ] Database is connected
- [ ] Research pipeline works
- [ ] History shows reports
- [ ] Downloads work (MD, TXT, PDF)
- [ ] Settings persist
- [ ] No errors in logs
- [ ] Shared URL with others
- [ ] Bookmarked admin dashboards

---

## 📊 Usage Monitoring

### Weekly Checks
- [ ] Check Streamlit Cloud usage
- [ ] Check Supabase database size
- [ ] Review error logs
- [ ] Test app functionality

### Monthly Checks
- [ ] Review API usage (Groq, Tavily)
- [ ] Clean up old reports if needed
- [ ] Update dependencies if needed
- [ ] Backup important data

---

## 🔐 Security Best Practices

### Do's ✅
- ✅ Use Streamlit Cloud secrets for API keys
- ✅ Keep `.env` in `.gitignore`
- ✅ Use strong database password
- ✅ Regularly update dependencies
- ✅ Monitor access logs

### Don'ts ❌
- ❌ Never commit `.env` to Git
- ❌ Never share API keys publicly
- ❌ Never expose database credentials
- ❌ Don't ignore security updates

---

## 🎉 Success!

Your ResearchMind is now:
- ✅ **Deployed** - Live on the internet
- ✅ **Database-backed** - PostgreSQL storage
- ✅ **Free** - $0/month hosting
- ✅ **Scalable** - Handles multiple users
- ✅ **Professional** - Production-ready

**Share your app URL with the world!** 🌍

---

## 📞 Support

### Need Help?
1. Check Streamlit Cloud logs
2. Check Supabase logs
3. Review this guide
4. Check GitHub issues
5. Ask in Streamlit Community

### Useful Links
- **Streamlit Docs:** https://docs.streamlit.io
- **Supabase Docs:** https://supabase.com/docs
- **Streamlit Community:** https://discuss.streamlit.io
- **Your App:** `https://YOUR_USERNAME-researchmind-app-xxxxx.streamlit.app`

---

**Version:** 2.0.0
**Last Updated:** May 20, 2026
**Deployment:** FREE (Streamlit Cloud + Supabase)

*Congratulations on deploying your app!* 🎊
