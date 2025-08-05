import streamlit as st

st.write("🧪 Debug App Starting...")

# Test 1: Basic imports
try:
    st.write("Testing basic imports...")
    import sys
    import os
    from datetime import datetime
    st.write("✅ Basic imports successful")
except Exception as e:
    st.error(f"❌ Basic imports failed: {e}")
    st.stop()

# Test 2: Path setup
try:
    st.write("Setting up path...")
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    st.write("✅ Path setup successful")
except Exception as e:
    st.error(f"❌ Path setup failed: {e}")
    st.stop()

# Test 3: Environment loading
try:
    st.write("Loading environment...")
    from dotenv import load_dotenv
    load_dotenv()
    if not os.getenv('ANTHROPIC_API_KEY'):
        load_dotenv('../.env')
    st.write("✅ Environment loading successful")
except Exception as e:
    st.error(f"❌ Environment loading failed: {e}")
    st.stop()

# Test 4: Orchestrator import
try:
    st.write("Importing orchestrator...")
    from orchestrator import Orchestrator
    st.write("✅ Orchestrator import successful")
except Exception as e:
    st.error(f"❌ Orchestrator import failed: {e}")
    st.stop()

# Test 5: Memory tools import
try:
    st.write("Importing memory tools...")
    from tools.memory_tools import conversation_memory
    st.write("✅ Memory tools import successful")
except Exception as e:
    st.error(f"❌ Memory tools import failed: {e}")
    st.stop()

st.write("🎉 All tests passed! The issue is elsewhere.")