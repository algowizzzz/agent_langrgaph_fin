# Interactive Agent Tester - Usage Guide

## 🚀 Quick Start

Run the interactive tester:
```bash
python3 interactive_agent_tester.py
```

## 📋 Features

✅ **Document Selection**: Choose from 50+ available documents  
✅ **Custom Queries**: Ask any question you want  
✅ **Follow-up Questions**: Continue conversations in the same session  
✅ **Full Response Capture**: Complete responses saved to markdown  
✅ **Multiple Workflows**: Document Q&A, Multi-Document Analysis, Knowledge Fallback  

## 🔄 How It Works

### 1. Document Selection
The script will show you available documents:
```
📂 Available Documents:
----------------------------------------
 1. riskandfinace.pdf
 2. car24_chpt1_0.pdf  
 3. car24_chpt7.pdf
 4. bmo_quarterly_review.docx
 ...
51. No documents (knowledge base only)
----------------------------------------
```

**Selection Options:**
- `1,3,5` - Select documents 1, 3, and 5
- `2` - Select just document 2  
- `none` - Use knowledge base only
- `1,2,3,4,5` - Select multiple documents for comparison

### 2. Query Input
Enter any question you want to ask:
```
❓ Query: What are the main risk factors mentioned in these documents?
```

### 3. Results & Follow-up
After each query, you can:
- **Ask follow-up** (keeps same documents)
- **New query** with different documents  
- **Generate report** and exit
- **Exit** without saving

### 4. Report Generation
Creates a comprehensive markdown file like:
- `interactive_test_results_20250803_214500.md`

## 💡 Example Usage Scenarios

### Scenario 1: Single Document Analysis
1. Select `2` (one PDF document)
2. Ask: "What are the key financial risks discussed?"
3. Follow up: "What mitigation strategies are recommended?"

### Scenario 2: Multi-Document Comparison  
1. Select `1,3` (two documents)
2. Ask: "Compare the risk assessment approaches in these documents"
3. Follow up: "Which document provides more technical details?"

### Scenario 3: Knowledge Base Testing
1. Select `none` (no documents)
2. Ask: "Explain the Basel III capital requirements"
3. Follow up: "How do these compare to Basel II?"

## 📊 Report Output

The generated report includes:
- **Complete responses** (full text, not previews)
- **Execution details** (tools used, parameters, timing)
- **Workflow classification** (Document Q&A, Multi-Doc, Knowledge Fallback)
- **Performance metrics** (confidence scores, response times)

## 🎯 Best Practices

### Document Selection
- **Single documents**: Best for specific analysis
- **2-3 documents**: Good for comparisons  
- **No documents**: Tests knowledge base capabilities

### Query Writing
- **Be specific**: "What are the liquidity risk factors?" vs "Tell me about risk"
- **Ask follow-ups**: Build on previous responses
- **Test different types**: Analysis, comparison, explanation, summarization

### Session Management
- **Group related queries**: Keep similar topics in one session
- **Use follow-ups**: More efficient than reselecting documents
- **Generate reports**: Save your work frequently

## 🔧 Technical Details

### Session Management
- Each run creates a unique session ID
- Follow-up questions maintain conversation context
- All queries in one session share the same context

### Document Handling
- Automatically detects available documents
- Supports PDF, TXT, CSV, DOCX files
- Uses actual document names from the system

### Output Format
- Markdown format for easy viewing
- Includes execution metadata
- Compatible with the existing test result format

## 🚨 Troubleshooting

### No Documents Found
- Check that documents are uploaded to the system
- Verify `global_uploads/` directory exists
- Use knowledge base mode if no documents available

### Query Errors
- Make sure queries are not empty
- Try simpler questions if complex ones fail
- Use follow-up feature for related questions

### Performance
- Larger documents take longer to process
- Multi-document queries are slower than single documents
- Knowledge base queries are fastest

## 📁 Example Output

Running the script with 3 queries generates a report like:
```
interactive_test_results_20250803_214500.md
├── Test 1: Document Q&A (1,200 chars response)
├── Test 2: Multi-Document Analysis (1,800 chars response)  
└── Test 3: Knowledge Fallback (1,500 chars response)
```

**🎉 Perfect for comprehensive testing and generating detailed documentation of your AI agent's capabilities!**