"""
Demo script for the new Meta-inspired UI
"""

import os
import subprocess
import sys

def main():
    print("🎨 NEW META-INSPIRED UI DEMO")
    print("=" * 50)
    
    print("\n✨ Design Highlights:")
    print("  • Meta/Facebook blue (#1877F2) and white theme")
    print("  • Compact sidebar (280px) with reduced font sizes")
    print("  • Collapsible agent reasoning sections")
    print("  • Clean, professional message bubbles")
    print("  • High contrast, readable typography")
    print("  • Streamlined document management")
    
    print("\n🎯 Key Improvements:")
    print("  • Much smaller sidebar for better content focus")
    print("  • 13px base font size (was larger)")
    print("  • Agent reasoning now collapses into expandable sections")
    print("  • Better formatted responses with proper spacing")
    print("  • Meta-style visual hierarchy and spacing")
    
    print("\n📱 Responsive Features:")
    print("  • Works great on desktop and mobile")
    print("  • Proper contrast for accessibility")
    print("  • Clean, distraction-free interface")
    
    print("\n🚀 Ready to Launch:")
    print("  • Upload your riskandfinace.pdf")
    print("  • Ask for a comprehensive summary")
    print("  • See the new collapsible reasoning")
    print("  • Experience the clean, professional design")
    
    print("\n" + "=" * 50)
    input("Press Enter to launch the new UI...")
    
    # Launch Streamlit with the new design
    try:
        env = os.environ.copy()
        env['PYTHONPATH'] = f"{env.get('PYTHONPATH', '')}:{os.getcwd()}"
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ], env=env)
    except KeyboardInterrupt:
        print("\n👋 Demo finished! Hope you enjoyed the new design!")

if __name__ == "__main__":
    main()