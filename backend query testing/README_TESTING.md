# Backend Query Testing Suite

Comprehensive automated testing scripts for the AI Document Agent backend API with **multi-document analysis support**.

## 📁 Organization

All testing scripts are organized in the `backend query testing/` folder:
```
backend query testing/
├── test_backend_series.sh      # Full-featured test script (multi-doc support)
├── simple_backend_test.sh      # Quick & easy testing (multi-doc support)
├── test_questions.json         # Question configurations and test suites
└── README_TESTING.md           # This documentation
```

## 🔄 **NEW: Multi-Document Analysis**

Both test scripts now support **multi-document analysis**, allowing you to:
- ✅ **Compare and contrast** themes between documents
- ✅ **Synthesize information** across multiple sources
- ✅ **Identify overlapping concepts** and differences
- ✅ **Extract cross-document insights** and relationships
- ✅ **Test regulatory synthesis** capabilities

## 📋 Available Scripts

### 1. `test_backend_series.sh` - Full-Featured Test Script (Multi-Document)

**Features:**
- ✅ **Interactive document selection** (1-2 documents)
- ✅ **Multi-document question sets** automatically selected
- ✅ **Single vs multi-document modes** with different question types
- ✅ **Numbered document selection** for easier interaction
- ✅ **Comprehensive markdown output** with multi-document analysis
- ✅ **Colored output with progress tracking**
- ✅ **Error handling and validation**

**Usage:**
```bash
# Interactive mode (select 1-2 documents)
./test_backend_series.sh

# Single document mode
./test_backend_series.sh "car24_chpt1_0.pdf"

# Multi-document mode
./test_backend_series.sh "car24_chpt1_0.pdf" "riskandfinace.pdf"

# Custom output file
./test_backend_series.sh "doc1.pdf" "doc2.pdf" "my_results.md"

# Help
./test_backend_series.sh --help
```

### 2. `simple_backend_test.sh` - Quick & Easy (Multi-Document)

**Features:**
- ✅ **Simple interactive prompts** with numbered selection
- ✅ **Optional second document** for multi-document testing
- ✅ **Automatic question set selection** based on document count
- ✅ **Clean markdown output** with analysis type indication
- ✅ **Fast execution** with essential tests

**Usage:**
```bash
./simple_backend_test.sh
# Follow prompts:
# 1. Select first document (number or name)
# 2. Choose whether to add second document
# 3. Let it run automatically
```

### 3. `test_questions.json` - Configuration File

**Features:**
- ✅ **Single-document test suites**: `cet_ratio_analysis`, `comprehensive_analysis`, `memory_test`
- ✅ **Multi-document test suites**: `comparative_analysis`, `regulatory_synthesis`, `cross_document_search`, `scenario_analysis`
- ✅ **Stress testing suites**: `large_document_set`, `performance_testing`
- ✅ **Question categories**: comparison, synthesis, extraction, analysis, application
- ✅ **Recommended document pairs** for optimal testing

## 🚀 Quick Start

### Prerequisites
```bash
# Ensure backend is running
cd /path/to/Agent
python main.py

# Check required tools (install if missing)
which curl jq

# Navigate to testing folder
cd "backend query testing"
```

### Single Document Test
```bash
# Simple test
./simple_backend_test.sh
# Select document: 0 (first document)
# Add second document: n
```

### Multi-Document Test
```bash
# Full test with two documents
./test_backend_series.sh
# Select document 1: 0 (e.g., car24_chpt1_0.pdf)
# Add second document: y
# Select document 2: 1 (e.g., riskandfinace.pdf)
```

## 📊 Question Types by Mode

### Single-Document Questions
- ✅ **Specific information extraction** (e.g., "explain what is CET ratio?")
- ✅ **Term frequency analysis** (e.g., "how many times was risk mentioned?")
- ✅ **Memory retention testing** (follow-up without document access)
- ✅ **Document structure identification** (e.g., "what is the chapter name?")

### Multi-Document Questions
- ✅ **Cross-document comparison** (e.g., "compare key themes between documents")
- ✅ **Common element identification** (e.g., "what regulatory requirements appear in both?")
- ✅ **Relationship analysis** (e.g., "how do these documents complement each other?")
- ✅ **Synthesis testing** (e.g., "synthesize the overall regulatory framework")
- ✅ **Conflict detection** (e.g., "identify any contradictions between documents")

## 📈 Output Files

All scripts generate timestamped markdown files with:
- ✅ **Test metadata** (date, session, documents, analysis type)
- ✅ **Question and response pairs** with multi-document indicators
- ✅ **Completion statistics** and performance metrics
- ✅ **Analysis insights** specific to single vs multi-document modes

**Single-Document Output Structure:**
```markdown
# Backend Test Results (Single-Document Analysis)
**Documents:** car24_chpt1_0.pdf
**Analysis Type:** Single-Document

## Question 1: explain what is cet ratio?
[AI Response...]

## Analysis Notes
### Single-Document Analysis Results:
- ✅ Content Extraction: Tests specific information retrieval
- ✅ Term Analysis: Tests frequency counting
```

