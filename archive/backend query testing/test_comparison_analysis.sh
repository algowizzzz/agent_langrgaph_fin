#!/bin/bash

# Multi-Document Comparison Analysis Test Script
# Tests comparison and contrast analysis between car24_chpt1_0.pdf and car24_chpt7.pdf

set -e  # Exit on any error

# Configuration
BACKEND_URL="http://localhost:8000"
SESSION_ID="comparison_analysis_$(date +%s)"
OUTPUT_FILE="comparison_analysis_results_$(date +%Y%m%d_%H%M%S).md"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${BLUE}🔍 Multi-Document Comparison Analysis Test${NC}"
echo "============================================="
echo "Session: $SESSION_ID"
echo "Output: $OUTPUT_FILE"
echo ""

# Check backend
echo -e "${BLUE}Checking backend health...${NC}"
if ! curl -s "$BACKEND_URL/health" > /dev/null; then
    echo "❌ Backend not running! Start with: python main.py"
    exit 1
fi
echo -e "${GREEN}✅ Backend is running${NC}"

# Get documents and find car24 files
echo ""
echo -e "${BLUE}Finding car24 documents...${NC}"
DOCS_JSON=$(curl -s "$BACKEND_URL/documents")

CHAP1_INTERNAL=$(echo "$DOCS_JSON" | jq -r '.documents[] | select(.name | contains("car24_chpt1_0.pdf")) | .internal_name' | head -1)
CHAP7_INTERNAL=$(echo "$DOCS_JSON" | jq -r '.documents[] | select(.name | contains("car24_chpt7.pdf")) | .internal_name' | head -1)

if [[ -z "$CHAP1_INTERNAL" || -z "$CHAP7_INTERNAL" ]]; then
    echo "❌ Could not find both car24 documents"
    echo "Available documents:"
    echo "$DOCS_JSON" | jq -r '.documents[].name'
    exit 1
fi

echo -e "${GREEN}✅ Found documents:${NC}"
echo "   Chapter 1: $CHAP1_INTERNAL"
echo "   Chapter 7: $CHAP7_INTERNAL"

# Create markdown file header
cat > "$OUTPUT_FILE" <<EOF
# Multi-Document Comparison Analysis Results

**Test Date:** $(date '+%Y-%m-%d %H:%M:%S')  
**Documents:** car24_chpt1_0.pdf + car24_chpt7.pdf  
**Session ID:** $SESSION_ID  
**Analysis Type:** Policy, Requirements & Procedures Comparison  

---

EOF

# Define test questions
declare -a questions=(
    "compare and contrast the policy, requirements and procedures mentioned in the two chapters?"
    "list them all down in concise bullet from above response"
)

declare -a descriptions=(
    "Multi-Document Comparative Analysis"
    "Follow-up Bullet Point Extraction"
)

# Send each question
for i in "${!questions[@]}"; do
    question_num=$((i + 1))
    question="${questions[$i]}"
    description="${descriptions[$i]}"
    
    echo ""
    echo -e "${PURPLE}📝 Question $question_num: $question${NC}"
    echo "Description: $description"
    echo ""
    
    # Prepare request
    request_data=$(cat <<EOF
{
    "query": "$question",
    "session_id": "$SESSION_ID",
    "active_documents": ["$CHAP1_INTERNAL", "$CHAP7_INTERNAL"]
}
EOF
)
    
    echo -e "${BLUE}🔄 Sending multi-document request...${NC}"
    
    # Send request
    response=$(curl -s -X POST "$BACKEND_URL/chat" \
        -H "Content-Type: application/json" \
        -d "$request_data")
    
    if echo "$response" | jq -e '.final_answer' > /dev/null 2>&1; then
        answer=$(echo "$response" | jq -r '.final_answer')
        
        echo -e "${GREEN}✅ Response received (${#answer} chars)${NC}"
        
        # Add to markdown file
        cat >> "$OUTPUT_FILE" <<EOF
## Question $question_num: $question 🔄 Multi-Document

**Description:** $description

**Response:**

$answer

---

EOF
        
        echo "💾 Added to markdown file"
        
    else
        echo "❌ Failed to get response"
        error_msg=$(echo "$response" | jq -r '.error_message // "Unknown error"' 2>/dev/null || echo "API Error")
        
        # Add error to markdown
        cat >> "$OUTPUT_FILE" <<EOF
## Question $question_num: $question 🔄 Multi-Document

**Description:** $description

**Response:**

ERROR: $error_msg

---

EOF
    fi
    
    # Small delay between questions
    if [[ $question_num -lt ${#questions[@]} ]]; then
        echo "⏱️  Waiting 3 seconds before next question..."
        sleep 3
    fi
done

# Add completion metadata
cat >> "$OUTPUT_FILE" <<EOF

## Test Completion Summary

**Test completed:** $(date '+%Y-%m-%d %H:%M:%S')  
**Total questions:** ${#questions[@]}  
**Session ID:** $SESSION_ID  
**Documents analyzed:** car24_chpt1_0.pdf + car24_chpt7.pdf  
**Analysis focus:** Policy, Requirements & Procedures Comparison

## Analysis Objectives

This test evaluated the multi-document system's ability to:

1. **Cross-Document Comparison** - Compare policies and procedures across Chapter 1 and Chapter 7
2. **Requirement Synthesis** - Identify and contrast regulatory requirements between chapters  
3. **Conversational Context** - Maintain session context for follow-up bullet point extraction
4. **Multi-Document Integration** - Demonstrate effective synthesis of content from both documents

## Key Assessment Criteria

- ✅ **Did Q1 analyze BOTH chapters?** (Not just one document)
- ✅ **Did Q1 show real comparison/contrast?** (Differences and similarities)
- ✅ **Did Q1 cover policies, requirements, AND procedures?** (All three categories)
- ✅ **Did Q2 extract bullets from Q1 response?** (Context retention)
- ✅ **Did Q2 maintain conversational flow?** (Session continuity)

EOF

echo ""
echo -e "${GREEN}🎉 Multi-Document Comparison Test Complete!${NC}"
echo "============================================="
echo "Output file: $OUTPUT_FILE"
echo "File size: $(du -h "$OUTPUT_FILE" | cut -f1)"
echo ""
echo -e "${BLUE}📊 Review the markdown file to assess:${NC}"
echo "   • Multi-document integration quality"
echo "   • Comparison and contrast effectiveness"  
echo "   • Session context retention"
echo "   • Policy/requirements/procedures coverage"