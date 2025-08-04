#!/usr/bin/env python3
"""
Test script to verify Streamlit chat UI setup
"""

import sys
import subprocess
import importlib.util
import requests
from pathlib import Path

def test_python_imports():
    """Test if required Python packages can be imported."""
    print("🐍 Testing Python imports...")
    
    required_packages = [
        'streamlit',
        'requests', 
        'json',
        'uuid',
        'datetime',
        'pathlib',
        'logging'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'streamlit':
                import streamlit
                print(f"   ✅ {package} (v{streamlit.__version__})")
            elif package == 'requests':
                import requests
                print(f"   ✅ {package} (v{requests.__version__})")
            else:
                __import__(package)
                print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - MISSING")
            missing_packages.append(package)
    
    return missing_packages

def test_backend_connection():
    """Test connection to FastAPI backend."""
    print("\n🔗 Testing backend connection...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Backend is running and accessible")
            return True
        else:
            print(f"   ❌ Backend returned HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ⚠️  Backend not running on http://localhost:8000")
        print("      Start your FastAPI backend first: python main.py")
        return False
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False

def test_files_exist():
    """Test if required files exist."""
    print("\n📁 Testing required files...")
    
    required_files = [
        'streamlit_chat_ui.py',
        'streamlit_requirements.txt',
        'run_streamlit_chat.sh',
        'STREAMLIT_CHAT_GUIDE.md'
    ]
    
    missing_files = []
    
    for file in required_files:
        file_path = Path(file)
        if file_path.exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - MISSING")
            missing_files.append(file)
    
    return missing_files

def test_streamlit_syntax():
    """Test if streamlit_chat_ui.py has valid syntax."""
    print("\n🔍 Testing Streamlit app syntax...")
    
    try:
        spec = importlib.util.spec_from_file_location("streamlit_chat_ui", "streamlit_chat_ui.py")
        if spec is None:
            print("   ❌ Could not load streamlit_chat_ui.py")
            return False
        
        module = importlib.util.module_from_spec(spec)
        # Don't execute, just check syntax
        with open("streamlit_chat_ui.py", 'r') as f:
            compile(f.read(), "streamlit_chat_ui.py", "exec")
        
        print("   ✅ Syntax is valid")
        return True
    except SyntaxError as e:
        print(f"   ❌ Syntax error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def install_missing_packages(packages):
    """Install missing packages using pip."""
    if not packages:
        return True
    
    print(f"\n📦 Installing missing packages: {', '.join(packages)}")
    
    try:
        # Try installing from requirements file first
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'streamlit_requirements.txt'])
        print("   ✅ Packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Installation failed: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 STREAMLIT CHAT UI SETUP TEST")
    print("="*50)
    
    all_tests_passed = True
    
    # Test file existence
    missing_files = test_files_exist()
    if missing_files:
        print(f"\n❌ Missing files: {', '.join(missing_files)}")
        all_tests_passed = False
    
    # Test Python imports
    missing_packages = test_python_imports()
    if missing_packages:
        print(f"\n📦 Attempting to install missing packages...")
        if install_missing_packages(missing_packages):
            # Re-test imports
            missing_packages = test_python_imports()
    
    if missing_packages:
        print(f"\n❌ Still missing packages after installation: {', '.join(missing_packages)}")
        all_tests_passed = False
    
    # Test syntax
    if not test_streamlit_syntax():
        all_tests_passed = False
    
    # Test backend connection (warning only)
    backend_running = test_backend_connection()
    
    # Final summary
    print("\n" + "="*50)
    if all_tests_passed:
        print("✅ ALL TESTS PASSED!")
        print("\n🚀 Ready to launch Streamlit Chat UI:")
        print("   ./run_streamlit_chat.sh")
        
        if not backend_running:
            print("\n⚠️  Remember to start your backend first:")
            print("   python main.py")
    else:
        print("❌ SOME TESTS FAILED!")
        print("\n🔧 Fix the issues above before launching the UI.")
    
    print("\n📖 For detailed instructions, see: STREAMLIT_CHAT_GUIDE.md")

if __name__ == "__main__":
    main()