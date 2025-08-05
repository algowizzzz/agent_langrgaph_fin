# 🚀 Backend Terminal Testing Guide

## 🔧 **Streaming Fix Implemented**

The streaming error has been **FIXED**! The issue was in the `progress_callback` function in `orchestrator_v2.py` that was incorrectly implemented as an async generator.

### **What Was Fixed:**
- ❌ **Before**: `progress_callback` used `yield` (async generator) but was called with `await`
- ✅ **After**: `progress_callback` uses `asyncio.Queue` to properly handle streaming events

---

## 🎯 **Quick Testing Steps**

### **1. Start the Backend**
```bash
cd /Users/saadahmed/Desktop/Apps/AWS_Extra/Agent
python main.py
```

### **2. Test Backend (Simple)**
```bash
# Test basic functionality
python test_query.py

# Test with custom query
python test_query.py "What is risk management?"

# Test streaming specifically
python test_query.py --stream "Explain finance concepts"
```

### **3. Test with cURL**
```bash
# Health check
curl http://localhost:8000/health

# System status
curl http://localhost:8000/system/status | jq

# Simple query
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is finance?",
    "session_id": "test-123",
    "active_documents": []
  }' | jq '.final_answer'
```

---

## 🎨 **Launch Streamlit UI**

### **Option 1: Quick Launch**
```bash
./run_streamlit_chat.sh
```

### **Option 2: Full Demo**
```bash
./start_full_demo.sh
```

### **Option 3: Manual**
```bash
streamlit run streamlit_chat_ui.py
```

---

## 📊 **Expected Results**

### **Backend Startup:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Started server process [12345]
2025-08-03 22:35:00 - orchestrator_v2.orchestrator_v2 - INFO - Orchestrator 2.0 initialized successfully
```

### **Successful Query:**
```json
{
  "status": "success",
  "final_answer": "I am an AI Finance and Risk Agent designed to help with document analysis...",
  "confidence_score": 0.85,
  "processing_time_ms": 1250,
  "session_id": "test-123"
}
```

### **Streaming Response:**
```
📡 Receiving events:
   📨 reasoning_step: 🚀 Orchestrator 2.0 analyzing your query...
   📨 reasoning_step: ✅ Plan created with 3 steps
   📨 tool_execution: ✅ knowledge_search completed
   📨 final_answer: Complete response ready
```

---

## 🔍 **Troubleshooting**

### **❌ "Connection refused"**
**Solution**: Make sure backend is running
```bash
python main.py
```

### **❌ Streaming still fails**
**Solution**: Use non-streaming endpoint
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "session_id": "test"}'
```

### **❌ Import errors**
**Solution**: Activate virtual environment
```bash
source venv/bin/activate  # or activate.bat on Windows
```

---

## 🎯 **Test Scenarios**

### **1. Basic Q&A**
```bash
python test_query.py "Who are you?"
```

### **2. Finance Query**
```bash
python test_query.py "What is risk management?"
```

### **3. Streaming Test**
```bash
python test_query.py --stream "Explain financial analysis"
```

### **4. Document Upload & Analysis**
```bash
# Upload document
curl -X POST "http://localhost:8000/upload" \
  -F "file=@your_document.pdf" \
  -F "session_id=test-session"

# Query with document
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Summarize this document",
    "session_id": "test-session",
    "active_documents": ["your_document.pdf"]
  }'
```

---

## ✨ **Features Now Working**

- ✅ **Non-streaming chat** (`/chat`) - Fully functional
- ✅ **Streaming chat** (`/chat/stream`) - **FIXED!**
- ✅ **Document upload** (`/upload`) - Working
- ✅ **Multi-document analysis** - Working
- ✅ **Memory integration** - Working
- ✅ **System status** (`/system/status`) - Working
- ✅ **Streamlit UI** - Ready to use

---

## 🚀 **Ready to Use!**

Your AI Finance and Risk Agent is now **fully functional** with both terminal and web interfaces!

**Start testing**: `python test_query.py`
**Launch UI**: `./run_streamlit_chat.sh`

🎉 **The streaming issue has been resolved!**