import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CrewAIAnalyzer:
    def __init__(self, knowledge_base_path: str = "./knowledge_base"):
        self.knowledge_base_path = knowledge_base_path
        self.vector_store = None
        self.llm = None
        self.embeddings = None
        self.setup_local_ai()
        self.setup_vector_store()
        
    def setup_local_ai(self):
        """Setup local AI model using Ollama only - no Gemini fallback for CrewAI"""
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
            model_name = "mistral"
            
            self.llm = Ollama(model=model_name, base_url=ollama_base_url)
            self.embeddings = OllamaEmbeddings(model=model_name, base_url=ollama_base_url)
            print(f"✅ Using local Ollama model: {model_name} for CrewAI (URL: {ollama_base_url})")
        except Exception as e:
            print(f"⚠️  Ollama not available for CrewAI: {e}")
            print("🔒 CrewAI will not be available - will fall back to simple search")
            # Don't configure Gemini - keep it local only
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
            
            # Split documents into chunks
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            
            chunks = text_splitter.split_documents(documents)
            print(f"📄 Created {len(chunks)} chunks from {len(documents)} documents")
            
            # Create vector store
            from langchain_community.vectorstores import Chroma
            self.vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory="./chroma_db"
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
        """Create CrewAI agents"""
        try:
            from crewai import Agent, Task, Crew
            from langchain.tools import Tool
            
            # Create the search tool
            search_tool = Tool(
                name="search_knowledge_base",
                description="Search the knowledge base for relevant information",
                func=self.search_knowledge_base_tool
            )
            
            # Research Agent - Finds relevant information
            research_agent = Agent(
                role='Research Analyst',
                goal='Find the most relevant information from the knowledge base for the given query',
                backstory="""You are an expert research analyst with deep knowledge of the organization's 
                documentation. You excel at finding the most relevant information quickly and accurately.""",
                verbose=False,
                allow_delegation=False,
                llm=self.llm,
                tools=[search_tool]
            )
            
            # Analysis Agent - Analyzes and synthesizes information
            analysis_agent = Agent(
                role='Content Analyst',
                goal='Analyze and synthesize the found information into comprehensive, well-structured answers',
                backstory="""You are a skilled content analyst who excels at taking raw information and 
                transforming it into clear, comprehensive, and well-organized responses. You understand 
                context and can provide nuanced analysis.""",
                verbose=False,
                allow_delegation=False,
                llm=self.llm
            )
            
            # Quality Agent - Ensures accuracy and completeness
            quality_agent = Agent(
                role='Quality Assurance Specialist',
                goal='Review and validate the analysis for accuracy, completeness, and relevance',
                backstory="""You are a meticulous quality assurance specialist who ensures that all 
                responses are accurate, complete, and relevant to the user's query. You catch errors 
                and suggest improvements.""",
                verbose=False,
                allow_delegation=False,
                llm=self.llm
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
        """Tool for searching the knowledge base"""
        if not self.vector_store:
            return "Vector store not available"
        
        try:
            results = self.vector_store.similarity_search(query, k=5)
            formatted_results = []
            
            for doc in results:
                source = doc.metadata.get('source', 'Unknown')
                folder = doc.metadata.get('folder_path', 'root')
                content = doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content
                formatted_results.append(f"Source: {source} (in {folder})\nContent: {content}\n")
            
            return "\n".join(formatted_results)
        except Exception as e:
            return f"Error searching knowledge base: {str(e)}"
    
    def analyze_query_simple(self, query: str) -> Dict[str, Any]:
        """Simple analysis without CrewAI for fallback scenarios"""
        print(f"🔍 Simple analysis for: {query}")
        
        # Load documents
        documents = self.load_documents_recursively()
        
        if not documents:
            return {
                'answer': "No documents found in knowledge base.",
                'sources': [],
                'method': 'simple_fallback'
            }
        
        # Simple keyword search
        query_words = set(query.lower().split())
        relevant_docs = []
        
        for doc in documents:
            content = doc.page_content.lower()
            if any(word in content for word in query_words):
                relevant_docs.append({
                    'filename': doc.metadata.get('source', 'Unknown'),
                    'folder_path': doc.metadata.get('folder_path', 'root'),
                    'content': doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                    'relevance': 75.0
                })
        
        if not relevant_docs:
            return {
                'answer': "No relevant information found in the knowledge base.",
                'sources': [],
                'method': 'simple_fallback'
            }
        
        # Create simple answer
        answer_parts = []
        for doc in relevant_docs[:3]:
            location = f"From {doc['folder_path']}/{doc['filename']}" if doc['folder_path'] != 'root' else f"From {doc['filename']}"
            answer_parts.append(f"{location}:\n{doc['content']}")
        
        answer = "Based on the local knowledge base:\n\n" + "\n\n".join(answer_parts)
        
        return {
            'answer': answer,
            'sources': relevant_docs,
            'method': 'simple_fallback'
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
            
            # Create tasks
            research_task = Task(
                description=f"""
                Search the knowledge base for information relevant to: "{query}"
                
                Your task:
                1. Use the search tool to find relevant documents
                2. Identify the most important and relevant information
                3. Provide a summary of what you found
                4. Include source information (filename and folder path)
                
                Focus on finding information that directly answers the user's question.
                """,
                agent=agents['research'],
                expected_output="A detailed summary of relevant information found in the knowledge base, including source citations."
            )
            
            analysis_task = Task(
                description=f"""
                Analyze the research findings and provide a comprehensive answer to: "{query}"
                
                Your task:
                1. Review the research findings
                2. Synthesize the information into a clear, comprehensive answer
                3. Structure your response logically
                4. Ensure all relevant information is included
                5. Maintain source attribution
                
                Make sure your answer is complete and addresses all aspects of the query.
                """,
                agent=agents['analysis'],
                expected_output="A comprehensive, well-structured answer to the user's query based on the research findings."
            )
            
            quality_task = Task(
                description=f"""
                Review the analysis for quality and accuracy.
                
                Your task:
                1. Verify the accuracy of the information provided
                2. Check for completeness - does it answer the full query?
                3. Ensure proper source attribution
                4. Validate the logical flow and structure
                5. Suggest any improvements if needed
                
                If you find issues, provide specific feedback and corrections.
                """,
                agent=agents['quality'],
                expected_output="Quality assessment with any necessary corrections or improvements to the analysis."
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

def get_crewai_analyzer(knowledge_base_path: str = "./knowledge_base"):
    """Get or create the CrewAI analyzer instance"""
    global crewai_analyzer
    if crewai_analyzer is None:
        crewai_analyzer = CrewAIAnalyzer(knowledge_base_path)
    return crewai_analyzer 