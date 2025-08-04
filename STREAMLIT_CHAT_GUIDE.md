# 🤖 AI Finance & Risk Agent - Streamlit Chat UI Guide

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.8+ installed
- Your FastAPI backend running on `http://localhost:8000`

### **Installation & Launch**
```bash
# Option 1: Use the automated launcher (recommended)
./run_streamlit_chat.sh

# Option 2: Manual installation
pip install -r streamlit_requirements.txt
streamlit run streamlit_chat_ui.py
```

### **Access the Chat Interface**
- **URL**: http://localhost:8501
- **Auto-opens**: In your default web browser

---

## ✨ **Features Overview**

### **🎯 Core Chat Features**
- ✅ **Real-time Streaming**: Live AI responses with reasoning steps
- ✅ **Multi-Document Analysis**: Select and analyze multiple documents
- ✅ **Memory Integration**: Conversation history maintained automatically
- ✅ **Document Management**: Upload, select, and manage documents
- ✅ **Modern UI**: ChatGPT-style interface with reasoning transparency

### **📄 Document Support**
| Format | Features | Example Use Cases |
|--------|----------|-------------------|
| **PDF** | Full text extraction, chunking | Financial reports, risk assessments |
| **DOCX** | Rich text processing | Policy documents, procedures |
| **CSV** | Structured data analysis | Financial data, metrics tables |
| **TXT** | Plain text analysis | Notes, transcripts, simple docs |

---

## 🖥️ **User Interface Guide**

### **Main Layout**
```
┌─────────────────────────────────────────────────────────┐
│                    🤖 AI Finance & Risk Agent            │
├─────────────────┬───────────────────────┬───────────────┤
│                 │                       │               │
│   📋 Sidebar    │    💬 Chat Interface  │ 📊 Analytics │
│                 │                       │               │
│ • System Status │ • Message History     │ • Statistics  │
│ • Upload Docs   │ • Streaming Response  │ • Recent      │
│ • Select Docs   │ • Input Area          │   Activity    │
│ • Session Info  │ • Send Button         │               │
│                 │                       │               │
└─────────────────┴───────────────────────┴───────────────┘
```

### **Sidebar Components**

#### **📊 System Status**
- **Green ✅**: Backend operational, all features available
- **Red ❌**: Connection issues or system problems
- **Feature indicators**: Shows which capabilities are active

#### **📄 Document Management**
1. **Upload**: Drag & drop or browse for files
2. **Select**: Choose documents for analysis
3. **Status**: View upload results and chunk information

#### **🔧 Session Info**
- **Session ID**: Unique identifier for your conversation
- **Message Count**: Total messages in current session
- **Clear Option**: Reset conversation history

### **Chat Interface**

#### **💬 Message Display**
- **User messages**: Blue bubbles, right-aligned
- **AI responses**: Gray bubbles, left-aligned with green accent
- **Document chips**: Show which documents were analyzed
- **Reasoning steps**: Expandable sections showing AI's thinking process

#### **📤 Input Area**
- **Text area**: Multi-line input for complex queries
- **Send button**: Processes query with selected documents
- **New chat**: Starts fresh conversation

#### **⚡ Real-time Streaming**
- **Status updates**: "AI is thinking...", "Loading context..."
- **Tool execution**: Live updates as AI uses different tools
- **Progressive display**: Response builds up in real-time

---

## 🎯 **Usage Examples**

### **Single Document Analysis**
1. Upload a document (e.g., `financial_report.pdf`)
2. Select it in the document list
3. Ask: *"What are the key financial highlights?"*
4. Watch the AI analyze in real-time

### **Multi-Document Comparison**
1. Upload multiple related documents
2. Select 2-3 documents
3. Ask: *"Compare the risk factors across these reports"*
4. See comprehensive cross-document analysis

### **Data Analysis (CSV)**
1. Upload a CSV file with financial data
2. Ask: *"Calculate the total revenue and show trends"*
3. Get structured analysis with calculations