**Multi-Document Output Structure:**
```markdown
# Backend Test Results (Multi-Document Analysis)
**Documents:** car24_chpt1_0.pdf, riskandfinace.pdf
**Analysis Type:** Multi-Document

## Question 1: compare key themes between documents 🔄 Multi-Document
[AI Cross-Document Analysis...]

## Analysis Notes
### Multi-Document Analysis Results:
- ✅ Cross-Document Comparison: Tests theme comparison
- ✅ Regulatory Synthesis: Tests requirement extraction
```

## 🔧 Advanced Configuration

### Custom Question Sets

Edit `test_questions.json` to add custom test suites:

```json
{
  "test_suites": {
    "multi_document": {
      "your_custom_test": {
        "description": "Your custom multi-document test",
        "document_count": 2,
        "questions": [
          {
            "query": "your custom comparison question",
            "use_document": true,
            "description": "what this tests"
          }
        ]
      }
    }
  }
}
```

### Recommended Document Combinations

For optimal multi-document testing, use these combinations:

1. **Regulatory + Risk Management**:
   - `car24_chpt1_0.pdf` + `riskandfinace.pdf`
   - Tests regulatory synthesis and risk analysis

2. **Policy + Implementation**:
   - Policy document + Implementation guide
   - Tests practical application scenarios

3. **Chapter Sequences**:
   - `car24_chpt1_0.pdf` + `car24_chpt7.pdf`
   - Tests progressive regulatory concepts

## 🐛 Troubleshooting

### Backend Issues
```bash
# Backend not running
curl -s http://localhost:8000/health
# Should return: {"status":"healthy","timestamp":"..."}

# If not running, start backend:
cd /path/to/Agent
python main.py
```

### Document Selection Issues
```bash
# Check available documents
curl -s http://localhost:8000/documents | jq '.documents[].name'

# If no documents, upload some first through the frontend
```

### Multi-Document Not Working
```bash
# Verify documents exist
curl -s http://localhost:8000/documents | jq '.documents | length'
# Should show > 1 for multi-document testing

# Check if both documents are accessible
curl -s http://localhost:8000/documents | jq '.documents[] | select(.name == "your_doc_name")'
```

### Tool Dependencies
```bash
# Install missing tools
# macOS:
brew install jq curl

# Ubuntu/Debian:
sudo apt-get install jq curl

# Make scripts executable:
chmod +x *.sh
```

## 📊 Performance Benchmarks

### Single-Document Performance
- ✅ **Response Time**: 2-6 seconds per question
- ✅ **Chunk Processing**: 5K word chunks (typically 4 chunks for OSFI docs)
- ✅ **Success Rate**: 100% for document-based queries
- ⚠️ **Memory Retention**: Limited for follow-up questions

### Multi-Document Performance
- ✅ **Response Time**: 4-10 seconds per question (cross-document analysis)
- ✅ **Document Handling**: Simultaneous processing of 2+ documents
- ✅ **Synthesis Quality**: High-quality cross-document insights
- ✅ **Comparison Accuracy**: Reliable theme and concept comparison

## 🔄 Continuous Testing

### Daily Testing Script
```bash
#!/bin/bash
# daily_test.sh
cd "backend query testing"
./simple_backend_test.sh
# Add to crontab: 0 9 * * * /path/to/daily_test.sh
```

### Integration Testing
```bash
# Test both single and multi-document modes
./test_backend_series.sh "doc1.pdf" "" "single_test.md"
./test_backend_series.sh "doc1.pdf" "doc2.pdf" "multi_test.md"
```

## 🎯 Best Practices

### Document Selection
1. **Choose complementary documents** for multi-document testing
2. **Use documents with overlapping themes** for better synthesis testing
3. **Test with different document types** (PDF, TXT, CSV)
4. **Ensure documents are properly uploaded** before testing

### Question Design
1. **Single-document**: Focus on extraction, analysis, memory
2. **Multi-document**: Focus on comparison, synthesis, relationships
3. **Include memory tests** to check conversation retention
4. **Vary question complexity** from simple to complex analysis

### Results Analysis
1. **Compare single vs multi-document** performance
2. **Monitor response times** for performance regression
3. **Evaluate synthesis quality** in multi-document mode
4. **Track consistency** across similar document pairs

## 📁 File Management

### Automatic Timestamping
All output files include timestamps:
- `test_results_20250802_1122.md`
- `backend_test_results_20250802_1122.md`

### Result Organization
```bash
# Create results directory
mkdir -p results

# Move old results
mv *_results_*.md results/

# Archive monthly
tar -czf "results_$(date +%Y%m).tar.gz" results/
```

---

*For questions or issues, check the script help commands (`--help`) or examine the source code for detailed implementation.*

## 🎉 Quick Examples

### Example 1: Single Document Test
```bash
./simple_backend_test.sh
# Select: 0 (car24_chpt1_0.pdf)
# Add second: n
# Result: Focused analysis of OSFI Chapter 1
```

### Example 2: Multi-Document Comparison
```bash
./test_backend_series.sh
# Select doc 1: 0 (car24_chpt1_0.pdf)
# Add second: y
# Select doc 2: 1 (riskandfinace.pdf)
# Result: Comparative analysis of regulatory framework vs risk management
```

### Example 3: Custom Multi-Document Test
```bash
./test_backend_series.sh "policy_doc.pdf" "implementation_guide.pdf" "policy_analysis.md"
# Result: Analysis of how policy and implementation relate
```