"""
Professional Document Intelligence Agent - Streamlit UI
Sleek, minimal interface with chat history, document upload, and reasoning display.
"""

import streamlit as st
import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path
import uuid
import tempfile
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()  # Try current directory first
if not os.getenv('ANTHROPIC_API_KEY'):
    load_dotenv('../.env')  # Fallback to parent directory

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestrator import Orchestrator
from tools.memory_tools import conversation_memory
from tools.document_tools import upload_document

# Page configuration
st.set_page_config(
    page_title="Document Intelligence Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Simple clean design - White background + Black text + Light grey bubbles
st.markdown("""
<style>
    /* Simple color palette */
    :root {
        --primary-blue: #1877F2;
        --text-black: #000000;
        --text-gray: #555555;
        --background-white: #FFFFFF;
        --bubble-light-gray: #F5F5F5;
        --border-gray: #DDDDDD;
        --input-bg: #FFFFFF;
    }
    
    /* Hide Streamlit defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .reportview-container .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Overall app styling */
    .stApp {
        background-color: var(--background-white);
    }
    
    /* Compact sidebar */
    .css-1d391kg {
        width: 280px !important;
        background-color: var(--background-white);
        border-right: 1px solid var(--border-gray);
    }
    
    /* Sidebar content sizing */
    .css-1d391kg .element-container {
        margin-bottom: 0.5rem;
    }
    
    /* Simple font styling */
    html, body, [class*="css"] {
        font-size: 14px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
        color: var(--text-black);
    }
    
    /* Clean chat messages */
    .user-message {
        background-color: var(--primary-blue);
        color: white;
        padding: 10px 14px;
        border-radius: 18px;
        margin: 8px 0 8px 20%;
        font-size: 14px;
        line-height: 1.4;
        max-width: 70%;
    }
    
    .assistant-message {
        background-color: var(--bubble-light-gray);
        color: var(--text-black);
        padding: 12px 16px;
        border-radius: 18px;
        margin: 8px 20% 8px 0;
        font-size: 14px;
        line-height: 1.5;
        max-width: 75%;
    }
    
    /* Simple reasoning styling with better formatting */
    .reasoning-content {
        background-color: var(--bubble-light-gray);
        padding: 12px 16px;
        border-radius: 8px;
        color: var(--text-gray);
        line-height: 1.6;
        font-size: 13px;
        font-family: "SF Mono", Monaco, "Courier New", monospace;
        white-space: pre-line;  /* Preserve line breaks */
    }
    
    /* Better spacing for steps */
    .reasoning-content br {
        margin-bottom: 4px;
    }
    
    /* Simple buttons */
    .stButton > button {
        border-radius: 8px;
        border: 1px solid var(--border-gray);
        background-color: var(--primary-blue);
        color: white;
        font-weight: 500;
        font-size: 14px;
        padding: 8px 16px;
        height: 40px;
    }
    
    .stButton > button:hover {
        background-color: #0d5bc9;
    }
    
    /* Fixed text input - WHITE background with BLACK text */
    .stTextInput > div > div > input {
        border-radius: 24px;
        border: 2px solid var(--border-gray);
        padding: 10px 16px;
        font-size: 14px;
        height: 44px;
        background-color: var(--input-bg) !important;
        color: var(--text-black) !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: var(--text-gray) !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-blue);
        outline: none;
    }
    
    /* Compact file uploader */
    .stFileUploader > div {
        padding: 1rem 0.5rem;
    }
    
    /* Sidebar headers */
    .sidebar-header {
        color: var(--text-black);
        font-size: 15px;
        font-weight: 600;
        margin-bottom: 8px;
        padding: 0 4px;
    }
    
    /* Document list */
    .doc-item {
        background-color: var(--bubble-light-gray);
        border: 1px solid var(--border-gray);
        border-radius: 8px;
        padding: 8px 10px;
        margin: 4px 0;
        font-size: 12px;
        color: var(--text-black);
    }
    
    .doc-item.active {
        background-color: var(--primary-blue);
        border-color: var(--primary-blue);
        color: white;
    }
    
    /* Chat history items */
    .chat-item {
        background-color: var(--bubble-light-gray);
        border: 1px solid var(--border-gray);
        border-radius: 8px;
        padding: 8px 10px;
        margin: 4px 0;
        font-size: 12px;
        color: var(--text-black);
        cursor: pointer;
    }
    
    .chat-item:hover {
        background-color: #EEEEEE;
    }
    
    .chat-item.active {
        background-color: var(--primary-blue);
        border-color: var(--primary-blue);
        color: white;
    }
    
    /* Compact spacing */
    .element-container {
        margin-bottom: 0.5rem;
    }
    
    /* Status indicators */
    .status-thinking {
        color: var(--primary-blue);
        font-size: 12px;
    }
    
    .status-success {
        color: #28A745;
        font-size: 12px;
    }
    
    .status-error {
        color: #DC3545;
        font-size: 12px;
    }
    
    /* Welcome message */
    .welcome-container {
        text-align: center;
        padding: 2rem 1rem;
        color: var(--text-gray);
        background-color: var(--background-white);
        border-radius: 12px;
        margin: 1rem 0;
        border: 1px solid var(--border-gray);
    }
    
    .welcome-container h3 {
        color: var(--text-black);
        font-size: 20px;
        margin-bottom: 0.5rem;
    }
    
    .welcome-container p {
        font-size: 14px;
        line-height: 1.4;
        margin-bottom: 0.5rem;
    }
    
    .welcome-container ul {
        font-size: 13px;
        text-align: left;
        display: inline-block;
        margin: 0.5rem 0;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .css-1d391kg {
            width: 240px !important;
        }
        .user-message, .assistant-message, .reasoning-container {
            margin-left: 5%;
            margin-right: 5%;
            max-width: 90%;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_chat_id' not in st.session_state:
    st.session_state.current_chat_id = None
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = {}
if 'uploaded_documents' not in st.session_state:
    st.session_state.uploaded_documents = []
if 'active_document' not in st.session_state:
    st.session_state.active_document = None
if 'chat_documents' not in st.session_state:
    st.session_state.chat_documents = {}  # Maps chat_id to active document

async def initialize_orchestrator():
    """Initialize the orchestrator asynchronously."""
    if st.session_state.orchestrator is None:
        st.session_state.orchestrator = Orchestrator()
    return st.session_state.orchestrator

async def load_chat_history():
    """Load chat history from memory system."""
    try:
        stats = await conversation_memory.get_memory_stats()
        # Get recent conversations from memory
        context = await conversation_memory.get_context()
        
        # Build chat history from memory
        if context.get('short_term'):
            chat_id = "current_session"
            if chat_id not in st.session_state.chat_history:
                st.session_state.chat_history[chat_id] = {
                    'messages': [],
                    'first_query': 'Current Session',
                    'created_at': datetime.now().isoformat()
                }
            
            # Convert memory messages to chat format
            for msg in context['short_term']:
                if msg['role'] in ['user', 'assistant']:
                    st.session_state.chat_history[chat_id]['messages'].append({
                        'role': msg['role'],
                        'content': msg['content'],
                        'timestamp': msg['timestamp']
                    })
    except Exception as e:
        st.error(f"Error loading chat history: {e}")

def create_new_chat():
    """Create a new chat session."""
    chat_id = str(uuid.uuid4())[:8]
    st.session_state.current_chat_id = chat_id
    st.session_state.messages = []
    st.session_state.chat_history[chat_id] = {
        'messages': [],
        'first_query': 'New Chat',
        'created_at': datetime.now().isoformat()
    }

def switch_to_chat(chat_id):
    """Switch to an existing chat."""
    st.session_state.current_chat_id = chat_id
    st.session_state.messages = st.session_state.chat_history[chat_id]['messages'].copy()
    
    # Restore active document for this chat
    if chat_id in st.session_state.chat_documents:
        st.session_state.active_document = st.session_state.chat_documents[chat_id]
    else:
        st.session_state.active_document = None

async def process_uploaded_file(uploaded_file):
    """Process uploaded file through the document system."""
    if uploaded_file is not None:
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # Upload document using our system
            result = await upload_document(tmp_path)
            
            # Clean up temporary file
            os.unlink(tmp_path)
            
            if result.get('status') == 'success':
                doc_info = {
                    'name': uploaded_file.name,
                    'doc_name': result.get('doc_name'),
                    'chunks_created': result.get('chunks_created'),
                    'uploaded_at': datetime.now().isoformat()
                }
                st.session_state.uploaded_documents.append(doc_info)
                
                # Set as active document for current chat
                st.session_state.active_document = result.get('doc_name')
                if st.session_state.current_chat_id:
                    st.session_state.chat_documents[st.session_state.current_chat_id] = result.get('doc_name')
                
                return True, f"✅ Successfully uploaded '{uploaded_file.name}' ({result.get('chunks_created')} chunks created)"
            else:
                return False, f"❌ Failed to upload '{uploaded_file.name}': {result.get('message', 'Unknown error')}"
                
        except Exception as e:
            return False, f"❌ Error uploading '{uploaded_file.name}': {str(e)}"
    
    return False, "No file provided"

async def process_user_message(user_input):
    """Process user message through the orchestrator."""
    if not user_input.strip():
        return
    
    # Add user message
    user_msg = {
        'role': 'user',
        'content': user_input,
        'timestamp': datetime.now().isoformat()
    }
    st.session_state.messages.append(user_msg)
    
    # Update chat history
    if st.session_state.current_chat_id:
        st.session_state.chat_history[st.session_state.current_chat_id]['messages'].append(user_msg)
        # Update first query if this is the first message
        if len(st.session_state.chat_history[st.session_state.current_chat_id]['messages']) == 1:
            st.session_state.chat_history[st.session_state.current_chat_id]['first_query'] = user_input[:50] + "..." if len(user_input) > 50 else user_input
    
    # Add to memory system
    await conversation_memory.add_message('user', user_input, st.session_state.current_chat_id)
    
    # Show thinking status
    thinking_placeholder = st.empty()
    thinking_placeholder.markdown(
        '<div class="reasoning-message"><span class="status-thinking">🤔 Agent is thinking...</span></div>',
        unsafe_allow_html=True
    )
    
    try:
        # Get orchestrator
        orchestrator = await initialize_orchestrator()
        
        # Get active document for this chat
        active_doc = None
        if st.session_state.current_chat_id and st.session_state.current_chat_id in st.session_state.chat_documents:
            active_doc = st.session_state.chat_documents[st.session_state.current_chat_id]
        elif st.session_state.active_document:
            active_doc = st.session_state.active_document
        
        # Process through orchestrator with context
        result = await orchestrator.run(user_input, st.session_state.current_chat_id or 'default', active_document=active_doc)
        
        # Clear thinking indicator
        thinking_placeholder.empty()
        
        # Add reasoning FIRST (if available) - with proper line breaks
        if result.get('reasoning_log'):
            reasoning_content = "Reasoning Steps:\n\n"
            for i, step in enumerate(result['reasoning_log'], 1):
                if isinstance(step, dict) and 'tool_name' in step:
                    tool_params = step.get('tool_params', {})
                    
                    # Main step
                    reasoning_content += f"Step {i}: {step['tool_name']}\n"
                    
                    # Sub-steps with parameters
                    if tool_params:
                        reasoning_content += "Parameters:\n"
                        for key, value in tool_params.items():
                            # Format value nicely
                            if isinstance(value, str) and len(value) > 100:
                                formatted_value = value[:100] + "..."
                            elif isinstance(value, dict):
                                formatted_value = f"{{{len(value)} items}}"
                            elif isinstance(value, list):
                                formatted_value = f"[{len(value)} items]"
                            else:
                                formatted_value = str(value)
                            
                            reasoning_content += f"  • {key}: {formatted_value}\n"
                    
                    reasoning_content += "\n"  # Extra line between steps
            
            reasoning_msg = {
                'role': 'reasoning',
                'content': reasoning_content,
                'timestamp': datetime.now().isoformat()
            }
            st.session_state.messages.append(reasoning_msg)
        
        # Add assistant response SECOND (clean separation)
        response_content = result.get('final_answer', 'No response generated')
        
        # Clean up the response - remove any extra status info
        if isinstance(response_content, dict):
            if 'error' in response_content:
                response_content = f"Sorry, there was an error: {response_content['error']}"
            else:
                response_content = str(response_content)
        
        assistant_msg = {
            'role': 'assistant',
            'content': response_content,
            'timestamp': datetime.now().isoformat(),
            'status': result.get('status', 'unknown')
        }
        st.session_state.messages.append(assistant_msg)
        
        # Update chat history
        if st.session_state.current_chat_id:
            st.session_state.chat_history[st.session_state.current_chat_id]['messages'].extend([
                reasoning_msg if 'reasoning_msg' in locals() else None,
                assistant_msg
            ])
            st.session_state.chat_history[st.session_state.current_chat_id]['messages'] = [
                msg for msg in st.session_state.chat_history[st.session_state.current_chat_id]['messages'] if msg is not None
            ]
        
        # Add to memory system
        await conversation_memory.add_message('assistant', response_content, st.session_state.current_chat_id)
        
    except Exception as e:
        thinking_placeholder.empty()
        error_msg = {
            'role': 'assistant',
            'content': f"❌ Error processing your request: {str(e)}",
            'timestamp': datetime.now().isoformat(),
            'status': 'error'
        }
        st.session_state.messages.append(error_msg)
        await conversation_memory.add_message('assistant', f"Error: {str(e)}", st.session_state.current_chat_id)

def render_sidebar():
    """Render the compact sidebar with Meta styling."""
    with st.sidebar:
        # App title - more compact
        st.markdown('<div class="sidebar-header">🤖 AI Document Agent</div>', unsafe_allow_html=True)
        
        # New Chat Button - compact
        if st.button("+ New Chat", use_container_width=True, type="primary"):
            create_new_chat()
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Document Upload Section - compact
        st.markdown('<div class="sidebar-header">📄 Upload</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "",  # No label for compact design
            type=['pdf', 'docx', 'txt', 'csv'],
            help="PDF, DOCX, TXT, CSV",
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            if st.button("Upload", use_container_width=True):
                success, message = asyncio.run(process_uploaded_file(uploaded_file))
                if success:
                    st.success("✅ Uploaded!")
                else:
                    st.error("❌ Failed")
                st.rerun()
        
        # Show uploaded documents - compact
        if st.session_state.uploaded_documents:
            st.markdown('<div class="sidebar-header">📚 Documents</div>', unsafe_allow_html=True)
            
            # Get active document for current chat
            active_doc = None
            if st.session_state.current_chat_id and st.session_state.current_chat_id in st.session_state.chat_documents:
                active_doc = st.session_state.chat_documents[st.session_state.current_chat_id]
            elif st.session_state.active_document:
                active_doc = st.session_state.active_document
            
            for doc in st.session_state.uploaded_documents[-3:]:  # Show last 3 only
                is_active = doc['doc_name'] == active_doc
                css_class = "doc-item active" if is_active else "doc-item"
                icon = "🎯" if is_active else "📄"
                
                st.markdown(
                    f'<div class="{css_class}">{icon} {doc["name"][:20]}{"..." if len(doc["name"]) > 20 else ""}<br><small>{doc["chunks_created"]} chunks</small></div>',
                    unsafe_allow_html=True
                )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Chat History - compact
        st.markdown('<div class="sidebar-header">💬 History</div>', unsafe_allow_html=True)
        
        # Load chat history
        asyncio.run(load_chat_history())
        
        if st.session_state.chat_history:
            for chat_id, chat_data in sorted(
                st.session_state.chat_history.items(),
                key=lambda x: x[1]['created_at'],
                reverse=True
            )[:5]:  # Show only last 5 chats
                is_active = chat_id == st.session_state.current_chat_id
                css_class = "chat-item active" if is_active else "chat-item"
                
                # Truncate chat name
                chat_name = chat_data['first_query'][:25] + "..." if len(chat_data['first_query']) > 25 else chat_data['first_query']
                
                if st.button(
                    chat_name,
                    key=f"chat_{chat_id}",
                    use_container_width=True
                ):
                    switch_to_chat(chat_id)
                    st.rerun()
        else:
            st.markdown('<div class="doc-item">No chats yet</div>', unsafe_allow_html=True)

def render_chat_messages():
    """Render chat messages with Meta-style design and collapsible reasoning."""
    # Compact header
    st.markdown('<div style="color: var(--meta-text); font-size: 16px; font-weight: 600; margin-bottom: 1rem;">💬 Document Intelligence Agent</div>', unsafe_allow_html=True)
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.messages:
            st.markdown("""
            <div class="welcome-container">
                <h3>👋 Welcome to Document Intelligence Agent</h3>
                <p>Upload a document and start asking questions, or begin a conversation!</p>
                <p><strong>Example queries:</strong></p>
                <ul>
                    <li>Summarize the entire document</li>
                    <li>Find all regulatory requirements</li>
                    <li>Analyze risk factors in the document</li>
                    <li>Extract key financial data</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Display messages with new styling
            for i, message in enumerate(st.session_state.messages):
                if message['role'] == 'user':
                    st.markdown(
                        f'<div class="user-message">👤 {message["content"]}</div>',
                        unsafe_allow_html=True
                    )
                elif message['role'] == 'reasoning':
                    # Clean collapsible reasoning with proper formatting
                    with st.expander("🔍 How I solved this", expanded=False):
                        # Format the reasoning content with proper line breaks
                        formatted_content = message["content"]
                        
                        # Replace newlines with HTML breaks for proper display
                        formatted_content = formatted_content.replace('\n\n', '<br><br>')  # Double breaks for paragraphs
                        formatted_content = formatted_content.replace('\n', '<br>')        # Single breaks for lines
                        
                        st.markdown(f"""
                        <div class="reasoning-content">
                            {formatted_content}
                        </div>
                        """, unsafe_allow_html=True)
                        
                elif message['role'] == 'assistant':
                    # Clean assistant response - no extra labels
                    content = message["content"]
                    
                    # Clean up any unwanted formatting
                    if isinstance(content, str):
                        # Remove any "Agent:" prefixes that might be in content
                        content = content.replace('Agent:', '').strip()
                        # Simple line break formatting
                        content = content.replace('\n\n', '<br><br>')
                        content = content.replace('\n', '<br>')
                    
                    st.markdown(
                        f'<div class="assistant-message">{content}</div>',
                        unsafe_allow_html=True
                    )

def main():
    """Main application function."""
    # Render sidebar
    render_sidebar()
    
    # Main chat area
    render_chat_messages()
    
    # Compact input area
    st.markdown('<div style="margin-top: 1rem; border-top: 1px solid var(--meta-border); padding-top: 1rem;"></div>', unsafe_allow_html=True)
    
    # Create new chat if none exists
    if not st.session_state.current_chat_id:
        create_new_chat()
    
    # Chat input with Meta styling
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_input(
            "",
            placeholder="Ask about your documents...",
            key="chat_input",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("Send", use_container_width=True, type="primary")
    
    # Process message
    if send_button and user_input:
        asyncio.run(process_user_message(user_input))
        st.rerun()

if __name__ == "__main__":
    main()