#!/usr/bin/env python3
"""
ResearchMind v2.0 - Installation Verification Script
Checks if all dependencies and configurations are correct.
"""

import sys
import os
from pathlib import Path

def print_header(text):
    """Print formatted header."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_status(check, status, message=""):
    """Print check status."""
    icon = "✅" if status else "❌"
    print(f"{icon} {check:<40} {message}")
    return status

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    is_valid = version.major == 3 and version.minor >= 10
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    return print_status(
        "Python Version (3.10+)",
        is_valid,
        f"v{version_str}"
    )

def check_module(module_name, display_name=None):
    """Check if a module is installed."""
    if display_name is None:
        display_name = module_name
    try:
        __import__(module_name)
        return print_status(f"{display_name}", True, "Installed")
    except ImportError:
        return print_status(f"{display_name}", False, "Missing")

def check_file(filepath, description):
    """Check if a file exists."""
    exists = Path(filepath).exists()
    return print_status(description, exists, filepath if exists else "Not found")

def check_directory(dirpath, description):
    """Check if a directory exists."""
    path = Path(dirpath)
    exists = path.exists() and path.is_dir()
    return print_status(description, exists, dirpath if exists else "Not found")

def check_env_variable(var_name):
    """Check if environment variable is set."""
    from dotenv import load_dotenv
    load_dotenv()
    value = os.getenv(var_name)
    is_set = value is not None and len(value) > 0
    display = "Set" if is_set else "Not set"
    if is_set:
        display += f" ({len(value)} chars)"
    return print_status(f"ENV: {var_name}", is_set, display)

def main():
    """Run all verification checks."""
    print_header("ResearchMind v2.0 - Installation Verification")
    
    all_passed = True
    
    # Python version
    print("\n📋 System Requirements:")
    all_passed &= check_python_version()
    
    # Core dependencies
    print("\n📦 Core Dependencies:")
    all_passed &= check_module("streamlit", "Streamlit")
    all_passed &= check_module("langchain", "LangChain")
    all_passed &= check_module("langchain_groq", "LangChain Groq")
    all_passed &= check_module("tavily", "Tavily")
    
    # Web scraping
    print("\n🌐 Web Scraping:")
    all_passed &= check_module("requests", "Requests")
    all_passed &= check_module("bs4", "BeautifulSoup4")
    
    # PDF generation
    print("\n📕 PDF Generation:")
    all_passed &= check_module("reportlab", "ReportLab")
    all_passed &= check_module("markdown", "Markdown")
    
    # Utilities
    print("\n🔧 Utilities:")
    all_passed &= check_module("dotenv", "Python-dotenv")
    all_passed &= check_module("rich", "Rich")
    all_passed &= check_module("tenacity", "Tenacity")
    
    # Application files
    print("\n📄 Application Files:")
    all_passed &= check_file("app.py", "Main App")
    all_passed &= check_file("agents.py", "Agents Module")
    all_passed &= check_file("pipeline.py", "Pipeline Module")
    all_passed &= check_file("tools.py", "Tools Module")
    all_passed &= check_file("config.py", "Config Module")
    all_passed &= check_file("utils.py", "Utils Module")
    all_passed &= check_file("history.py", "History Module (NEW)")
    all_passed &= check_file("pdf_exporter.py", "PDF Exporter (NEW)")
    
    # Configuration files
    print("\n⚙️ Configuration:")
    all_passed &= check_file("requirements.txt", "Requirements")
    all_passed &= check_file(".env.example", "Env Example")
    env_exists = check_file(".env", "Environment File")
    
    # Directories
    print("\n📁 Directories:")
    check_directory(".cache", "Cache Directory")
    check_directory("logs", "Logs Directory")
    check_directory("reports", "Reports Directory")
    
    # Environment variables (only if .env exists)
    if env_exists:
        print("\n🔐 Environment Variables:")
        all_passed &= check_env_variable("GROQ_API_KEY")
        all_passed &= check_env_variable("TAVILY_API_KEY")
        check_env_variable("GROQ_MODEL")
        check_env_variable("MODEL_TEMPERATURE")
    
    # Documentation
    print("\n📚 Documentation:")
    check_file("README.md", "README")
    check_file("QUICK_START_V2.md", "Quick Start Guide")
    check_file("DEPLOYMENT_GUIDE.md", "Deployment Guide")
    check_file("TESTING_GUIDE.md", "Testing Guide")
    check_file("VISUAL_GUIDE.md", "Visual Guide")
    check_file("QUICK_REFERENCE.md", "Quick Reference")
    
    # Import test
    print("\n🧪 Import Tests:")
    try:
        import streamlit
        import history
        import pdf_exporter
        print_status("All imports", True, "Success")
    except Exception as e:
        print_status("All imports", False, f"Failed: {str(e)}")
        all_passed = False
    
    # Final result
    print_header("Verification Results")
    
    if all_passed:
        print("\n🎉 SUCCESS! All critical checks passed.")
        print("\n✅ Your installation is ready!")
        print("\n📝 Next Steps:")
        print("   1. Edit .env and add your API keys (if not done)")
        print("   2. Run: streamlit run app.py")
        print("   3. Open: http://localhost:8501")
        print("\n📚 Documentation:")
        print("   - Quick Start: QUICK_START_V2.md")
        print("   - Testing: TESTING_GUIDE.md")
        print("   - Deployment: DEPLOYMENT_GUIDE.md")
        return 0
    else:
        print("\n⚠️  WARNING: Some checks failed.")
        print("\n🔧 To fix:")
        print("   1. Install missing dependencies:")
        print("      pip install -r requirements.txt --upgrade")
        print("   2. Create .env file:")
        print("      cp .env.example .env")
        print("   3. Add your API keys to .env")
        print("   4. Run this script again")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error during verification: {str(e)}")
        sys.exit(1)
