#!/usr/bin/env python3
"""
Search Manager
Handles LlamaIndex vector search
"""

import os
import time
import logging
from typing import Dict, List, Any
from datetime import datetime

from llamaindex_manager import LlamaIndexManager

class SearchManager:
    def __init__(self,
                 knowledge_base_path: str = "/app/knowledge_base",
                 vector_store_path: str = "/app/vector_store",
                 ollama_base_url: str = "http://localhost:11434",
                 embedding_model: str = "nomic-embed-text",
                 llm_model: str = "llama2",
                 use_chroma: bool = True):
        """
        Initialize Search Manager
        """
        self.knowledge_base_path = knowledge_base_path
        self.vector_store_path = vector_store_path
        self.ollama_base_url = ollama_base_url
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.use_chroma = use_chroma

        self.llamaindex_manager = None
        self.llamaindex_available = False

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

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
            build_result = self.llamaindex_manager.build_index()
            if build_result['success']:
                self.llamaindex_available = True
                self.logger.info("✅ LlamaIndex initialized successfully")
            else:
                self.logger.warning(f"⚠️ LlamaIndex build failed: {build_result.get('error')}")
                self.llamaindex_available = False
        except Exception as e:
            self.logger.error(f"❌ Error initializing LlamaIndex: {e}")
            self.llamaindex_available = False

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
        if result['success']:
            self.llamaindex_available = True
            self.logger.info("✅ LlamaIndex rebuilt successfully and is now available")
        else:
            self.llamaindex_available = False
            self.logger.warning(f"⚠️ LlamaIndex rebuild failed: {result.get('error')}")
        return result

    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        stats = {
            'llamaindex_available': self.llamaindex_available,
        }
        if self.llamaindex_manager:
            stats['llamaindex_stats'] = self.llamaindex_manager.get_stats()
        return stats
