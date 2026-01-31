#!/usr/bin/env python3
"""
Scraper Metrics Tracker

Tracks the success rate and productivity of each scraping technique.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

METRICS_FILE = Path(__file__).parent.parent / "data" / "scraper_metrics.json"

class ScraperMetrics:
    def __init__(self):
        self.metrics = self._load()
    
    def _load(self) -> Dict:
        """Load existing metrics."""
        if METRICS_FILE.exists():
            with open(METRICS_FILE) as f:
                return json.load(f)
        return {
            "sources": {},
            "runs": [],
            "created_at": datetime.now().isoformat()
        }
    
    def save(self):
        """Save metrics to file."""
        METRICS_FILE.parent.mkdir(exist_ok=True)
        with open(METRICS_FILE, 'w') as f:
            json.dump(self.metrics, f, indent=2, default=str)
    
    def record_run_start(self):
        """Record the start of a scraping run."""
        self.current_run = {
            "started_at": datetime.now().isoformat(),
            "sources": {}
        }
    
    def record_source_attempt(self, source_name: str, technique: str):
        """Record that we attempted to scrape a source."""
        if source_name not in self.metrics["sources"]:
            self.metrics["sources"][source_name] = {
                "technique": technique,
                "attempts": 0,
                "successes": 0,
                "items_found": 0,
                "errors": [],
                "first_seen": datetime.now().isoformat(),
                "last_attempt": None
            }
        
        self.metrics["sources"][source_name]["attempts"] += 1
        self.metrics["sources"][source_name]["last_attempt"] = datetime.now().isoformat()
        
        # Also track in current run
        if "current_run" in dir(self):
            if source_name not in self.current_run["sources"]:
                self.current_run["sources"][source_name] = {
                    "success": False,
                    "items": 0,
                    "error": None
                }
    
    def record_source_success(self, source_name: str, items_found: int = 0):
        """Record successful scrape."""
        if source_name in self.metrics["sources"]:
            self.metrics["sources"][source_name]["successes"] += 1
            self.metrics["sources"][source_name]["items_found"] += items_found
        
        if "current_run" in dir(self) and source_name in self.current_run["sources"]:
            self.current_run["sources"][source_name]["success"] = True
            self.current_run["sources"][source_name]["items"] = items_found
    
    def record_source_error(self, source_name: str, error: str):
        """Record scrape error."""
        if source_name in self.metrics["sources"]:
            self.metrics["sources"][source_name]["errors"].append({
                "time": datetime.now().isoformat(),
                "error": error
            })
            # Keep only last 10 errors
            self.metrics["sources"][source_name]["errors"] = \
                self.metrics["sources"][source_name]["errors"][-10:]
        
        if "current_run" in dir(self) and source_name in self.current_run["sources"]:
            self.current_run["sources"][source_name]["error"] = error
    
    def record_run_end(self, total_items: int):
        """Record end of scraping run."""
        if "current_run" in dir(self):
            self.current_run["ended_at"] = datetime.now().isoformat()
            self.current_run["total_items"] = total_items
            self.metrics["runs"].append(self.current_run)
            # Keep only last 50 runs
            self.metrics["runs"] = self.metrics["runs"][-50:]
            delattr(self, "current_run")
    
    def get_summary(self) -> Dict:
        """Get productivity summary for all sources."""
        summary = {
            "generated_at": datetime.now().isoformat(),
            "sources": {},
            "overall": {
                "total_sources": len(self.metrics["sources"]),
                "total_attempts": 0,
                "total_successes": 0,
                "total_items": 0
            }
        }
        
        for source_name, data in self.metrics["sources"].items():
            attempts = data["attempts"]
            successes = data["successes"]
            items = data["items_found"]
            
            success_rate = (successes / attempts * 100) if attempts > 0 else 0
            items_per_success = (items / successes) if successes > 0 else 0
            
            # Calculate trend from last 5 runs
            recent_successes = 0
            recent_items = 0
            recent_runs = [r for r in self.metrics["runs"] if source_name in r.get("sources", {})][-5:]
            for run in recent_runs:
                source_data = run["sources"].get(source_name, {})
                if source_data.get("success"):
                    recent_successes += 1
                    recent_items += source_data.get("items", 0)
            
            summary["sources"][source_name] = {
                "technique": data["technique"],
                "attempts": attempts,
                "successes": successes,
                "success_rate": round(success_rate, 1),
                "items_found": items,
                "items_per_success": round(items_per_success, 2),
                "recent_success_rate": round(recent_successes / len(recent_runs) * 100, 1) if recent_runs else 0,
                "recent_items": recent_items,
                "last_attempt": data["last_attempt"],
                "status": "active" if success_rate > 50 else "struggling" if attempts > 5 else "new"
            }
            
            summary["overall"]["total_attempts"] += attempts
            summary["overall"]["total_successes"] += successes
            summary["overall"]["total_items"] += items
        
        # Overall success rate
        total_attempts = summary["overall"]["total_attempts"]
        total_successes = summary["overall"]["total_successes"]
        summary["overall"]["success_rate"] = round(
            (total_successes / total_attempts * 100), 1
        ) if total_attempts > 0 else 0
        
        return summary


# Singleton instance
_metrics = None

def get_metrics() -> ScraperMetrics:
    """Get or create metrics instance."""
    global _metrics
    if _metrics is None:
        _metrics = ScraperMetrics()
    return _metrics
