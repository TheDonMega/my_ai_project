#!/usr/bin/env python3
"""
Hybrid Search System
Combines LlamaIndex vector search with existing keyword search and feedback system
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Import existing search system - use lazy imports to avoid circular dependency
# from server import search_knowledge_base, load_feedback_enhancement, apply_feedback_enhancement

# Import LlamaIndex manager
from llamaindex_manager import LlamaIndexManager

class HybridSearchSystem:
    def __init__(self, 
                 knowledge_base_path: str = "/app/knowledge_base",
                 vector_store_path: str = "/app/vector_store",
                 ollama_base_url: str = "http://localhost:11434",
                 embedding_model: str = "nomic-embed-text",
                 llm_model: str = "llama2",
                 use_chroma: bool = True,
                 hybrid_weight: float = 0.7):
        """
        Initialize Hybrid Search System
        
        Args:
            knowledge_base_path: Path to knowledge base documents
            vector_store_path: Path to store vector embeddings
            ollama_base_url: Ollama API base URL
            embedding_model: Ollama embedding model name
            llm_model: Ollama LLM model name
            use_chroma: Whether to use ChromaDB (True) or FAISS (False)
            hybrid_weight: Weight for LlamaIndex results vs keyword search (0.0-1.0)
        """
        self.knowledge_base_path = knowledge_base_path
        self.vector_store_path = vector_store_path
        self.ollama_base_url = ollama_base_url
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.use_chroma = use_chroma
        self.hybrid_weight = hybrid_weight
        
        # Initialize LlamaIndex manager
        self.llamaindex_manager = None
        self.llamaindex_available = False
        
        # Performance tracking
        self.search_stats = {
            'total_searches': 0,
            'llamaindex_searches': 0,
            'keyword_searches': 0,
            'hybrid_searches': 0,
            'average_response_time': 0.0,
            'last_search': None
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize LlamaIndex
        self._initialize_llamaindex()
    
    def _initialize_llamaindex(self):
        """Initialize LlamaIndex manager"""
        try:
            self.llamaindex_manager = LlamaIndexManager(
                knowledge_base_path=self.knowledge_base_path,
                vector_store_path=self.vector_store_path,
                ollama_base_url=self.ollama_base_url,
                embedding_model=self.embedding_model,
                llm_model=self.llm_model,
                use_chroma=self.use_chroma
            )
            
            # Try to build index
            build_result = self.llamaindex_manager.build_index()
            if build_result['success']:
                self.llamaindex_available = True
                self.logger.info("✅ LlamaIndex initialized successfully")
                self.logger.info(f"📊 Index stats: {build_result['documents_processed']} docs, {build_result['chunks_created']} chunks")
            else:
                self.logger.warning(f"⚠️ LlamaIndex build failed: {build_result.get('error')}")
                self.llamaindex_available = False
                
        except Exception as e:
            self.logger.error(f"❌ Error initializing LlamaIndex: {e}")
            self.llamaindex_available = False
    
    def search(self, 
               query: str, 
               knowledge_base: List[Dict[str, Any]],
               search_mode: str = "hybrid",
               num_results: int = 5,
               similarity_threshold: float = 0.6) -> Dict[str, Any]:
        """
        Perform hybrid search combining LlamaIndex and keyword search
        
        Args:
            query: Search query
            knowledge_base: List of knowledge base documents
            search_mode: "hybrid", "llamaindex", "keyword", or "fallback"
            num_results: Number of results to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            Dictionary with search results and metadata
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"🔍 Starting {search_mode} search: {query}")
            
            results = {
                'query': query,
                'search_mode': search_mode,
                'results': [],
                'sources': [],
                'search_time': 0,
                'llamaindex_available': self.llamaindex_available,
                'stats': {}
            }
            
            if search_mode == "llamaindex" and self.llamaindex_available:
                # Pure LlamaIndex search
                llamaindex_results = self._llamaindex_search(query, num_results, similarity_threshold)
                results.update(llamaindex_results)
                self.search_stats['llamaindex_searches'] += 1
                
            elif search_mode == "keyword":
                # Pure keyword search
                keyword_results = self._keyword_search(query, knowledge_base, num_results)
                results.update(keyword_results)
                self.search_stats['keyword_searches'] += 1
                
            elif search_mode == "hybrid" and self.llamaindex_available:
                # Hybrid search
                hybrid_results = self._hybrid_search(query, knowledge_base, num_results, similarity_threshold)
                results.update(hybrid_results)
                self.search_stats['hybrid_searches'] += 1
                
            else:
                # Fallback to keyword search
                self.logger.warning("⚠️ Falling back to keyword search")
                keyword_results = self._keyword_search(query, knowledge_base, num_results)
                results.update(keyword_results)
                results['search_mode'] = "fallback"
                self.search_stats['keyword_searches'] += 1
            
            # Update stats
            search_time = time.time() - start_time
            results['search_time'] = search_time
            results['stats'] = self._update_search_stats(search_time)
            
            self.logger.info(f"✅ Search completed in {search_time:.2f}s using {results['search_mode']} mode")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error during search: {e}")
            return {
                'query': query,
                'search_mode': 'error',
                'results': [],
                'sources': [],
                'search_time': time.time() - start_time,
                'error': str(e),
                'llamaindex_available': self.llamaindex_available
            }
    
    def _llamaindex_search(self, 
                          query: str, 
                          num_results: int, 
                          similarity_threshold: float) -> Dict[str, Any]:
        """Perform LlamaIndex vector search"""
        try:
            # Get similar documents from LlamaIndex
            similar_docs = self.llamaindex_manager.get_similar_documents(
                query=query,
                top_k=num_results,
                similarity_threshold=similarity_threshold
            )
            
            # Format results
            results = []
            sources = []
            
            for doc in similar_docs:
                result = {
                    'content': doc['content'],
                    'filename': doc['filename'],
                    'score': doc['score'],
                    'source_type': 'llamaindex_vector',
                    'metadata': doc.get('metadata', {})
                }
                results.append(result)
                
                source = {
                    'content': doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content'],
                    'filename': doc['filename'],
                    'score': doc['score'],
                    'source_type': 'llamaindex_vector'
                }
                sources.append(source)
            
            return {
                'results': results,
                'sources': sources,
                'total_results': len(results),
                'search_method': 'llamaindex_vector'
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error in LlamaIndex search: {e}")
            return {
                'results': [],
                'sources': [],
                'total_results': 0,
                'search_method': 'llamaindex_vector',
                'error': str(e)
            }
    
    def _keyword_search(self, 
                       query: str, 
                       knowledge_base: List[Dict[str, Any]], 
                       num_results: int) -> Dict[str, Any]:
        """Perform keyword-based search using existing system"""
        try:
            # Import here to avoid circular dependency
            from server import search_knowledge_base
            keyword_results = search_knowledge_base(query, knowledge_base, num_results)
            
            # Format results
            results = []
            sources = []
            
            for result in keyword_results:
                formatted_result = {
                    'content': result['section'],
                    'filename': result['filename'],
                    'score': result['score'],
                    'relevance': result['relevance'],
                    'source_type': 'keyword_search',
                    'header': result.get('header', ''),
                    'folder_path': result.get('folder_path', '')
                }
                results.append(formatted_result)
                
                source = {
                    'content': result['section'][:200] + "..." if len(result['section']) > 200 else result['section'],
                    'filename': result['filename'],
                    'score': result['score'],
                    'relevance': result['relevance'],
                    'source_type': 'keyword_search',
                    'header': result.get('header', '')
                }
                sources.append(source)
            
            return {
                'results': results,
                'sources': sources,
                'total_results': len(results),
                'search_method': 'keyword_search'
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error in keyword search: {e}")
            return {
                'results': [],
                'sources': [],
                'total_results': 0,
                'search_method': 'keyword_search',
                'error': str(e)
            }
    
    def _hybrid_search(self, 
                      query: str, 
                      knowledge_base: List[Dict[str, Any]], 
                      num_results: int,
                      similarity_threshold: float) -> Dict[str, Any]:
        """Perform hybrid search combining both methods"""
        try:
            # Get results from both methods
            llamaindex_results = self._llamaindex_search(query, num_results * 2, similarity_threshold)
            keyword_results = self._keyword_search(query, knowledge_base, num_results * 2)
            
            # Combine and rank results
            combined_results = self._combine_search_results(
                llamaindex_results['results'],
                keyword_results['results'],
                num_results
            )
            
            # Format sources
            sources = []
            for result in combined_results:
                source = {
                    'content': result['content'][:200] + "..." if len(result['content']) > 200 else result['content'],
                    'filename': result['filename'],
                    'score': result['score'],
                    'source_type': result['source_type'],
                    'combined_score': result.get('combined_score', result['score'])
                }
                sources.append(source)
            
            return {
                'results': combined_results,
                'sources': sources,
                'total_results': len(combined_results),
                'search_method': 'hybrid',
                'llamaindex_results': len(llamaindex_results['results']),
                'keyword_results': len(keyword_results['results'])
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error in hybrid search: {e}")
            return {
                'results': [],
                'sources': [],
                'total_results': 0,
                'search_method': 'hybrid',
                'error': str(e)
            }
    
    def _combine_search_results(self, 
                               llamaindex_results: List[Dict], 
                               keyword_results: List[Dict], 
                               num_results: int) -> List[Dict]:
        """Combine and rank results from both search methods"""
        combined = []
        
        # Normalize scores and add source information
        for result in llamaindex_results:
            result['combined_score'] = result['score'] * self.hybrid_weight
            result['source_weight'] = self.hybrid_weight
            combined.append(result)
        
        for result in keyword_results:
            result['combined_score'] = result['score'] * (1 - self.hybrid_weight)
            result['source_weight'] = 1 - self.hybrid_weight
            combined.append(result)
        
        # Remove duplicates based on filename and content similarity
        unique_results = self._deduplicate_results(combined)
        
        # Sort by combined score
        unique_results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return unique_results[:num_results]
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results based on filename and content similarity"""
        unique_results = []
        seen_files = set()
        
        for result in results:
            filename = result['filename']
            
            # Check if we've seen this file
            if filename in seen_files:
                # Find existing result for this file
                existing = next((r for r in unique_results if r['filename'] == filename), None)
                if existing:
                    # Keep the one with higher combined score
                    if result['combined_score'] > existing['combined_score']:
                        unique_results.remove(existing)
                        unique_results.append(result)
                continue
            
            seen_files.add(filename)
            unique_results.append(result)
        
        return unique_results
    
    def _update_search_stats(self, search_time: float) -> Dict[str, Any]:
        """Update search statistics"""
        self.search_stats['total_searches'] += 1
        self.search_stats['last_search'] = datetime.now().isoformat()
        
        # Update average response time
        current_avg = self.search_stats['average_response_time']
        total_searches = self.search_stats['total_searches']
        self.search_stats['average_response_time'] = (
            (current_avg * (total_searches - 1) + search_time) / total_searches
        )
        
        return {
            'total_searches': self.search_stats['total_searches'],
            'llamaindex_searches': self.search_stats['llamaindex_searches'],
            'keyword_searches': self.search_stats['keyword_searches'],
            'hybrid_searches': self.search_stats['hybrid_searches'],
            'average_response_time': self.search_stats['average_response_time'],
            'llamaindex_available': self.llamaindex_available
        }
    
    def query_with_llamaindex(self, 
                             query: str, 
                             use_cache: bool = True,
                             similarity_threshold: float = 0.7,
                             top_k: int = 5) -> Dict[str, Any]:
        """Query using LlamaIndex with full RAG pipeline"""
        if not self.llamaindex_available:
            return {
                'success': False,
                'error': 'LlamaIndex not available',
                'response': None,
                'sources': []
            }
        
        return self.llamaindex_manager.query(
            query=query,
            use_cache=use_cache,
            similarity_threshold=similarity_threshold,
            top_k=top_k
        )
    
    def rebuild_index(self, force_rebuild: bool = True) -> Dict[str, Any]:
        """Rebuild the LlamaIndex"""
        if not self.llamaindex_manager:
            return {
                'success': False,
                'error': 'LlamaIndex manager not initialized'
            }
        
        result = self.llamaindex_manager.build_index(force_rebuild=force_rebuild)
        
        # Update availability status based on build result
        if result['success']:
            self.llamaindex_available = True
            self.logger.info("✅ LlamaIndex rebuilt successfully and is now available")
        else:
            self.llamaindex_available = False
            self.logger.warning(f"⚠️ LlamaIndex rebuild failed: {result.get('error')}")
        
        return result
    
    def check_llamaindex_availability(self) -> bool:
        """Check if LlamaIndex is available and update status"""
        try:
            if not self.llamaindex_manager:
                self.llamaindex_available = False
                return False
            
            # Check if index exists and is ready
            stats = self.llamaindex_manager.get_stats()
            index_ready = stats['index_info']['index_exists'] and stats['index_info']['query_engine_ready']
            
            self.llamaindex_available = index_ready
            if index_ready:
                self.logger.info("✅ LlamaIndex is available and ready")
            else:
                self.logger.warning("⚠️ LlamaIndex is not ready")
            
            return index_ready
            
        except Exception as e:
            self.logger.error(f"❌ Error checking LlamaIndex availability: {e}")
            self.llamaindex_available = False
            return False

    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        stats = {
            'search_stats': self.search_stats,
            'llamaindex_available': self.llamaindex_available,
            'hybrid_weight': self.hybrid_weight
        }
        
        if self.llamaindex_manager:
            llamaindex_stats = self.llamaindex_manager.get_stats()
            stats['llamaindex_stats'] = llamaindex_stats
        
        return stats
    
    def cleanup_cache(self):
        """Clean up cache in LlamaIndex manager"""
        if self.llamaindex_manager:
            self.llamaindex_manager.cleanup_cache()
