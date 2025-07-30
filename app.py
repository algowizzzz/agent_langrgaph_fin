import streamlit as st
import requests
import uuid
from pathlib import Path
import yaml
from typing import Dict, Any

# Load configuration
def load_config() -> Dict[str, Any]:
    """Load configuration from YAML file."""
    config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}

config = load_config()

# Constants from config
MAX_FILE_SIZE_MB = config.get('upload', {}).get('max_file_size_mb', 10)
ALLOWED_EXTENSIONS = config.get('upload', {}).get('allowed_extensions', ['.doc', '.docx', '.xlsx', '.csv', '.pdf'])
API_BASE_URL = "http://localhost:8000"

def validate_file_client_side(uploaded_file) -> tuple[bool, str]:
    """Client-side file validation."""
    if uploaded_file is None:
        return False, "No file selected"
    
    # Check file size
    if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return False, f"File size {uploaded_file.size / (1024*1024):.1f}MB exceeds {MAX_FILE_SIZE_MB}MB limit"
    
    # Check file extension
    file_ext = Path(uploaded_file.name).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"File type {file_ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
    
    return True, "Valid file"

def upload_file_to_backend(session_id: str, uploaded_file) -> tuple[bool, str, str]:
    """Upload file to backend API."""
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        params = {"session_id": session_id}
        
        response = requests.post(f"{API_BASE_URL}/upload", files=files, params=params)
        
        if response.status_code == 200:
            result = response.json()
            return True, result.get("file_id", ""), "Upload successful"
        else:
            error_data = response.json()
            return False, "", error_data.get("message", "Upload failed")
            
    except requests.exceptions.RequestException as e:
        return False, "", f"Connection error: {str(e)}"
    except Exception as e:
        return False, "", f"Upload error: {str(e)}"

def send_chat_message(session_id: str, messages: list, uploaded_files: dict) -> tuple[bool, str, str, list, str]:
    """Send chat message to backend API."""
    try:
        payload = {
            "session_id": session_id,
            "messages": messages,
            "uploaded_files": uploaded_files
        }
        
        response = requests.post(f"{API_BASE_URL}/chat", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            content = result.get("content", "")
            source = result.get("source", "")
            reasoning_steps = result.get("reasoning_steps", [])
            thoughts = result.get("thoughts", "")
            return True, content, source, reasoning_steps, thoughts
        else:
            error_data = response.json()
            return False, "", error_data.get("message", "Chat request failed"), [], ""
            
    except requests.exceptions.RequestException as e:
        return False, "", f"Connection error: {str(e)}", [], ""
    except Exception as e:
        return False, "", f"Chat error: {str(e)}", [], ""

def cleanup_session(session_id: str) -> bool:
    """Clean up session on backend."""
    try:
        response = requests.delete(f"{API_BASE_URL}/session/{session_id}")
        return response.status_code == 200
    except:
        return False

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}

# Main UI
st.title("BMO Documentation Analysis Tool")

# Sidebar
with st.sidebar:
    st.header("File Upload")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=[ext.lstrip('.') for ext in ALLOWED_EXTENSIONS],
        help=f"Max size: {MAX_FILE_SIZE_MB}MB. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
    )
    
    if uploaded_file is not None:
        # Client-side validation
        is_valid, validation_message = validate_file_client_side(uploaded_file)
        
        if is_valid:
            # Check if file is already uploaded
            if uploaded_file.name not in st.session_state.uploaded_files:
                with st.spinner("Uploading file..."):
                    success, file_id, message = upload_file_to_backend(
                        st.session_state.session_id, uploaded_file
                    )
                
                if success:
                    st.success(f"✅ {uploaded_file.name} uploaded successfully!")
                    
                    # Add to session state
                    st.session_state.uploaded_files[uploaded_file.name] = {
                        "id": file_id,
                        "role": "Content"  # Default role
                    }
                else:
                    st.error(f"❌ Upload failed: {message}")
            else:
                st.info(f"📄 {uploaded_file.name} already uploaded")
        else:
            st.error(f"❌ {validation_message}")
    
    # Display uploaded files
    if st.session_state.uploaded_files:
        st.subheader("Uploaded Files")
        for filename, file_info in st.session_state.uploaded_files.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(f"📄 {filename}")
                # Role selector
                role = st.selectbox(
                    f"Role for {filename}",
                    ["Content", "Template"],
                    index=0 if file_info["role"] == "Content" else 1,
                    key=f"role_{filename}"
                )
                st.session_state.uploaded_files[filename]["role"] = role
            
            with col2:
                if st.button("🗑️", key=f"delete_{filename}"):
                    del st.session_state.uploaded_files[filename]
                    st.rerun()
    
    st.divider()
    
    # Session controls
    st.subheader("Session Controls")
    
    if st.button("Clear Session", type="secondary"):
        # Clean up backend
        cleanup_session(st.session_state.session_id)
        
        # Clear session state
        st.session_state.messages = []
        st.session_state.uploaded_files = {}
        st.session_state.session_id = str(uuid.uuid4())
        
        st.success("Session cleared!")
        st.rerun()
    
    # Display session info
    st.caption(f"Session ID: {st.session_state.session_id[:8]}...")

# Main chat area
st.subheader("Chat")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "source" in message and message["source"]:
            st.caption(f"Source: {message['source']}")

# Chat input
if prompt := st.chat_input("Ask a question or request document analysis..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Send to backend
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            success, response_content, source, reasoning_steps, thoughts = send_chat_message(
                st.session_state.session_id,
                st.session_state.messages,
                st.session_state.uploaded_files
            )
        
        if success:
            # Show reasoning steps if available
            if reasoning_steps:
                st.markdown("**🤔 Agent Thinking Process**")
                
                # Custom CSS for tighter spacing
                st.markdown("""
                <style>
                    ul.reasoning-steps {
                        list-style-type: none;
                        padding-left: 0;
                        margin-top: 0.5rem;
                        margin-bottom: 0;
                    }
                    ul.reasoning-steps li {
                        margin-bottom: 0.2rem;
                        padding-left: 0;
                    }
                </style>
                """, unsafe_allow_html=True)

                reasoning_html = "<ul class='reasoning-steps'>"
                for i, step in enumerate(reasoning_steps, 1):
                    step_name = step.get("step", f"Step {i}")
                    thought = step.get("thought", "")
                    reasoning_html += f"<li><small><b>{i}. {step_name}:</b> <i>{thought}</i></small></li>"
                reasoning_html += "</ul>"
                
                st.markdown(reasoning_html, unsafe_allow_html=True)
            
            # Show the main response
            st.write(response_content)
            if source:
                st.caption(f"Source: {source}")
            
            # Add assistant response to chat history
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_content,
                "source": source
            })
        else:
            error_message = f"❌ Error: {response_content}"
            st.error(error_message)
            
            # Add error to chat history
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_message
            })

# Display connection status
try:
    health_response = requests.get(f"{API_BASE_URL}/health", timeout=2)
    if health_response.status_code == 200:
        st.sidebar.success("🟢 Backend Connected")
    else:
        st.sidebar.error("🔴 Backend Error")
except:
    st.sidebar.error("🔴 Backend Disconnected")