#!/usr/bin/env python3
"""
LlamaIndex Manager for Advanced RAG System
Handles document loading, vector storage, retrieval, and query processing
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

# LlamaIndex imports
from llama_index.core import (
    VectorStoreIndex, 
    Document, 
    Settings,
    StorageContext,
    load_index_from_storage,
    get_response_synthesizer
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.indices.vector_store import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.vector_stores.faiss import FaissVectorStore
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

# ChromaDB for vector storage
import chromadb
from chromadb.config import Settings as ChromaSettings

class LlamaIndexManager:
    def __init__(self, 
                 knowledge_base_path: str = "/app/knowledge_base",
                 vector_store_path: str = "/app/vector_store",
                 ollama_base_url: str = "http://localhost:11434",
                 embedding_model: str = "nomic-embed-text",
                 llm_model: str = "llama2",
                 use_chroma: bool = True,
                 chunk_size: int = 1024,  # Increased for better context
                 chunk_overlap: int = 200):  # Increased overlap for better continuity
        """
        Initialize LlamaIndex Manager
        
        Args:
            knowledge_base_path: Path to knowledge base documents
            vector_store_path: Path to store vector embeddings
            ollama_base_url: Ollama API base URL
            embedding_model: Ollama embedding model name
            llm_model: Ollama LLM model name
            use_chroma: Whether to use ChromaDB (True) or FAISS (False)
            chunk_size: Size of document chunks
            chunk_overlap: Overlap between chunks
        """
        self.knowledge_base_path = knowledge_base_path
        self.vector_store_path = vector_store_path
        self.ollama_base_url = ollama_base_url
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.use_chroma = use_chroma
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize components
        self.embed_model = None
        self.llm = None
        self.vector_store = None
        self.index = None
        self.query_engine = None
        
        # Performance tracking
        self.indexing_stats = {
            'documents_processed': 0,
            'chunks_created': 0,
            'last_indexed': None,
            'indexing_time': 0
        }
        
        # Cache for performance
        self.response_cache = {}
        self.cache_ttl = 3600  # 1 hour
        self.last_cache_cleanup = time.time()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize LlamaIndex components"""
        try:
            # Initialize embedding model
            self.embed_model = OllamaEmbedding(
                model_name=self.embedding_model,
                base_url=self.ollama_base_url
            )
            self.logger.info(f"✅ Initialized embedding model: {self.embedding_model}")
            
            # Initialize LLM
            self.llm = Ollama(
                model=self.llm_model,
                base_url=self.ollama_base_url,
                request_timeout=60.0
            )
            self.logger.info(f"✅ Initialized LLM: {self.llm_model}")
            
            # Set global settings
            Settings.embed_model = self.embed_model
            Settings.llm = self.llm
            Settings.chunk_size = self.chunk_size
            Settings.chunk_overlap = self.chunk_overlap
            
            # Initialize vector store
            self._initialize_vector_store()
            
        except Exception as e:
            self.logger.error(f"❌ Error initializing LlamaIndex components: {e}")
            raise
    
    def _initialize_vector_store(self):
        """Initialize vector store (ChromaDB or FAISS)"""
        try:
            os.makedirs(self.vector_store_path, exist_ok=True)
            
            if self.use_chroma:
                # Initialize ChromaDB
                chroma_client = chromadb.PersistentClient(
                    path=os.path.join(self.vector_store_path, "chroma_db"),
                    settings=ChromaSettings(anonymized_telemetry=False)
                )
                chroma_collection = chroma_client.get_or_create_collection("knowledge_base")
                self.vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
                # Fix for compatibility issue
                if not hasattr(self.vector_store, '_collection'):
                    self.vector_store._collection = chroma_collection
                self.logger.info("✅ Initialized ChromaDB vector store")
            else:
                # Initialize FAISS
                faiss_path = os.path.join(self.vector_store_path, "faiss_index")
                self.vector_store = FaissVectorStore.from_persist_dir(faiss_path)
                self.logger.info("✅ Initialized FAISS vector store")
                
        except Exception as e:
            self.logger.error(f"❌ Error initializing vector store: {e}")
            raise
    
    def _load_documents_from_knowledge_base(self) -> List[Document]:
        """Load documents from knowledge base directory"""
        documents = []
        
        if not os.path.exists(self.knowledge_base_path):
            self.logger.warning(f"⚠️ Knowledge base path not found: {self.knowledge_base_path}")
            return documents
        
        self.logger.info(f"📚 Loading documents from: {self.knowledge_base_path}")
        
        for root, dirs, files in os.walk(self.knowledge_base_path):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.knowledge_base_path)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Create LlamaIndex Document
                        doc = Document(
                            text=content,
                            metadata={
                                'filename': relative_path,
                                'file_path': file_path,
                                'file_type': 'markdown',
                                'created_at': datetime.now().isoformat()
                            }
                        )
                        documents.append(doc)
                        self.logger.debug(f"📄 Loaded: {relative_path}")
                        
                    except Exception as e:
                        self.logger.error(f"❌ Error loading {file_path}: {e}")
        
        self.logger.info(f"✅ Loaded {len(documents)} documents")
        return documents
    
    def _create_or_load_index(self, documents: List[Document]) -> VectorStoreIndex:
        """Create new index or load existing one"""
        try:
            # Check if index exists
            index_path = os.path.join(self.vector_store_path, "index")
            
            if os.path.exists(index_path) and documents:
                # Load existing index
                storage_context = StorageContext.from_defaults(
                    vector_store=self.vector_store
                )
                self.index = load_index_from_storage(storage_context)
                self.logger.info("✅ Loaded existing index")
            else:
                # Create new index
                if not documents:
                    self.logger.warning("⚠️ No documents to index")
                    return None
                
                # Create storage context
                storage_context = StorageContext.from_defaults(
                    vector_store=self.vector_store
                )
                
                # Create index with documents
                self.index = VectorStoreIndex.from_documents(
                    documents,
                    storage_context=storage_context,
                    show_progress=True
                )
                
                # Save index
                self.index.storage_context.persist(persist_dir=index_path)
                self.logger.info("✅ Created and saved new index")
            
            return self.index
            
        except Exception as e:
            self.logger.error(f"❌ Error creating/loading index: {e}")
            raise
    
    def _setup_query_engine(self):
        """Setup query engine with retriever and response synthesizer"""
        try:
            if not self.index:
                self.logger.error("❌ No index available for query engine setup")
                return None
            
            # Create retriever with optimized settings
            retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=10,  # Increased for better coverage
                vector_store_query_mode="hybrid"
            )
            
            # Create response synthesizer optimized for speed and quality
            response_synthesizer = get_response_synthesizer(
                response_mode="tree_summarize",  # Changed from "compact" to "tree_summarize"
                structured_answer_filtering=False  # Disabled structured filtering
            )
            
            # Create query engine with optimized postprocessing
            self.query_engine = RetrieverQueryEngine(
                retriever=retriever,
                response_synthesizer=response_synthesizer,
                node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.3)]  # Lower cutoff for more results
            )
            
            self.logger.info("✅ Query engine setup complete with optimized settings")
            
        except Exception as e:
            self.logger.error(f"❌ Error setting up query engine: {e}")
            raise
    
    def build_index(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """Build or rebuild the vector index"""
        start_time = time.time()
        
        try:
            self.logger.info("🚀 Starting index build...")
            
            # Load documents
            documents = self._load_documents_from_knowledge_base()
            
            if not documents:
                return {
                    'success': False,
                    'error': 'No documents found to index',
                    'documents_processed': 0,
                    'chunks_created': 0,
                    'indexing_time': 0
                }
            
            # Force rebuild if requested
            if force_rebuild:
                index_path = os.path.join(self.vector_store_path, "index")
                if os.path.exists(index_path):
                    import shutil
                    shutil.rmtree(index_path)
                    self.logger.info("🗑️ Removed existing index for rebuild")
            
            # Create or load index
            self.index = self._create_or_load_index(documents)
            
            if not self.index:
                return {
                    'success': False,
                    'error': 'Failed to create index',
                    'documents_processed': 0,
                    'chunks_created': 0,
                    'indexing_time': 0
                }
            
            # Setup query engine
            self._setup_query_engine()
            
            # Update stats
            indexing_time = time.time() - start_time
            self.indexing_stats.update({
                'documents_processed': len(documents),
                'chunks_created': len(self.index.docstore.docs),
                'last_indexed': datetime.now().isoformat(),
                'indexing_time': indexing_time
            })
            
            self.logger.info(f"✅ Index build complete in {indexing_time:.2f}s")
            
            return {
                'success': True,
                'documents_processed': len(documents),
                'chunks_created': len(self.index.docstore.docs),
                'indexing_time': indexing_time,
                'index_size_mb': self._get_index_size()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error building index: {e}")
            return {
                'success': False,
                'error': str(e),
                'documents_processed': 0,
                'chunks_created': 0,
                'indexing_time': time.time() - start_time
            }
    
    def query(self, 
              query: str, 
              use_cache: bool = True,
              similarity_threshold: float = 0.3,  # Lower default threshold
              top_k: int = 10) -> Dict[str, Any]:  # Increased default top_k
        """
        Query the knowledge base using LlamaIndex
        
        Args:
            query: User query
            use_cache: Whether to use response caching
            similarity_threshold: Minimum similarity score for results
            top_k: Number of top results to retrieve
            
        Returns:
            Dictionary with query results
        """
        start_time = time.time()
        
        try:
            # Check cache
            if use_cache:
                cache_key = self._get_cache_key(query)
                if cache_key in self.response_cache:
                    cached_result = self.response_cache[cache_key]
                    if time.time() - cached_result['timestamp'] < self.cache_ttl:
                        self.logger.info("✅ Using cached response")
                        return cached_result['data']
            
            if not self.index:
                return {
                    'success': False,
                    'error': 'Index not initialized. Please build index first.',
                    'response': None,
                    'sources': [],
                    'query_time': 0
                }
            
            # Get similar documents first (this works)
            similar_docs = self.get_similar_documents(
                query=query,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )
            
            self.logger.info(f"🔍 Retrieved {len(similar_docs)} documents")
            
            if not similar_docs:
                return {
                    'success': True,
                    'response': "I couldn't find any relevant information in the knowledge base.",
                    'sources': [],
                    'query_time': time.time() - start_time,
                    'total_sources': 0,
                    'filtered_sources': 0
                }
            
            # Format documents for LLM (limit to top 1 document and minimal context)
            if similar_docs:
                doc = similar_docs[0]  # Use only the top document
                # Truncate content to very small size
                content = doc['content'][:400] + "..." if len(doc['content']) > 400 else doc['content']
                context_text = f"Document from {doc['filename']}:\n{content}"
            else:
                context_text = "No relevant documents found."
            
            # Create a very simple prompt for the LLM
            prompt = f"""Question: {query}

Context: {context_text}

Answer:"""
            
            # Query the LLM directly with very short timeout
            self.logger.info(f"🔍 Querying LLM with 1 document")
            try:
                # Set a very short timeout for faster responses
                llm_response = self.llm.complete(prompt, timeout=15.0)
                response_text = str(llm_response)
                self.logger.info(f"🔍 LLM response: {response_text[:200]}...")
            except Exception as e:
                self.logger.error(f"❌ LLM query failed: {e}")
                # Fallback: create a simple response from the documents
                if similar_docs:
                    response_text = f"Based on the retrieved documents, here's what I found:\n\n"
                    for i, doc in enumerate(similar_docs[:2], 1):
                        response_text += f"{i}. From {doc['filename']}: {doc['content'][:200]}...\n\n"
                else:
                    response_text = "I couldn't find any relevant information in the knowledge base."
            
            # Format sources
            sources = []
            for doc in similar_docs:
                source_info = {
                    'content': doc['content'],
                    'filename': doc['filename'],
                    'score': doc['score']
                }
                sources.append(source_info)
            
            query_time = time.time() - start_time
            
            result = {
                'success': True,
                'response': response_text,
                'sources': sources,
                'query_time': query_time,
                'total_sources': len(similar_docs),
                'filtered_sources': len(similar_docs)
            }
            
            # Cache result
            if use_cache:
                cache_key = self._get_cache_key(query)
                self.response_cache[cache_key] = {
                    'data': result,
                    'timestamp': time.time()
                }
            
            self.logger.info(f"✅ Query completed in {query_time:.2f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error during query: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': None,
                'sources': [],
                'query_time': time.time() - start_time
            }
    
    def get_similar_documents(self, 
                             query: str, 
                             top_k: int = 5,
                             similarity_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Get similar documents without generating a response"""
        try:
            if not self.index:
                return []
            
            # Create retriever for similarity search
            retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=top_k,
                vector_store_query_mode="hybrid"
            )
            
            # Get similar nodes
            nodes = retriever.retrieve(query)
            
            # Format results
            results = []
            for node in nodes:
                if hasattr(node, 'score') and node.score >= similarity_threshold:
                    result = {
                        'content': node.text,
                        'filename': node.metadata.get('filename', 'Unknown'),
                        'score': node.score,
                        'metadata': node.metadata
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error getting similar documents: {e}")
            return []
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key for query"""
        import hashlib
        return hashlib.md5(query.encode()).hexdigest()
    
    def _get_index_size(self) -> float:
        """Get index size in MB"""
        try:
            index_path = os.path.join(self.vector_store_path, "index")
            if os.path.exists(index_path):
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(index_path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        total_size += os.path.getsize(filepath)
                return total_size / (1024 * 1024)  # Convert to MB
            return 0.0
        except Exception:
            return 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            'indexing_stats': self.indexing_stats,
            'cache_stats': {
                'cache_size': len(self.response_cache),
                'cache_hits': getattr(self, 'cache_hits', 0),
                'cache_misses': getattr(self, 'cache_misses', 0)
            },
            'index_info': {
                'index_exists': self.index is not None,
                'query_engine_ready': self.query_engine is not None,
                'index_size_mb': self._get_index_size(),
                'vector_store_type': 'ChromaDB' if self.use_chroma else 'FAISS'
            },
            'model_info': {
                'embedding_model': self.embedding_model,
                'llm_model': self.llm_model,
                'ollama_base_url': self.ollama_base_url
            }
        }
    
    def cleanup_cache(self):
        """Clean up expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, value in self.response_cache.items()
            if current_time - value['timestamp'] > self.cache_ttl
        ]
        
        for key in expired_keys:
            del self.response_cache[key]
        
        if expired_keys:
            self.logger.info(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")
    
    def reload_index(self) -> Dict[str, Any]:
        """Reload the index from storage"""
        try:
            self.logger.info("🔄 Reloading index...")
            
            # Load documents
            documents = self._load_documents_from_knowledge_base()
            
            # Rebuild index
            result = self.build_index(force_rebuild=True)
            
            if result['success']:
                self.logger.info("✅ Index reloaded successfully")
            else:
                self.logger.error(f"❌ Failed to reload index: {result.get('error')}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error reloading index: {e}")
            return {
                'success': False,
                'error': str(e)
            }