### **Expert Query Examples**
```
💼 Finance: "Analyze the liquidity ratios and recommend improvements"
🎯 Risk: "Identify operational risks and their mitigation strategies"
📊 Data: "What patterns do you see in this quarterly data?"
🔍 Comparison: "How do these two policies differ in their approach?"
```

---

## 🔧 **Configuration & Customization**

### **Backend URL Configuration**
Edit `streamlit_chat_ui.py`:
```python
API_BASE_URL = "http://localhost:8000"  # Change this for different backends
```

### **UI Theme Customization**
The launcher script includes theme options:
```bash
--theme.primaryColor "#007bff"        # Primary blue color
--theme.backgroundColor "#ffffff"      # White background
--theme.secondaryBackgroundColor "#f8f9fa"  # Light gray
```

### **Advanced Settings**
```bash
# Custom port
streamlit run streamlit_chat_ui.py --server.port 8502

# Headless mode (no auto-open browser)
streamlit run streamlit_chat_ui.py --server.headless true

# External access
streamlit run streamlit_chat_ui.py --server.address 0.0.0.0
```

---

## 🐛 **Troubleshooting**

### **Common Issues**

#### **❌ "Connection Error"**
**Problem**: Can't connect to backend
**Solution**: 
1. Ensure FastAPI backend is running: `python main.py`
2. Check URL in browser: http://localhost:8000/health
3. Verify API_BASE_URL in `streamlit_chat_ui.py`

#### **❌ "Import Error"**
**Problem**: Missing Python packages
**Solution**:
```bash
pip install -r streamlit_requirements.txt
```

#### **❌ "No Documents Available"**
**Problem**: Documents not showing up
**Solution**:
1. Check upload was successful (green confirmation)
2. Refresh the document list
3. Verify backend storage in `/documents` endpoint

#### **❌ "Streaming Not Working"**
**Problem**: No real-time updates
**Solution**:
1. Check browser console for JavaScript errors
2. Ensure `/chat/stream` endpoint is accessible
3. Try refreshing the page

### **Performance Tips**
- **Large documents**: May take longer to process initially
- **Multiple documents**: Select only relevant ones for faster responses
- **Long conversations**: Use "New Chat" to reset for better performance
- **Browser memory**: Refresh page if UI becomes sluggish

---

## 📈 **Advanced Features**

### **Conversation Memory**
- **Automatic**: Last 10 messages included in context
- **Persistent**: Memory maintained across queries in same session
- **Smart**: Relevant conversation history retrieved when needed

### **Document Intelligence**
- **Chunking**: 10K token chunks for optimal AI processing
- **Cross-reference**: AI can cite specific document sections
- **Metadata**: Extraction of document structure and key information

### **Real-time Experience**
- **Progressive rendering**: Responses appear as they're generated
- **Tool transparency**: See exactly which AI tools are being used
- **Status tracking**: Clear indicators of processing stages

---

## 🚀 **Production Deployment**

### **For Teams/Organizations**

#### **Docker Deployment**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY streamlit_requirements.txt .
RUN pip install -r streamlit_requirements.txt

COPY streamlit_chat_ui.py .
EXPOSE 8501

CMD ["streamlit", "run", "streamlit_chat_ui.py", "--server.address", "0.0.0.0"]
```

#### **Environment Variables**
```bash
export STREAMLIT_API_BASE_URL="https://your-backend.com"
export STREAMLIT_PORT="8501"
```

#### **Security Considerations**
- Use HTTPS in production
- Add authentication if needed
- Implement rate limiting
- Configure CORS properly

---

## 📞 **Support & Next Steps**

### **Getting Help**
1. Check the troubleshooting section above
2. Verify backend logs for API errors
3. Test individual endpoints with curl/Postman
4. Check browser console for JavaScript errors

### **Enhancement Ideas**
- **Authentication**: Add user login system
- **File export**: Download conversation history
- **Templates**: Pre-built query templates for common use cases
- **Collaboration**: Share conversations with team members

**Your Streamlit chat interface is ready for an amazing AI-powered document analysis experience!** 🚀