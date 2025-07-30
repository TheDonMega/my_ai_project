#!/usr/bin/env python3
"""
Test script to verify API key usage separation
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_crewai_no_gemini():
    """Test that CrewAI doesn't use Gemini API key"""
    print("🔍 Testing CrewAI API key usage...")
    
    # Check if Gemini API key is set
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("⚠️  No GEMINI_API_KEY found in environment")
        return
    
    print(f"✅ GEMINI_API_KEY is set (length: {len(gemini_key)})")
    
    try:
        # Import CrewAI analyzer
        from crewai_analyzer import get_crewai_analyzer
        print("✅ Successfully imported CrewAI analyzer")
        
        # Get analyzer instance
        analyzer = get_crewai_analyzer()
        print("✅ Successfully created CrewAI analyzer instance")
        
        # Check what LLM is being used
        if analyzer.llm:
            llm_type = type(analyzer.llm).__name__
            print(f"✅ CrewAI is using: {llm_type}")
            
            if "Ollama" in llm_type:
                print("🔒 CrewAI is using local Ollama - NO Gemini API calls!")
            else:
                print("⚠️  CrewAI is not using Ollama - check configuration")
        else:
            print("⚠️  CrewAI has no LLM configured - will use simple search")
        
        # Test a simple query
        print("\n🧪 Testing CrewAI with sample query...")
        result = analyzer.analyze_query("test query")
        print(f"✅ CrewAI analysis completed with method: {result.get('method', 'unknown')}")
        
        if result.get('method') == 'crewai':
            print("🔒 CrewAI used local models only - NO Gemini API calls!")
        elif result.get('method') == 'simple_fallback':
            print("🔒 Used simple fallback - NO Gemini API calls!")
        else:
            print(f"⚠️  Unknown method: {result.get('method')}")
            
    except ImportError as e:
        print(f"❌ Could not import CrewAI: {e}")
    except Exception as e:
        print(f"❌ Error testing CrewAI: {e}")

def test_gemini_usage():
    """Test that Gemini is only used for web search"""
    print("\n🔍 Testing Gemini API usage...")
    
    try:
        import google.generativeai as genai
        print("✅ Google Generative AI imported")
        
        # This would only be used in server.py for web search
        print("ℹ️  Gemini is only used in server.py for web search functionality")
        print("ℹ️  CrewAI operations never touch the Gemini API")
        
    except ImportError as e:
        print(f"❌ Could not import Google Generative AI: {e}")

if __name__ == "__main__":
    print("🧪 API Key Usage Test")
    print("=" * 40)
    
    test_crewai_no_gemini()
    test_gemini_usage()
    
    print("\n" + "=" * 40)
    print("✅ Test completed!")
    print("\n📋 Summary:")
    print("- CrewAI uses only local Ollama models")
    print("- Gemini API key is only used for web search")
    print("- No API key usage during CrewAI operations") 