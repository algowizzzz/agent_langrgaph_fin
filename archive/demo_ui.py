"""
Quick demo script to showcase the Streamlit UI capabilities
"""

import os
import subprocess
import sys
from pathlib import Path

def main():
    print("🎨 Document Intelligence Agent - Streamlit UI Demo")
    print("=" * 55)
    
    print("\n📋 Pre-flight checks:")
    
    # Check if we're in the right directory
    if not Path("streamlit_app.py").exists():
        print("❌ streamlit_app.py not found. Run this from the project root.")
        return
    
    print("✅ Streamlit app found")
    
    # Check virtual environment
    if Path("venv").exists():
        print("✅ Virtual environment detected")
    else:
        print("⚠️  No virtual environment found (optional)")
    
    # Check if Streamlit is installed
    try:
        import streamlit
        print(f"✅ Streamlit {streamlit.__version__} installed")
    except ImportError:
        print("❌ Streamlit not installed. Installing now...")
        subprocess.run([sys.executable, "-m", "pip", "install", "streamlit", "plotly"])
    
    # Check if our agent components exist
    if Path("orchestrator.py").exists():
        print("✅ Orchestrator found")
    if Path("tools").exists():
        print("✅ Tools directory found")
    if Path("memory").exists():
        print("✅ Memory system found")
    
    print("\n🌟 UI Features Available:")
    print("  • Professional chat interface with gradients")
    print("  • Document upload (PDF, DOCX, TXT, CSV)")
    print("  • Real-time reasoning display")
    print("  • Chat history with memory persistence")
    print("  • All 17 agent tools accessible")
    print("  • Responsive design for desktop/mobile")
    
    print("\n🚀 Starting Streamlit UI...")
    print("💡 The UI will open in your default browser")
    print("📍 URL: http://localhost:8501")
    print("🔄 Use Ctrl+C to stop the server")
    
    print("\n📚 Quick Start Tips:")
    print("  1. Upload a document using the left sidebar")
    print("  2. Try: 'Summarize the entire document'")
    print("  3. Try: 'Extract all regulations as a bullet list'")
    print("  4. Watch the reasoning process in real-time!")
    
    print("\n" + "=" * 55)
    input("Press Enter to launch the UI...")
    
    # Launch Streamlit
    try:
        # Set environment variable for Python path
        env = os.environ.copy()
        env['PYTHONPATH'] = f"{env.get('PYTHONPATH', '')}:{os.getcwd()}"
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ], env=env)
    except KeyboardInterrupt:
        print("\n👋 Streamlit UI stopped. Thanks for the demo!")
    except Exception as e:
        print(f"\n❌ Error launching UI: {e}")
        print("💡 Try running manually: streamlit run streamlit_app.py")

if __name__ == "__main__":
    main()