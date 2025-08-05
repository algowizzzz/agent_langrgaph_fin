# Testing Instructions - BMO Documentation Analysis Tool

## 🚀 Quick Start Guide

### Option 1: Test with Mock Data (No API Keys Required)
```bash
# Run all tests
python3 run_tests.py

# Start the application in mock mode
python3 start_with_api.py
```

### Option 2: Test with Real APIs (Requires API Keys)

1. **Setup API Keys:**
   ```bash
   # Copy the template
   cp .env.template .env
   
   # Edit .env and add your API keys
   nano .env
   ```

2. **Add your API key to .env:**
   ```bash
   # Choose ONE of these:
   ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
   # OR
   OPENAI_API_KEY=sk-your-openai-key-here
   ```

3. **Start the application:**
   ```bash
   python3 start_with_api.py
   ```

## 🎨 UI Overview

The Streamlit interface includes:

### **Main Chat Area**
- Clean chat interface for asking questions
- Real-time responses from AI
- Message history with source attribution
- Support for both Q&A and document analysis

### **Sidebar Features**
- **File Upload**: Drag & drop or browse files
- **File Validation**: Real-time size and type checking
- **File Management**: View uploaded files with role selection
- **Session Controls**: Clear session and start fresh
- **Connection Status**: Backend health indicator

### **Supported File Types**
- 📄 **PDF** - Text extraction and analysis
- 📊 **Excel** (.xlsx) - Multi-sheet processing
- 📝 **Word** (.docx) - Document structure and content
- 📈 **CSV** - Data analysis and insights

## 🧪 Testing Scenarios

### 1. Q&A Testing (No Documents)
Try these questions:
- "What are BMO's hours of operation?"
- "How do I open a new account?"
- "What are the fees for international transfers?"
- "Tell me about BMO's mobile banking features"

### 2. Document Analysis Testing
Upload the test files and try:
- **Employee CSV**: "Analyze the employee distribution by department"
- **Financial CSV**: "What are the revenue trends?"
- **Word Document**: "Summarize the quarterly review"
- **Excel File**: "Extract key financial metrics"
- **PDF Strategy**: "What are the main technology initiatives?"

### 3. Combined Workflow Testing
1. Ask a general question: "What services does BMO offer?"
2. Upload a relevant document
3. Ask: "How does this document relate to BMO's services?"

### 4. Error Handling Testing
- Try uploading files over 10MB
- Upload unsupported file types
- Ask empty questions
- Test session cleanup

## 🔧 Development Testing

### Backend API Testing
```bash
# Check API health
curl http://localhost:8000/health

# Test file upload
curl -X POST -F "file=@test_files/sample.csv" \
     "http://localhost:8000/upload?session_id=test123"

# Test chat endpoint
curl -X POST -H "Content-Type: application/json" \
     -d '{"session_id":"test123","messages":[{"role":"user","content":"Hello"}],"uploaded_files":{}}' \
     http://localhost:8000/chat
```

### API Documentation
Visit: http://localhost:8000/docs for interactive API documentation

## 📊 Expected Results

### With Mock Data:
- **Q&A Responses**: Generic but contextually appropriate responses
- **Document Analysis**: Mock analysis with file statistics and placeholders
- **Processing Time**: Very fast (~0.1-0.5 seconds)
- **Cost**: Free for unlimited testing

### With Real APIs:
- **Q&A Responses**: Detailed, contextually accurate responses
- **Document Analysis**: Comprehensive, insightful analysis
- **Processing Time**: Moderate (~2-10 seconds depending on document size)
- **Cost**: API usage charges apply

## 🐛 Troubleshooting

### Common Issues:

1. **Backend Disconnected**
   - Check if port 8000 is available
   - Restart with: `python3 start_with_api.py`

2. **File Upload Fails**
   - Check file size (<10MB)
   - Verify file type is supported
   - Check uploads/ directory permissions

3. **API Errors**
   - Verify API keys in .env
   - Check internet connection
   - Monitor API quota/limits

4. **Import Errors**
   - Install dependencies: `pip install -r requirements.txt`
   - Use virtual environment for isolation

### Debug Mode:
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python3 start_with_api.py
```

## 🔍 Testing Checklist

### ✅ Basic Functionality
- [ ] Application starts without errors
- [ ] Frontend loads at http://localhost:8501
- [ ] Backend API responds at http://localhost:8000
- [ ] Health check passes

### ✅ File Upload
- [ ] Files upload successfully
- [ ] File validation works (size/type)
- [ ] Files appear in sidebar
- [ ] File roles can be changed
- [ ] Files can be deleted

### ✅ Q&A Features
- [ ] Questions receive responses
- [ ] Responses are contextually appropriate
- [ ] Chat history is maintained
- [ ] Source attribution works

### ✅ Document Analysis
- [ ] Documents are processed successfully
- [ ] Analysis results are comprehensive
- [ ] Multiple file types work
- [ ] Processing status is shown

### ✅ Session Management
- [ ] Session IDs are unique
- [ ] Session cleanup works
- [ ] File isolation between sessions
- [ ] Memory usage is reasonable

### ✅ Error Handling
- [ ] Invalid files are rejected
- [ ] API errors are handled gracefully
- [ ] User-friendly error messages
- [ ] System remains stable after errors

## 📈 Performance Expectations

### Mock Mode:
- **Startup**: ~2-3 seconds
- **Q&A Response**: ~100ms
- **Document Processing**: ~200-500ms
- **Memory Usage**: ~50-100MB

### Production Mode:
- **Startup**: ~5-10 seconds
- **Q&A Response**: ~2-5 seconds
- **Document Processing**: ~5-30 seconds (depending on size)
- **Memory Usage**: ~100-300MB

## 🎯 Success Criteria

### ✅ Must Have:
- All test scenarios pass
- No critical errors or crashes
- Reasonable response times
- User-friendly interface

### ⭐ Nice to Have:
- Sub-second response times for Q&A
- Detailed document insights
- Smooth user experience
- Professional presentation

---

**Ready to test? Run `python3 start_with_api.py` and visit http://localhost:8501** 🚀