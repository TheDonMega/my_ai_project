#!/usr/bin/env python3
"""
Knowledge Base Training and Indexing Script
This script helps optimize the knowledge base for better AI performance
"""

import os
import json
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

class KnowledgeBaseTrainer:
    def __init__(self, knowledge_base_path: str = "/app/knowledge_base"):
        self.knowledge_base_path = knowledge_base_path
        self.index_file = "/app/knowledge_base_index.json"
        self.metadata_file = "/app/knowledge_metadata.json"
        self.history_file = "/app/training_history.json"
        self.feedback_learning_file = "/app/feedback_learning.json"
        
    def load_training_history(self) -> List[Dict[str, Any]]:
        """Load training history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading training history: {e}")
        return []
    
    def save_training_history(self, history: List[Dict[str, Any]]):
        """Save training history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error saving training history: {e}")
    
    def add_training_record(self, documents_processed: int, duration: float, success: bool = True):
        """Add a new training record to history"""
        history = self.load_training_history()
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'documents_processed': documents_processed,
            'duration': duration,
            'success': success
        }
        
        history.append(record)
        
        # Keep only last 50 records
        if len(history) > 50:
            history = history[-50:]
        
        self.save_training_history(history)
        
    def scan_knowledge_base(self) -> Dict[str, Any]:
        """Scan the knowledge base and create an index"""
        print("🔍 Scanning knowledge base...")
        
        index = {
            "last_updated": datetime.now().isoformat(),
            "total_files": 0,
            "total_size": 0,
            "categories": {},
            "files": {}
        }
        
        if not os.path.exists(self.knowledge_base_path):
            print(f"❌ Knowledge base path not found: {self.knowledge_base_path}")
            return index
            
        for root, dirs, files in os.walk(self.knowledge_base_path):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.knowledge_base_path)
                    
                    # Get file stats
                    stat = os.stat(file_path)
                    file_size = stat.st_size
                    
                    # Calculate file hash for change detection
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        file_hash = hashlib.md5(content.encode()).hexdigest()
                    
                    # Extract category from folder structure
                    folder_parts = relative_path.split(os.sep)
                    category = folder_parts[0] if len(folder_parts) > 1 else "root"
                    
                    # Analyze content
                    content_analysis = self.analyze_content(content)
                    
                    file_info = {
                        "path": relative_path,
                        "size": file_size,
                        "hash": file_hash,
                        "category": category,
                        "last_modified": stat.st_mtime,
                        "word_count": len(content.split()),
                        "content_analysis": content_analysis
                    }
                    
                    index["files"][relative_path] = file_info
                    index["total_files"] += 1
                    index["total_size"] += file_size
                    
                    # Track categories
                    if category not in index["categories"]:
                        index["categories"][category] = {
                            "file_count": 0,
                            "total_size": 0,
                            "files": []
                        }
                    index["categories"][category]["file_count"] += 1
                    index["categories"][category]["total_size"] += file_size
                    index["categories"][category]["files"].append(relative_path)
        
        print(f"✅ Scanned {index['total_files']} files in {len(index['categories'])} categories")
        return index
    
    def analyze_content(self, content: str) -> Dict[str, Any]:
        """Analyze content for better indexing"""
        lines = content.split('\n')
        headers = [line.strip() for line in lines if line.strip().startswith('#')]
        
        # Extract key topics from headers
        topics = []
        for header in headers:
            # Remove markdown symbols and get clean topic
            topic = header.lstrip('#').strip()
            if topic:
                topics.append(topic)
        
        # Count code blocks, links, images
        code_blocks = content.count('```')
        links = content.count('http')
        images = content.count('![')
        
        return {
            "topics": topics,
            "headers": len(headers),
            "code_blocks": code_blocks // 2,  # Each block has opening and closing
            "links": links,
            "images": images,
            "has_code": code_blocks > 0,
            "has_links": links > 0,
            "has_images": images > 0
        }
    
    def save_index(self, index: Dict[str, Any]):
        """Save the index to file"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
            print(f"✅ Index saved to {self.index_file}")
        except Exception as e:
            print(f"❌ Error saving index: {e}")
    
    def load_index(self) -> Dict[str, Any]:
        """Load existing index"""
        try:
            if os.path.exists(self.index_file):
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading index: {e}")
        return {}
    
    def check_for_changes(self, new_index: Dict[str, Any]) -> List[str]:
        """Check for changes in the knowledge base"""
        old_index = self.load_index()
        changed_files = []
        
        # Ensure old_index has the required structure
        if not old_index or "files" not in old_index:
            # If no old index or no files, all new files are considered changed
            return list(new_index["files"].keys())
        
        for file_path, file_info in new_index["files"].items():
            if file_path in old_index["files"]:
                old_hash = old_index["files"][file_path]["hash"]
                if file_info["hash"] != old_hash:
                    changed_files.append(file_path)
            else:
                changed_files.append(file_path)
        
        return changed_files
    
    def create_search_metadata(self, index: Dict[str, Any]):
        """Create metadata for better search performance"""
        metadata = {
            "search_keywords": {},
            "category_keywords": {},
            "file_relationships": {}
        }
        
        # Extract keywords from topics and headers
        for file_path, file_info in index["files"].items():
            topics = file_info["content_analysis"]["topics"]
            category = file_info["category"]
            
            # Add keywords from topics
            for topic in topics:
                words = topic.lower().split()
                for word in words:
                    if len(word) > 3:  # Skip short words
                        if word not in metadata["search_keywords"]:
                            metadata["search_keywords"][word] = []
                        metadata["search_keywords"][word].append(file_path)
            
            # Add category keywords
            if category not in metadata["category_keywords"]:
                metadata["category_keywords"][category] = []
            metadata["category_keywords"][category].append(file_path)
        
        # Save metadata
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            print(f"✅ Search metadata saved to {self.metadata_file}")
        except Exception as e:
            print(f"❌ Error saving metadata: {e}")
    
    def train(self):
        """Main training function"""
        print("🚀 Starting knowledge base training...")
        
        start_time = time.time()
        
        try:
            # Scan knowledge base
            new_index = self.scan_knowledge_base()
            
            # Check for changes
            changed_files = self.check_for_changes(new_index)
            
            if changed_files:
                print(f"📝 Found {len(changed_files)} changed/new files:")
                for file_path in changed_files[:5]:  # Show first 5
                    print(f"  - {file_path}")
                if len(changed_files) > 5:
                    print(f"  ... and {len(changed_files) - 5} more")
            else:
                print("✅ No changes detected in knowledge base")
            
            # Analyze feedback patterns for learning
            print("🧠 Analyzing feedback patterns for learning...")
            feedback_patterns = self.analyze_feedback_patterns()
            
            if feedback_patterns:
                print(f"📊 Analyzed {len(feedback_patterns.get('high_rated_queries', []))} high-rated and {len(feedback_patterns.get('low_rated_queries', []))} low-rated responses")
                print(f"🔍 Found {len(set(feedback_patterns.get('common_issues', [])))} common issues to avoid")
            else:
                print("ℹ️  No feedback data available for learning")
            
            # Save index
            self.save_index(new_index)
            
            # Create enhanced metadata with feedback insights
            print("📈 Creating feedback-enhanced metadata...")
            enhanced_metadata = self.create_feedback_enhanced_metadata(new_index, feedback_patterns)
            
            # Save enhanced metadata
            try:
                with open(self.metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(enhanced_metadata, f, indent=2, ensure_ascii=False)
                print(f"✅ Enhanced metadata saved to {self.metadata_file}")
            except Exception as e:
                print(f"❌ Error saving enhanced metadata: {e}")
            
            # Save feedback learning data
            if feedback_patterns:
                self.save_feedback_learning_data(feedback_patterns)
            
            # Calculate training duration
            duration = time.time() - start_time
            
            # Save training record
            self.add_training_record(
                documents_processed=new_index['total_files'],
                duration=duration,
                success=True
            )
            
            # Print summary
            print("\n📊 Knowledge Base Summary:")
            print(f"  Total files: {new_index['total_files']}")
            print(f"  Total size: {new_index['total_size'] / 1024:.1f} KB")
            print(f"  Categories: {len(new_index['categories'])}")
            print(f"  Training duration: {duration:.2f} seconds")
            
            if feedback_patterns:
                print(f"  Feedback analyzed: {len(feedback_patterns.get('high_rated_queries', [])) + len(feedback_patterns.get('low_rated_queries', []))} responses")
                print(f"  Learning patterns: {len(feedback_patterns.get('successful_patterns', []))} successful patterns")
            
            for category, info in new_index['categories'].items():
                print(f"    - {category}: {info['file_count']} files")
            
            print("\n✅ Training completed with feedback learning!")
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Training failed: {e}")
            
            # Save failed training record
            self.add_training_record(
                documents_processed=0,
                duration=duration,
                success=False
            )
            
            raise e

    def get_training_status(self) -> Dict[str, Any]:
        """Get current training status and statistics"""
        try:
            index = self.load_index()
            history = self.load_training_history()
            
            status = {
                'is_trained': len(index.get('files', {})) > 0,
                'total_documents': index.get('total_files', 0),
                'categories': len(index.get('categories', {})),
                'last_training': None,
                'training_count': len(history),
                'total_size': index.get('total_size', 0)
            }
            
            if history:
                status['last_training'] = history[-1]['timestamp']
            
            return status
        except Exception as e:
            print(f"Error getting training status: {e}")
            return {
                'is_trained': False,
                'total_documents': 0,
                'categories': 0,
                'last_training': None,
                'training_count': 0,
                'total_size': 0
            }

    def load_feedback_data(self) -> Dict[str, Any]:
        """Load feedback data for learning"""
        try:
            from feedback_system import feedback_system
            if hasattr(feedback_system, 'get_all_feedback'):
                return feedback_system.get_all_feedback()
        except Exception as e:
            print(f"⚠️  Error loading feedback data: {e}")
        return {}
    
    def analyze_feedback_patterns(self) -> Dict[str, Any]:
        """Analyze feedback patterns to improve future responses"""
        feedback_data = self.load_feedback_data()
        
        if not feedback_data or not feedback_data.get('feedback_entries'):
            return {}
        
        patterns = {
            'high_rated_queries': [],
            'low_rated_queries': [],
            'common_issues': [],
            'successful_patterns': [],
            'query_improvements': {}
        }
        
        for entry in feedback_data['feedback_entries']:
            rating = entry.get('rating', 0)
            query = entry.get('user_question', '').lower()
            response = entry.get('ai_response', '')
            feedback_text = entry.get('feedback_text', '').lower()
            
            # Analyze high-rated responses (4-5 stars)
            if rating >= 4:
                patterns['high_rated_queries'].append({
                    'query': query,
                    'rating': rating,
                    'feedback': feedback_text
                })
                patterns['successful_patterns'].append({
                    'query_type': self._categorize_query(query),
                    'rating': rating
                })
            
            # Analyze low-rated responses (1-2 stars)
            elif rating <= 2:
                patterns['low_rated_queries'].append({
                    'query': query,
                    'rating': rating,
                    'feedback': feedback_text
                })
                
                # Extract common issues from feedback
                if feedback_text:
                    issues = self._extract_issues_from_feedback(feedback_text)
                    patterns['common_issues'].extend(issues)
            
            # Store query improvements
            if feedback_text and 'better' in feedback_text or 'improve' in feedback_text:
                patterns['query_improvements'][query] = {
                    'original_rating': rating,
                    'feedback': feedback_text,
                    'suggested_improvements': self._extract_improvements(feedback_text)
                }
        
        return patterns
    
    def _categorize_query(self, query: str) -> str:
        """Categorize query type for pattern analysis"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['how', 'what', 'why', 'when', 'where']):
            return 'question'
        elif any(word in query_lower for word in ['explain', 'describe', 'tell me about']):
            return 'explanation'
        elif any(word in query_lower for word in ['find', 'search', 'look for']):
            return 'search'
        elif any(word in query_lower for word in ['compare', 'difference', 'vs']):
            return 'comparison'
        else:
            return 'general'
    
    def _extract_issues_from_feedback(self, feedback: str) -> List[str]:
        """Extract common issues from feedback text"""
        issues = []
        feedback_lower = feedback.lower()
        
        if 'not relevant' in feedback_lower or 'irrelevant' in feedback_lower:
            issues.append('irrelevant_response')
        if 'incomplete' in feedback_lower or 'missing' in feedback_lower:
            issues.append('incomplete_response')
        if 'confusing' in feedback_lower or 'unclear' in feedback_lower:
            issues.append('unclear_response')
        if 'wrong' in feedback_lower or 'incorrect' in feedback_lower:
            issues.append('incorrect_information')
        if 'too long' in feedback_lower or 'verbose' in feedback_lower:
            issues.append('too_verbose')
        if 'too short' in feedback_lower or 'brief' in feedback_lower:
            issues.append('too_brief')
        
        return issues
    
    def _extract_improvements(self, feedback: str) -> List[str]:
        """Extract suggested improvements from feedback"""
        improvements = []
        feedback_lower = feedback.lower()
        
        if 'more detail' in feedback_lower:
            improvements.append('add_more_details')
        if 'examples' in feedback_lower:
            improvements.append('include_examples')
        if 'simpler' in feedback_lower or 'easier' in feedback_lower:
            improvements.append('simplify_language')
        if 'structure' in feedback_lower or 'organize' in feedback_lower:
            improvements.append('better_structure')
        
        return improvements
    
    def create_feedback_enhanced_metadata(self, index: Dict[str, Any], feedback_patterns: Dict[str, Any]):
        """Create enhanced metadata using feedback patterns"""
        enhanced_metadata = {
            "search_keywords": {},
            "category_keywords": {},
            "file_relationships": {},
            "feedback_insights": {
                "query_patterns": feedback_patterns.get('successful_patterns', []),
                "common_issues": list(set(feedback_patterns.get('common_issues', []))),
                "query_improvements": feedback_patterns.get('query_improvements', {}),
                "high_rated_queries": feedback_patterns.get('high_rated_queries', []),
                "low_rated_queries": feedback_patterns.get('low_rated_queries', [])
            },
            "response_guidelines": self._generate_response_guidelines(feedback_patterns)
        }
        
        # Extract keywords from topics and headers
        for file_path, file_info in index["files"].items():
            topics = file_info["content_analysis"]["topics"]
            category = file_info["category"]
            
            # Add keywords from topics
            for topic in topics:
                words = topic.lower().split()
                for word in words:
                    if len(word) > 3:  # Skip short words
                        if word not in enhanced_metadata["search_keywords"]:
                            enhanced_metadata["search_keywords"][word] = []
                        enhanced_metadata["search_keywords"][word].append(file_path)
            
            # Add category keywords
            if category not in enhanced_metadata["category_keywords"]:
                enhanced_metadata["category_keywords"][category] = []
            enhanced_metadata["category_keywords"][category].append(file_path)
        
        return enhanced_metadata
    
    def _generate_response_guidelines(self, feedback_patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response guidelines based on feedback patterns"""
        guidelines = {
            "response_length": "medium",  # default
            "detail_level": "standard",
            "include_examples": False,
            "structure_style": "paragraphs",
            "avoid_issues": []
        }
        
        # Analyze common issues to create avoidance guidelines
        common_issues = feedback_patterns.get('common_issues', [])
        if 'too_verbose' in common_issues:
            guidelines["response_length"] = "concise"
        if 'too_brief' in common_issues:
            guidelines["response_length"] = "detailed"
        if 'unclear_response' in common_issues:
            guidelines["structure_style"] = "bullet_points"
        if 'incomplete_response' in common_issues:
            guidelines["detail_level"] = "comprehensive"
        
        # Set avoidance guidelines
        guidelines["avoid_issues"] = list(set(common_issues))
        
        return guidelines
    
    def save_feedback_learning_data(self, feedback_patterns: Dict[str, Any]):
        """Save feedback learning data for future use"""
        try:
            learning_data = {
                "last_updated": datetime.now().isoformat(),
                "feedback_patterns": feedback_patterns,
                "learning_summary": {
                    "total_feedback_analyzed": len(feedback_patterns.get('high_rated_queries', [])) + 
                                              len(feedback_patterns.get('low_rated_queries', [])),
                    "successful_patterns": len(feedback_patterns.get('successful_patterns', [])),
                    "common_issues": len(set(feedback_patterns.get('common_issues', []))),
                    "query_improvements": len(feedback_patterns.get('query_improvements', {}))
                }
            }
            
            with open(self.feedback_learning_file, 'w', encoding='utf-8') as f:
                json.dump(learning_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Feedback learning data saved to {self.feedback_learning_file}")
        except Exception as e:
            print(f"❌ Error saving feedback learning data: {e}")
    
    def load_feedback_learning_data(self) -> Dict[str, Any]:
        """Load feedback learning data"""
        try:
            if os.path.exists(self.feedback_learning_file):
                with open(self.feedback_learning_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading feedback learning data: {e}")
        return {}

def main():
    """Main function"""
    trainer = KnowledgeBaseTrainer()
    trainer.train()

if __name__ == "__main__":
    main() 