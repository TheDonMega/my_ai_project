#!/usr/bin/env python3
"""
Setup script for CrewAI integration with local AI models
"""

import subprocess
import sys
import os
import platform
import pkg_resources

def run_command(command, description, capture_output=True):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        if capture_output:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            print(f"✅ {description} completed successfully")
            return True, result.stdout
        else:
            result = subprocess.run(command, shell=True, check=True)
            print(f"✅ {description} completed successfully")
            return True, ""
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False, e.stderr

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} is not supported. Please use Python 3.8 or higher.")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def check_pip():
    """Check if pip is available and up to date"""
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError:
        print("❌ pip is not available")
        return False

def upgrade_pip():
    """Upgrade pip to latest version"""
    print("🔄 Upgrading pip...")
    return run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip")

def check_ollama():
    """Check if Ollama is installed and running"""
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Ollama is installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ Ollama is not working properly")
            return False
    except FileNotFoundError:
        print("❌ Ollama is not installed")
        return False

def install_ollama():
    """Install Ollama based on the operating system"""
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        print("🍎 Installing Ollama on macOS...")
        return run_command(
            "curl -fsSL https://ollama.ai/install.sh | sh",
            "Installing Ollama"
        )
    
    elif system == "linux":
        print("🐧 Installing Ollama on Linux...")
        return run_command(
            "curl -fsSL https://ollama.ai/install.sh | sh",
            "Installing Ollama"
        )
    
    elif system == "windows":
        print("🪟 Installing Ollama on Windows...")
        print("Please download and install Ollama from: https://ollama.ai/download")
        print("After installation, restart your terminal and run this script again.")
        return False, ""
    
    else:
        print(f"❌ Unsupported operating system: {system}")
        return False, ""

def pull_llama_model():
    """Pull the Llama2 model for Ollama"""
    print("📥 Pulling Llama2 model (this may take a while)...")
    return run_command("ollama pull llama2", "Pulling Llama2 model")

def install_python_dependencies():
    """Install Python dependencies with conflict resolution"""
    print("📦 Installing Python dependencies...")
    
    # First, try to install with --no-deps to avoid conflicts
    success, output = run_command(
        f"{sys.executable} -m pip install -r requirements.txt --no-deps",
        "Installing packages without dependencies"
    )
    
    if not success:
        print("⚠️  Trying alternative installation method...")
        # Try installing packages one by one
        packages = [
            "google-generativeai>=0.8.0",
            "python-dotenv>=1.0.0", 
            "flask>=2.3.0",
            "flask-cors>=4.0.0",
            "crewai==0.70.0",
            "langchain==0.1.0",
            "langchain-community==0.0.20",
            "langchain-core==0.1.0",
            "chromadb==0.4.22",
            "sentence-transformers==2.2.2",
            "ollama==0.1.7",
            "pydantic>=2.0.0",
            "typing-extensions>=4.0.0"
        ]
        
        for package in packages:
            success, _ = run_command(
                f"{sys.executable} -m pip install {package}",
                f"Installing {package}"
            )
            if not success:
                print(f"❌ Failed to install {package}")
                return False
    
    return True

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking installed dependencies...")
    
    required_packages = {
        'crewai': '0.70.0',
        'langchain': '0.1.0',
        'langchain-community': '0.0.20',
        'chromadb': '0.4.22',
        'sentence-transformers': '2.2.2',
        'ollama': '0.1.7'
    }
    
    missing_packages = []
    version_mismatches = []
    
    for package, required_version in required_packages.items():
        try:
            installed_version = pkg_resources.get_distribution(package).version
            print(f"✅ {package}: {installed_version}")
            
            # Check if version matches (for exact version requirements)
            if '==' in required_version:
                expected_version = required_version.replace('==', '')
                if installed_version != expected_version:
                    version_mismatches.append(f"{package}: expected {expected_version}, got {installed_version}")
                    
        except pkg_resources.DistributionNotFound:
            missing_packages.append(package)
            print(f"❌ {package}: not installed")
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        return False
    
    if version_mismatches:
        print(f"\n⚠️  Version mismatches: {', '.join(version_mismatches)}")
        print("This might cause compatibility issues.")
    
    return True

def test_crewai_setup():
    """Test the CrewAI setup"""
    print("🧪 Testing CrewAI setup...")
    try:
        from crewai_analyzer import CrewAIAnalyzer
        print("✅ CrewAI analyzer imported successfully")
        
        # Test basic initialization
        analyzer = CrewAIAnalyzer()
        print("✅ CrewAI analyzer initialized successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Try: pip install --upgrade crewai langchain langchain-community")
        return False
    except Exception as e:
        print(f"❌ CrewAI setup test failed: {e}")
        return False

def create_virtual_environment():
    """Create a virtual environment if not already in one"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Already in a virtual environment")
        return True
    
    print("📁 Creating virtual environment...")
    venv_name = "crewai_env"
    
    success, _ = run_command(
        f"{sys.executable} -m venv {venv_name}",
        "Creating virtual environment"
    )
    
    if success:
        print(f"✅ Virtual environment created: {venv_name}")
        print(f"💡 Activate it with: source {venv_name}/bin/activate (macOS/Linux) or {venv_name}\\Scripts\\activate (Windows)")
        return True
    
    return False

def main():
    """Main setup function"""
    print("🚀 Setting up CrewAI with local AI models...")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Check pip
    if not check_pip():
        return False
    
    # Upgrade pip
    upgrade_pip()
    
    # Create virtual environment (optional)
    create_virtual_environment()
    
    # Check if Ollama is installed
    if not check_ollama():
        print("\n📥 Ollama not found. Installing...")
        success, _ = install_ollama()
        if not success:
            print("❌ Failed to install Ollama. Please install manually from https://ollama.ai")
            return False
        
        # Check again after installation
        if not check_ollama():
            print("❌ Ollama installation verification failed")
            return False
    
    # Pull Llama2 model
    success, _ = pull_llama_model()
    if not success:
        print("❌ Failed to pull Llama2 model")
        return False
    
    # Install Python dependencies
    if not install_python_dependencies():
        print("❌ Failed to install Python dependencies")
        return False
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed")
        return False
    
    # Test the setup
    if not test_crewai_setup():
        print("❌ CrewAI setup test failed")
        return False
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Start Ollama: ollama serve")
    print("2. Start your Flask server: python server.py")
    print("3. Start your frontend: cd frontend && npm run dev")
    print("\n🔧 Available models:")
    print("- llama2 (default)")
    print("- mistral (alternative)")
    print("- codellama (for code analysis)")
    print("\n💡 To use a different model, edit crewai_analyzer.py and change 'llama2' to your preferred model")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 