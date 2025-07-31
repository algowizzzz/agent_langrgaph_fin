import streamlit as st

st.title("🧪 Minimal Test")
st.write("✅ Streamlit is working!")

if st.button("Test Backend"):
    st.write("Testing imports...")
    
    try:
        import sys, os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        st.write("✅ Path setup done")
        
        # Test one import at a time
        st.write("Testing orchestrator import...")
        from orchestrator import Orchestrator
        st.write("✅ Orchestrator imported")
        
        st.write("Creating orchestrator instance...")
        orch = Orchestrator()
        st.write("✅ Orchestrator created successfully!")
        
    except Exception as e:
        st.error(f"❌ Error: {e}")
        import traceback
        st.text(traceback.format_exc())