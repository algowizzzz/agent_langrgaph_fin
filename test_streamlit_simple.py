import streamlit as st

st.title("🧪 Simple Test App")
st.write("✅ Basic Streamlit is working!")

# Test basic imports without running them
try:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    from orchestrator import Orchestrator
    st.write("✅ Orchestrator import successful")
    
    from tools.memory_tools import conversation_memory
    st.write("✅ Memory tools import successful")
    
    from tools.document_tools import upload_document
    st.write("✅ Document tools import successful")
    
    st.write("🎉 All components are working!")
    
except Exception as e:
    st.error(f"❌ Import error: {e}")
    st.write("This is the source of the loading issue.")