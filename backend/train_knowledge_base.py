#!/usr/bin/env python3
"""
Knowledge Base Trainer
Trains the knowledge base by scanning and indexing documents
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class KnowledgeBaseTrainer:
    def __init__(self, knowledge_base_path: str = "/app/knowledge_base"):
        self.knowledge_base_path = knowledge_base_path
        self.index_file = "/app/knowledge_base_index.json"
        self.metadata_file = "/app/knowledge_base_metadata.json"
        self.training_history_file = "/app/training_history.json"
    
    def load_training_history(self) -> List[Dict[str, Any]]:
        """Load training history"""
        try:
            if os.path.exists(self.training_history_file):
                with open(self.training_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading training history: {e}")
        return []
    
    def save_training_history(self, history: List[Dict[str, Any]]):
        """Save training history"""
        try:
            with open(self.training_history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving training history: {e}")
    
    def add_training_record(self, documents_processed: int, duration: float, success: bool = True):
        """Add a training record to history"""
        history = self.load_training_history()
        record = {
            "timestamp": datetime.now().isoformat(),
            "documents_processed": documents_processed,
            "duration": duration,
            "success": success
        }
        history.append(record)
        self.save_training_history(history)
    
    def scan_knowledge_base(self) -> Dict[str, Any]:
        """Scan the knowledge base and create an index"""
        print(f"🔍 Scanning knowledge base at {self.knowledge_base_path}")
        
        index = {
            "files": {},
            "categories": {},
            "total_files": 0,
            "total_size": 0,
            "last_updated": datetime.now().isoformat()
        }
        
        if not os.path.exists(self.knowledge_base_path):
            print(f"❌ Knowledge base path does not exist: {self.knowledge_base_path}")
            return index
        
        try:
            for root, dirs, files in os.walk(self.knowledge_base_path):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, self.knowledge_base_path)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            file_size = len(content.encode('utf-8'))
                            file_stats = os.stat(file_path)
                            
                            # Analyze content
                            analysis = self.analyze_content(content)
                            
                            # Determine category based on folder structure
                            category = os.path.dirname(relative_path) if os.path.dirname(relative_path) else 'root'
                            
                            index["files"][relative_path] = {
                                "size": file_size,
                                "modified": file_stats.st_mtime,
                                "analysis": analysis,
                                "category": category
                            }
                            
                            # Update category stats
                            if category not in index["categories"]:
                                index["categories"][category] = {
                                    "file_count": 0,
                                    "total_size": 0
                                }
                            index["categories"][category]["file_count"] += 1
                            index["categories"][category]["total_size"] += file_size
                            
                            index["total_files"] += 1
                            index["total_size"] += file_size
                            
                        except Exception as e:
                            print(f"⚠️ Error processing {file_path}: {e}")
            
            print(f"✅ Scanned {index['total_files']} files ({index['total_size'] / 1024:.1f} KB)")
            return index
            
        except Exception as e:
            print(f"❌ Error scanning knowledge base: {e}")
            return index
    
    def analyze_content(self, content: str) -> Dict[str, Any]:
        """Analyze document content"""
        lines = content.split('\n')
        headers = [line.strip() for line in lines if line.strip().startswith('#')]
        
        return {
            "line_count": len(lines),
            "word_count": len(content.split()),
            "headers": headers,
            "has_code_blocks": "```" in content,
            "has_links": "[" in content and "]" in content and "(" in content and ")" in content
        }
    
    def save_index(self, index: Dict[str, Any]):
        """Save the knowledge base index"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
            print(f"✅ Index saved to {self.index_file}")
        except Exception as e:
            print(f"❌ Error saving index: {e}")
    
    def load_index(self) -> Dict[str, Any]:
        """Load the knowledge base index"""
        try:
            if os.path.exists(self.index_file):
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading index: {e}")
        return {"files": {}, "categories": {}, "total_files": 0, "total_size": 0}
    
    def check_for_changes(self, new_index: Dict[str, Any]) -> List[str]:
        """Check for changes in the knowledge base"""
        old_index = self.load_index()
        changed_files = []
        
        for file_path, file_info in new_index["files"].items():
            if file_path not in old_index["files"]:
                changed_files.append(f"Added: {file_path}")
            elif old_index["files"][file_path]["modified"] != file_info["modified"]:
                changed_files.append(f"Modified: {file_path}")
        
        for file_path in old_index["files"]:
            if file_path not in new_index["files"]:
                changed_files.append(f"Removed: {file_path}")
        
        return changed_files
    
    def create_search_metadata(self, index: Dict[str, Any]):
        """Create search metadata for better querying"""
        metadata = {
            "search_index": {},
            "categories": index["categories"],
            "file_paths": list(index["files"].keys()),
            "total_files": index["total_files"],
            "total_size": index["total_size"],
            "created_at": datetime.now().isoformat()
        }
        
        # Create search index
        for file_path, file_info in index["files"].items():
            analysis = file_info["analysis"]
            
            # Add headers to search index
            for header in analysis["headers"]:
                if header not in metadata["search_index"]:
                    metadata["search_index"][header] = []
                metadata["search_index"][header].append(file_path)
        
        return metadata
    
    def train(self):
        """Main training function"""
        print("🚀 Starting knowledge base training...")
        start_time = time.time()
        
        try:
            # Scan knowledge base
            new_index = self.scan_knowledge_base()
            
            if new_index["total_files"] == 0:
                print("⚠️ No markdown files found in knowledge base")
                return
            
            # Check for changes
            changed_files = self.check_for_changes(new_index)
            if changed_files:
                print(f"📝 Detected {len(changed_files)} changes:")
                for file_path in changed_files[:5]:
                    print(f"  - {file_path}")
                if len(changed_files) > 5:
                    print(f"  ... and {len(changed_files) - 5} more")
            else:
                print("✅ No changes detected in knowledge base")
            
            # Save index
            self.save_index(new_index)
            
            # Create enhanced metadata
            print("📈 Creating enhanced metadata...")
            enhanced_metadata = self.create_enhanced_metadata(new_index)
            
            # Save enhanced metadata
            try:
                with open(self.metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(enhanced_metadata, f, indent=2, ensure_ascii=False)
                print(f"✅ Enhanced metadata saved to {self.metadata_file}")
            except Exception as e:
                print(f"❌ Error saving enhanced metadata: {e}")
            
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
            
            for category, info in new_index['categories'].items():
                print(f"    - {category}: {info['file_count']} files")
            
            print("\n✅ Training completed!")
            
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
    
    def create_enhanced_metadata(self, index: Dict[str, Any]):
        """Create enhanced metadata without feedback dependencies"""
        enhanced_metadata = {
            "index_info": index,
            "search_metadata": self.create_search_metadata(index),
            "training_info": {
                "last_trained": datetime.now().isoformat(),
                "total_files": index["total_files"],
                "categories": list(index["categories"].keys())
            }
        }
        
        return enhanced_metadata

def main():
    """Main function for standalone execution"""
    trainer = KnowledgeBaseTrainer()
    trainer.train()

if __name__ == "__main__":
    main()
