"""
Storage layer for scraped content - SQLite + export utilities.
"""
import aiosqlite
import json
import yaml
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class ScrapeStorage:
    """Handles storage and retrieval of scraped content."""
    
    def __init__(self, db_path: str = "data/scraper.db"):
        """Initialize storage with SQLite database."""
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    async def init_db(self):
        """Create database schema."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS scrapes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_name TEXT,
                    url TEXT,
                    depth INTEGER,
                    extracted_content TEXT,
                    matched BOOLEAN,
                    timestamp REAL,
                    UNIQUE(job_name, url)
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS scrape_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_name TEXT UNIQUE,
                    config TEXT,
                    started_at REAL,
                    completed_at REAL,
                    total_pages INTEGER,
                    matched_pages INTEGER
                )
            """)
            
            # Full-text search for content
            await db.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS content_fts 
                USING fts5(url, content, job_name)
            """)
            
            await db.commit()
    
    async def save_page(self, job_name: str, page):
        """Save a scraped page to database."""
        async with aiosqlite.connect(self.db_path) as db:
            content_json = json.dumps(page.extracted_content) if page.extracted_content else None
            
            await db.execute("""
                INSERT OR REPLACE INTO scrapes 
                (job_name, url, depth, extracted_content, matched, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (job_name, page.url, page.depth, content_json, page.matched, page.timestamp))
            
            # Add to FTS index
            if page.extracted_content:
                content_text = json.dumps(page.extracted_content)
                await db.execute("""
                    INSERT INTO content_fts (url, content, job_name)
                    VALUES (?, ?, ?)
                """, (page.url, content_text, job_name))
            
            await db.commit()
    
    async def save_job(self, job_name: str, config: Dict, pages: List):
        """Save scrape job metadata."""
        async with aiosqlite.connect(self.db_path) as db:
            matched_count = sum(1 for p in pages if p.matched)
            
            await db.execute("""
                INSERT OR REPLACE INTO scrape_jobs
                (job_name, config, started_at, completed_at, total_pages, matched_pages)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                job_name,
                json.dumps(config),
                min(p.timestamp for p in pages) if pages else None,
                max(p.timestamp for p in pages) if pages else None,
                len(pages),
                matched_count
            ))
            
            await db.commit()
    
    async def get_job_results(self, job_name: str) -> List[Dict]:
        """Retrieve all results for a scrape job."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT url, depth, extracted_content, matched, timestamp
                FROM scrapes
                WHERE job_name = ?
                ORDER BY timestamp
            """, (job_name,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def search_content(self, query: str, job_name: Optional[str] = None) -> List[Dict]:
        """Full-text search across scraped content."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            if job_name:
                sql = """
                    SELECT url, content, job_name
                    FROM content_fts
                    WHERE content_fts MATCH ? AND job_name = ?
                """
                params = (query, job_name)
            else:
                sql = """
                    SELECT url, content, job_name
                    FROM content_fts
                    WHERE content_fts MATCH ?
                """
                params = (query,)
            
            async with db.execute(sql, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    def export_json(self, pages: List, output_path: str):
        """Export scraped pages as JSON."""
        data = [
            {
                "url": p.url,
                "depth": p.depth,
                "content": p.extracted_content,
                "matched": p.matched,
                "timestamp": datetime.fromtimestamp(p.timestamp).isoformat()
            }
            for p in pages
        ]
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def export_markdown(self, pages: List, output_path: str):
        """Export scraped pages as Markdown."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write("# Scrape Results\n\n")
            f.write(f"Total pages: {len(pages)}\n")
            f.write(f"Matched pages: {sum(1 for p in pages if p.matched)}\n\n")
            
            for page in pages:
                if not page.matched:
                    continue
                
                f.write(f"## {page.url}\n\n")
                f.write(f"**Depth:** {page.depth}  \n")
                f.write(f"**Timestamp:** {datetime.fromtimestamp(page.timestamp).isoformat()}\n\n")
                
                if page.extracted_content:
                    f.write("### Extracted Content\n\n")
                    f.write("```json\n")
                    f.write(json.dumps(page.extracted_content, indent=2))
                    f.write("\n```\n\n")
                
                f.write("---\n\n")
    
    def export_yaml(self, pages: List, output_path: str):
        """Export scraped pages as YAML."""
        data = [
            {
                "url": p.url,
                "depth": p.depth,
                "content": p.extracted_content,
                "matched": p.matched,
                "timestamp": datetime.fromtimestamp(p.timestamp).isoformat()
            }
            for p in pages
        ]
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
