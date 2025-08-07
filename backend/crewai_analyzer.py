import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CrewAIAnalyzer:
    def __init__(self, knowledge_base_path: str = "/app/knowledge_base"):
        self.knowledge_base_path = knowledge_base_path
        self.vector_store = None
        self.llm = None
        self.embeddings = None
        self.setup_local_ai()
        self.setup_vector_store()
        
    def setup_local_ai(self):
        """Setup local AI model using Ollama for CrewAI"""
        try:
            # Try to use Ollama with a local model
            from langchain_community.llms import Ollama
            from langchain_community.embeddings import OllamaEmbeddings
            
            # Get Ollama base URL from environment (for Docker) or use default
            ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            
            # You can change this model name to use different models:
            # - "llama2" (default)
            # - "mistral" (faster, smaller)
            # - "codellama" (good for code)
            # - "llama2:13b" (larger, more capable)
            #model_name = "mistral"
            model_name = "llama2"
            
            self.llm = Ollama(model=model_name, base_url=ollama_base_url)
            self.embeddings = OllamaEmbeddings(model=model_name, base_url=ollama_base_url)
            print(f"✅ Using local Ollama model: {model_name} for CrewAI (URL: {ollama_base_url})")
        except Exception as e:
            print(f"⚠️  Ollama not available for CrewAI: {e}")
            print("🔒 CrewAI will not be available - will fall back to simple search")
            # Keep it local only - no external AI services
            self.llm = None
            self.embeddings = None
    
    def setup_vector_store(self):
        """Create a vector store from the knowledge base for semantic search"""
        print("🔍 Setting up vector store from knowledge base...")
        
        try:
            # Load all markdown files recursively
            documents = self.load_documents_recursively()
            
            if not documents:
                print("⚠️  No documents found in knowledge base")
                return
            
            if not self.embeddings:
                print("⚠️  No embeddings available, skipping vector store")
                return
            
            # Enhanced text splitting with better chunking strategy
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,  # Smaller chunks for more precise retrieval
                chunk_overlap=100,  # Good overlap to maintain context
                length_function=len,
                separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]  # Better separators
            )
            
            chunks = text_splitter.split_documents(documents)
            print(f"📄 Created {len(chunks)} chunks from {len(documents)} documents")
            
            # Create vector store with better configuration
            from langchain_community.vectorstores import Chroma
            self.vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory="/app/chroma_db",
                collection_metadata={"hnsw:space": "cosine"}  # Better similarity metric
            )
            print("✅ Vector store created and ready")
            
        except Exception as e:
            print(f"❌ Error setting up vector store: {e}")
            self.vector_store = None
    
    def load_documents_recursively(self) -> List:
        """Load all markdown files from the knowledge base recursively"""
        documents = []
        
        def load_recursive(current_path: str, base_path: str):
            try:
                for item in os.listdir(current_path):
                    item_path = os.path.join(current_path, item)
                    
                    if os.path.isdir(item_path):
                        load_recursive(item_path, base_path)
                    elif item.endswith(".md"):
                        relative_path = os.path.relpath(item_path, base_path)
                        
                        with open(item_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            from langchain.schema import Document
                            documents.append(Document(
                                page_content=content,
                                metadata={
                                    "source": relative_path,
                                    "filename": os.path.basename(item_path),
                                    "folder_path": os.path.dirname(relative_path) if os.path.dirname(relative_path) else "root"
                                }
                            ))
            except Exception as e:
                print(f"Error loading documents from {current_path}: {e}")
        
        load_recursive(self.knowledge_base_path, self.knowledge_base_path)
        return documents
    
    def create_agents(self) -> Dict[str, Any]:
        """Create enhanced CrewAI agents with better memory and context"""
        try:
            from crewai import Agent, Task, Crew
            from langchain.tools import Tool
            from langchain.memory import ConversationBufferMemory
            
            # Create the enhanced search tool
            search_tool = Tool(
                name="search_knowledge_base",
                description="Search the knowledge base for relevant information. Use this to find specific details, procedures, or information related to the user's query.",
                func=self.search_knowledge_base_tool
            )
            
            # Enhanced Research Agent with memory
            research_memory = ConversationBufferMemory(
                memory_key="research_history",
                return_messages=True
            )
            
            research_agent = Agent(
                role='Senior Research Analyst',
                goal='Find the most relevant and specific information from the knowledge base that directly answers the user\'s question',
                backstory="""You are an expert research analyst with deep knowledge of the organization's 
                documentation. You excel at finding the most relevant information quickly and accurately.
                You understand context and can identify the most important details that directly address
                the user's specific question. You always verify the relevance of information before
                including it in your research.""",
                verbose=False,
                allow_delegation=False,
                llm=self.llm,
                tools=[search_tool],
                memory=research_memory
            )
            
            # Enhanced Analysis Agent with better synthesis
            analysis_memory = ConversationBufferMemory(
                memory_key="analysis_history",
                return_messages=True
            )
            
            analysis_agent = Agent(
                role='Content Synthesis Specialist',
                goal='Analyze and synthesize the found information into comprehensive, well-structured answers that directly address the user\'s question',
                backstory="""You are a skilled content analyst who excels at taking raw information and 
                transforming it into clear, comprehensive, and well-organized responses. You understand 
                context and can provide nuanced analysis. You focus on answering the specific question
                asked, not providing general information. You always structure your response to be
                directly relevant to what the user is asking.""",
                verbose=False,
                allow_delegation=False,
                llm=self.llm,
                memory=analysis_memory
            )
            
            # Enhanced Quality Agent with better validation
            quality_memory = ConversationBufferMemory(
                memory_key="quality_history",
                return_messages=True
            )
            
            quality_agent = Agent(
                role='Quality Assurance & Relevance Specialist',
                goal='Review and validate the analysis for accuracy, completeness, relevance, and direct answer to the user\'s question',
                backstory="""You are a meticulous quality assurance specialist who ensures that all 
                responses are accurate, complete, and directly relevant to the user's query. You catch 
                errors, suggest improvements, and ensure the answer actually addresses what was asked.
                You verify that the response is focused and doesn't include irrelevant information.""",
                verbose=False,
                allow_delegation=False,
                llm=self.llm,
                memory=quality_memory
            )
            
            return {
                'research': research_agent,
                'analysis': analysis_agent,
                'quality': quality_agent
            }
        except Exception as e:
            print(f"❌ Error creating agents: {e}")
            return {}
    
    def search_knowledge_base_tool(self, query: str) -> str:
        """Enhanced tool for searching the knowledge base with better relevance scoring"""
        if not self.vector_store:
            return "Vector store not available"
        
        try:
            # Use MMR (Maximal Marginal Relevance) for better diversity and relevance
            results = self.vector_store.max_marginal_relevance_search(
                query, 
                k=8,  # Get more candidates
                fetch_k=20,  # Fetch more for better selection
                lambda_mult=0.7  # Balance between relevance and diversity
            )
            
            # Filter and score results based on query relevance
            query_words = set(query.lower().split())
            scored_results = []
            
            for doc in results:
                content = doc.page_content.lower()
                source = doc.metadata.get('source', 'Unknown')
                folder = doc.metadata.get('folder_path', 'root')
                
                # Calculate relevance score
                content_words = set(content.split())
                word_overlap = len(query_words.intersection(content_words))
                relevance_score = word_overlap / len(query_words) if query_words else 0
                
                # Only include results with meaningful relevance
                if relevance_score > 0.1:  # Minimum relevance threshold
                    scored_results.append({
                        'doc': doc,
                        'score': relevance_score,
                        'source': source,
                        'folder': folder
                    })
            
            # Sort by relevance and take top results
            scored_results.sort(key=lambda x: x['score'], reverse=True)
            top_results = scored_results[:3]  # Return top 3 most relevant
            
            if not top_results:
                return "No relevant information found in the knowledge base."
            
            formatted_results = []
            for result in top_results:
                doc = result['doc']
                source = result['source']
                folder = result['folder']
                content = doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content
                relevance = f"{result['score']:.1%}"
                
                formatted_results.append(
                    f"Source: {source} (in {folder}) - Relevance: {relevance}\n"
                    f"Content: {content}\n"
                )
            
            return "\n".join(formatted_results)
            
        except Exception as e:
            return f"Error searching knowledge base: {str(e)}"
    
    def analyze_query_simple(self, query: str) -> Dict[str, Any]:
        """Enhanced simple analysis with better relevance filtering"""
        print(f"🔍 Enhanced simple analysis for: {query}")
        
        # Load documents
        documents = self.load_documents_recursively()
        
        if not documents:
            return {
                'answer': "No documents found in knowledge base.",
                'sources': [],
                'method': 'simple_fallback'
            }
        
        # Enhanced keyword search with better scoring
        query_words = set(query.lower().split())
        relevant_docs = []
        
        for doc in documents:
            content = doc.page_content.lower()
            title = doc.metadata.get('source', '').lower()
            
            # Calculate multiple relevance scores
            content_words = set(content.split())
            title_words = set(title.split())
            
            # Content relevance
            content_overlap = len(query_words.intersection(content_words))
            content_score = content_overlap / len(query_words) if query_words else 0
            
            # Title relevance (weighted higher)
            title_overlap = len(query_words.intersection(title_words))
            title_score = (title_overlap / len(query_words)) * 2 if query_words else 0
            
            # Combined score with title weighting
            total_score = content_score + title_score
            
            # Only include results with meaningful relevance
            if total_score > 0.15:  # Higher threshold for better filtering
                relevant_docs.append({
                    'filename': doc.metadata.get('source', 'Unknown'),
                    'folder_path': doc.metadata.get('folder_path', 'root'),
                    'content': doc.page_content[:400] + "..." if len(doc.page_content) > 400 else doc.page_content,
                    'relevance': total_score * 100,
                    'title_score': title_score,
                    'content_score': content_score
                })
        
        # Sort by relevance and take top results
        relevant_docs.sort(key=lambda x: x['relevance'], reverse=True)
        top_docs = relevant_docs[:2]  # Limit to top 2 most relevant
        
        if not top_docs:
            return {
                'answer': "No relevant information found in the knowledge base for your specific question.",
                'sources': [],
                'method': 'simple_fallback'
            }
        
        # Create focused answer
        answer_parts = []
        for doc in top_docs:
            location = f"From {doc['folder_path']}/{doc['filename']}" if doc['folder_path'] != 'root' else f"From {doc['filename']}"
            relevance = f"{doc['relevance']:.1f}%"
            answer_parts.append(f"{location} (Relevance: {relevance}):\n{doc['content']}")
        
        answer = "Based on the most relevant information in the knowledge base:\n\n" + "\n\n".join(answer_parts)
        
        return {
            'answer': answer,
            'sources': top_docs,
            'method': 'enhanced_simple_fallback'
        }
    
    def analyze_query_crewai(self, query: str) -> Dict[str, Any]:
        """Analyze using CrewAI if available"""
        try:
            from crewai import Task, Crew, Process
            
            # Create agents
            agents = self.create_agents()
            if not agents:
                print("❌ Failed to create agents, falling back to simple analysis")
                return self.analyze_query_simple(query)
            
            # Create enhanced tasks with better focus
            research_task = Task(
                description=f"""
                RESEARCH TASK: Find the most relevant information for: "{query}"
                
                Your specific instructions:
                1. Use the search tool to find information that DIRECTLY answers the user's question
                2. Focus on finding specific details, procedures, or facts related to the query
                3. Ignore general information that doesn't directly address the question
                4. Look for the most recent and authoritative information
                5. If the query is about a specific topic, focus on that topic only
                6. Provide source information (filename and folder path) for each relevant piece
                
                IMPORTANT: Only include information that is directly relevant to answering the user's specific question.
                Do not include general background information unless it's essential for understanding the answer.
                
                Expected output: A focused summary of only the most relevant information found, with clear source citations.
                """,
                agent=agents['research'],
                expected_output="A focused summary of the most relevant information that directly answers the user's question, with source citations."
            )
            
            analysis_task = Task(
                description=f"""
                ANALYSIS TASK: Create a focused answer for: "{query}"
                
                Your specific instructions:
                1. Review the research findings and focus ONLY on what directly answers the question
                2. Structure your response to directly address the user's specific question
                3. If the research found multiple relevant pieces, prioritize the most relevant ones
                4. Be concise and focused - don't include unnecessary background information
                5. If the research doesn't fully answer the question, clearly state what's missing
                6. Maintain source attribution for all information used
                
                IMPORTANT: Your answer should be directly relevant to what the user asked.
                If the user asked about a specific procedure, focus on that procedure.
                If they asked about a specific concept, focus on that concept.
                
                Expected output: A clear, focused answer that directly addresses the user's question.
                """,
                agent=agents['analysis'],
                expected_output="A clear, focused answer that directly addresses the user's specific question."
            )
            
            quality_task = Task(
                description=f"""
                QUALITY ASSURANCE TASK: Review the analysis for relevance and accuracy.
                
                Your specific instructions:
                1. Verify that the answer directly addresses the user's question: "{query}"
                2. Check that the response is focused and doesn't include irrelevant information
                3. Ensure all information is accurate and properly sourced
                4. Verify that the answer is complete for the specific question asked
                5. If the answer includes unnecessary information, suggest removing it
                6. If the answer is missing important details, suggest adding them
                
                IMPORTANT: Focus on relevance to the user's specific question.
                The answer should be targeted and focused, not a general overview.
                
                Expected output: Quality assessment with specific feedback on relevance and focus.
                """,
                agent=agents['quality'],
                expected_output="Quality assessment focusing on relevance, accuracy, and direct answer to the user's question."
            )
            
            # Create and run the crew
            crew = Crew(
                agents=list(agents.values()),
                tasks=[research_task, analysis_task, quality_task],
                process=Process.sequential,
                verbose=False
            )
            
            print("🚀 Starting CrewAI execution...")
            result = crew.kickoff()
            sources = self.extract_sources_from_result(result)
            
            return {
                'answer': result,
                'sources': sources,
                'method': 'crewai'
            }
            
        except Exception as e:
            print(f"❌ CrewAI analysis failed: {e}")
            return self.analyze_query_simple(query)
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze a query using available methods"""
        try:
            # Try CrewAI first if available
            if self.llm:
                return self.analyze_query_crewai(query)
            else:
                return self.analyze_query_simple(query)
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return self.analyze_query_simple(query)
    
    def extract_sources_from_result(self, result: str) -> List[Dict[str, Any]]:
        """Extract source information from the result"""
        sources = []
        
        lines = result.split('\n')
        for line in lines:
            if line.startswith('Source:') or 'source:' in line.lower():
                source_info = line.replace('Source:', '').strip()
                if '(' in source_info and ')' in source_info:
                    filename = source_info.split('(')[0].strip()
                    folder = source_info.split('(')[1].split(')')[0].strip()
                    
                    sources.append({
                        'filename': filename,
                        'folder_path': folder,
                        'relevance': 85.0,
                        'header': 'CrewAI Analysis',
                        'content': 'Analyzed by CrewAI',
                        'full_document_available': True
                    })
        
        return sources

# Global instance
crewai_analyzer = None

def get_crewai_analyzer(knowledge_base_path: str = "/app/knowledge_base"):
    """Get or create the CrewAI analyzer instance"""
    global crewai_analyzer
    if crewai_analyzer is None:
        crewai_analyzer = CrewAIAnalyzer(knowledge_base_path)
    return crewai_analyzer 