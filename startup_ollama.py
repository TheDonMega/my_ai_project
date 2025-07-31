#!/usr/bin/env python3
"""
Startup script to ensure Ollama models are available before backend starts
"""

import os
import time
import requests
import subprocess
import sys

def wait_for_ollama():
    """Wait for Ollama service to be ready"""
    print("⏳ Waiting for Ollama service to be ready...")
    max_attempts = 60  # Increased for startup
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://ollama-ai-project:11434/api/tags", timeout=5)
            if response.status_code == 200:
                print("✅ Ollama service is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        if attempt % 10 == 0:  # Log every 10th attempt
            print(f"⏳ Attempt {attempt + 1}/{max_attempts} - Ollama not ready yet...")
        time.sleep(2)
    
    print("❌ Ollama service did not become ready in time")
    return False

def check_model_exists(model_name):
    """Check if a model exists"""
    try:
        response = requests.get("http://ollama-ai-project:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            for model in models:
                # Check both the exact name and with :latest suffix
                model_name_check = model.get("name", "")
                if model_name_check == model_name or model_name_check == f"{model_name}:latest":
                    return True
        return False
    except Exception:
        return False

def pull_model(model_name):
    """Pull a model using Ollama API"""
    print(f"📥 Pulling model: {model_name}")
    
    try:
        # Start the pull request
        response = requests.post(
            "http://ollama-ai-project:11434/api/pull",
            json={"name": model_name},
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"✅ Successfully started pulling {model_name}")
            return True
        else:
            print(f"❌ Failed to start pulling {model_name}: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error pulling {model_name}: {e}")
        return False

def wait_for_model_download(model_name):
    """Wait for model download to complete"""
    print(f"⏳ Waiting for {model_name} to finish downloading...")
    max_attempts = 300  # 10 minutes max
    for attempt in range(max_attempts):
        if check_model_exists(model_name):
            print(f"✅ {model_name} is ready!")
            return True
        
        if attempt % 30 == 0:  # Log every 30th attempt (every minute)
            print(f"⏳ Still downloading {model_name}... (attempt {attempt + 1}/{max_attempts})")
        
        time.sleep(2)
    
    print(f"❌ {model_name} download did not complete in time")
    return False

def main():
    """Main startup function"""
    print("🚀 Ollama Startup Check")
    print("=" * 30)
    
    # Wait for Ollama to be ready
    if not wait_for_ollama():
        print("❌ Cannot proceed without Ollama service")
        sys.exit(1)
    
    # Check if mistral model exists
    if check_model_exists("mistral"):
        print("✅ mistral model already exists")
        return True
    
    # Pull the mistral model
    print("📥 Pulling mistral model (this may take a while)...")
    if pull_model("mistral"):
        # Wait for download to complete
        if wait_for_model_download("mistral"):
            print("✅ mistral model is ready for use!")
            return True
        else:
            print("❌ mistral model download failed")
            sys.exit(1)
    else:
        print("❌ Failed to start pulling mistral model")
        sys.exit(1)

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 