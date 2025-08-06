#!/usr/bin/env python3
"""
Feedback System for AI Response Improvement
Allows users to rate responses and provide specific feedback for continuous learning
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class FeedbackEntry:
    """Feedback entry data structure"""
    id: Optional[int]
    timestamp: str
    user_question: str
    ai_response: str
    rating: int  # 1-5 scale
    feedback_type: str  # 'thumbs_up', 'thumbs_down', 'neutral'
    feedback_text: str
    search_method: str  # 'crewai', 'simple_search', 'enhanced_simple_fallback'
    sources_used: List[str]
    relevance_score: float
    response_length: int
    user_session_id: str

class FeedbackSystem:
    def __init__(self, db_path: str = "/app/feedback.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the feedback database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create feedback table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_question TEXT NOT NULL,
                    ai_response TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    feedback_type TEXT NOT NULL,
                    feedback_text TEXT,
                    search_method TEXT NOT NULL,
                    sources_used TEXT,
                    relevance_score REAL,
                    response_length INTEGER,
                    user_session_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create feedback analysis table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feedback_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_date TEXT NOT NULL,
                    total_feedback INTEGER,
                    avg_rating REAL,
                    thumbs_up_count INTEGER,
                    thumbs_down_count INTEGER,
                    common_issues TEXT,
                    improvement_suggestions TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create search improvement table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_improvements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_pattern TEXT NOT NULL,
                    original_sources TEXT,
                    suggested_sources TEXT,
                    feedback_count INTEGER DEFAULT 1,
                    improvement_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            print("✅ Feedback database initialized")
            
        except Exception as e:
            print(f"❌ Error initializing feedback database: {e}")
    
    def save_feedback(self, feedback: FeedbackEntry) -> bool:
        """Save user feedback to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO feedback (
                    timestamp, user_question, ai_response, rating, feedback_type,
                    feedback_text, search_method, sources_used, relevance_score,
                    response_length, user_session_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                feedback.timestamp,
                feedback.user_question,
                feedback.ai_response,
                feedback.rating,
                feedback.feedback_type,
                feedback.feedback_text,
                feedback.search_method,
                json.dumps(feedback.sources_used),
                feedback.relevance_score,
                feedback.response_length,
                feedback.user_session_id
            ))
            
            conn.commit()
            conn.close()
            print(f"✅ Feedback saved (Rating: {feedback.rating}/5)")
            return True
            
        except Exception as e:
            print(f"❌ Error saving feedback: {e}")
            return False
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get comprehensive feedback statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get total feedback count
            cursor.execute("SELECT COUNT(*) FROM feedback")
            total_feedback = cursor.fetchone()[0]
            
            if total_feedback == 0:
                return {
                    "total_feedback": 0,
                    "avg_rating": 0,
                    "rating_distribution": {},
                    "feedback_types": {},
                    "search_methods": {},
                    "recent_feedback": []
                }
            
            # Get average rating
            cursor.execute("SELECT AVG(rating) FROM feedback")
            avg_rating = cursor.fetchone()[0] or 0
            
            # Get rating distribution
            cursor.execute("""
                SELECT rating, COUNT(*) 
                FROM feedback 
                GROUP BY rating 
                ORDER BY rating
            """)
            rating_distribution = dict(cursor.fetchall())
            
            # Get feedback type distribution
            cursor.execute("""
                SELECT feedback_type, COUNT(*) 
                FROM feedback 
                GROUP BY feedback_type
            """)
            feedback_types = dict(cursor.fetchall())
            
            # Get search method distribution
            cursor.execute("""
                SELECT search_method, COUNT(*) 
                FROM feedback 
                GROUP BY search_method
            """)
            search_methods = dict(cursor.fetchall())
            
            # Get recent feedback (last 10)
            cursor.execute("""
                SELECT user_question, ai_response, rating, feedback_type, feedback_text, timestamp
                FROM feedback 
                ORDER BY timestamp DESC 
                LIMIT 10
            """)
            recent_feedback = []
            for row in cursor.fetchall():
                recent_feedback.append({
                    "user_question": row[0],
                    "ai_response": row[1],
                    "rating": row[2],
                    "feedback_type": row[3],
                    "feedback_text": row[4],
                    "timestamp": row[5]
                })
            
            conn.close()
            
            return {
                "total_feedback": total_feedback,
                "avg_rating": round(avg_rating, 2),
                "rating_distribution": rating_distribution,
                "feedback_types": feedback_types,
                "search_methods": search_methods,
                "recent_feedback": recent_feedback
            }
            
        except Exception as e:
            print(f"❌ Error getting feedback stats: {e}")
            return {}
    
    def get_all_feedback(self) -> Dict[str, Any]:
        """Get all feedback data for learning purposes"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all feedback entries
            cursor.execute("""
                SELECT user_question, ai_response, rating, feedback_type, feedback_text, 
                       search_method, sources_used, relevance_score, timestamp
                FROM feedback 
                ORDER BY timestamp DESC
            """)
            
            feedback_entries = []
            for row in cursor.fetchall():
                feedback_entries.append({
                    "user_question": row[0],
                    "ai_response": row[1],
                    "rating": row[2],
                    "feedback_type": row[3],
                    "feedback_text": row[4],
                    "search_method": row[5],
                    "sources_used": row[6].split(',') if row[6] else [],
                    "relevance_score": row[7] or 0.0,
                    "timestamp": row[8]
                })
            
            conn.close()
            
            return {
                "feedback_entries": feedback_entries,
                "total_entries": len(feedback_entries),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error getting all feedback: {e}")
            return {"feedback_entries": [], "total_entries": 0}
    
    def analyze_common_issues(self) -> List[Dict[str, Any]]:
        """Analyze common issues from negative feedback"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT feedback_text, COUNT(*) as count
                FROM feedback 
                WHERE feedback_type = 'thumbs_down' 
                AND feedback_text IS NOT NULL
                GROUP BY feedback_text
                ORDER BY count DESC
                LIMIT 10
            ''')
            
            issues = cursor.fetchall()
            conn.close()
            
            return [{"issue": issue[0], "count": issue[1]} for issue in issues]
            
        except Exception as e:
            print(f"❌ Error analyzing common issues: {e}")
            return []
    
    def get_search_improvements(self, query: str) -> List[Dict[str, Any]]:
        """Get search improvements based on similar queries"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find similar queries that received good feedback
            cursor.execute('''
                SELECT user_question, sources_used, rating
                FROM feedback 
                WHERE rating >= 4 
                AND user_question LIKE ?
                ORDER BY rating DESC, created_at DESC
                LIMIT 5
            ''', (f'%{query}%',))
            
            improvements = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "similar_query": imp[0],
                    "sources_used": json.loads(imp[1]) if imp[1] else [],
                    "rating": imp[2]
                }
                for imp in improvements
            ]
            
        except Exception as e:
            print(f"❌ Error getting search improvements: {e}")
            return []
    
    def generate_improvement_report(self) -> Dict[str, Any]:
        """Generate a comprehensive improvement report"""
        stats = self.get_feedback_stats()
        common_issues = self.analyze_common_issues()
        
        report = {
            "summary": stats,
            "common_issues": common_issues,
            "recommendations": []
        }
        
        # Generate recommendations based on feedback
        if stats.get("thumbs_down", 0) > stats.get("thumbs_up", 0):
            report["recommendations"].append({
                "type": "search_improvement",
                "priority": "high",
                "suggestion": "Consider improving search relevance thresholds and result filtering"
            })
        
        if stats.get("average_rating", 0) < 3.0:
            report["recommendations"].append({
                "type": "response_quality",
                "priority": "high", 
                "suggestion": "Focus on improving response accuracy and relevance"
            })
        
        # Add specific recommendations based on common issues
        for issue in common_issues[:3]:
            if "irrelevant" in issue["issue"].lower():
                report["recommendations"].append({
                    "type": "relevance",
                    "priority": "medium",
                    "suggestion": "Improve relevance scoring and result filtering"
                })
            elif "incomplete" in issue["issue"].lower():
                report["recommendations"].append({
                    "type": "completeness",
                    "priority": "medium",
                    "suggestion": "Enhance search to find more comprehensive information"
                })
        
        return report

# Global feedback system instance
feedback_system = FeedbackSystem()

def save_user_feedback(
    user_question: str,
    ai_response: str,
    rating: int,
    feedback_type: str,
    feedback_text: str = "",
    search_method: str = "unknown",
    sources_used: List[str] = None,
    relevance_score: float = 0.0,
    user_session_id: str = ""
) -> bool:
    """Save user feedback"""
    feedback = FeedbackEntry(
        id=None,
        timestamp=datetime.now().isoformat(),
        user_question=user_question,
        ai_response=ai_response,
        rating=rating,
        feedback_type=feedback_type,
        feedback_text=feedback_text,
        search_method=search_method,
        sources_used=sources_used or [],
        relevance_score=relevance_score,
        response_length=len(ai_response),
        user_session_id=user_session_id
    )
    
    return feedback_system.save_feedback(feedback)

def get_feedback_insights() -> Dict[str, Any]:
    """Get insights from feedback data"""
    return feedback_system.generate_improvement_report() 