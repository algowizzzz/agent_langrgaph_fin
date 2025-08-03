#!/bin/bash

# Simple Backend Test Script (Multi-Document Support)
# Usage: ./simple_backend_test.sh

# Configuration
BACKEND_URL="http://localhost:8000"
SESSION_ID="test_$(date +%s)"
OUTPUT_FILE="test_results_$(date +%Y%m%d_%H%M%S).md"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting Simple Backend Test (Multi-Document Support)${NC}"
echo "Session ID: $SESSION_ID"
echo "Output: $OUTPUT_FILE"
echo ""

# Check backend
echo -e "${BLUE}Checking backend...${NC}"
if ! curl -s "$BACKEND_URL/health" > /dev/null; then
    echo -e "${RED}❌ Backend not running! Start with: python main.py${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Backend is running${NC}"

# Get documents with numbers
echo -e "${BLUE}Available documents:${NC}"
DOCS=$(curl -s "$BACKEND_URL/documents" | jq -r '.documents[] | .name' 2>/dev/null)
if [[ -z "$DOCS" ]]; then
    echo -e "${RED}❌ Failed to get documents${NC}"
    exit 1
fi

echo "$DOCS" | nl -v 0 | sed 's/^[ \t]*/📄 [/' | sed 's/\t/] /'

echo ""

# Select first document
while true; do
    read -p "Enter document number or name for Document 1: " DOC_INPUT_1
    
    # Check if it's a number
    if [[ "$DOC_INPUT_1" =~ ^[0-9]+$ ]]; then
        DOC_NAME_1=$(echo "$DOCS" | sed -n "$((DOC_INPUT_1 + 1))p")
    else
        DOC_NAME_1="$DOC_INPUT_1"
    fi
    
    # Get internal name
    DOC_INTERNAL_1=$(curl -s "$BACKEND_URL/documents" | jq -r ".documents[] | select(.name == \"$DOC_NAME_1\") | .internal_name" 2>/dev/null)
    
    if [[ -n "$DOC_INTERNAL_1" ]]; then
        echo -e "${GREEN}✅ Selected Document 1: $DOC_NAME_1${NC}"
        break
    else
        echo -e "${RED}❌ Document not found! Please try again.${NC}"
    fi
done

# Select second document (optional)
echo ""
read -p "Add a second document for multi-document analysis? (y/n): " ADD_SECOND

MULTI_DOC=false
DOC_NAMES="$DOC_NAME_1"
ACTIVE_DOCS="[\"$DOC_INTERNAL_1\"]"

if [[ "$ADD_SECOND" =~ ^[Yy] ]]; then
    while true; do
        read -p "Enter document number or name for Document 2: " DOC_INPUT_2
        
        # Check if it's a number
        if [[ "$DOC_INPUT_2" =~ ^[0-9]+$ ]]; then
            DOC_NAME_2=$(echo "$DOCS" | sed -n "$((DOC_INPUT_2 + 1))p")
        else
            DOC_NAME_2="$DOC_INPUT_2"
        fi
        
        # Get internal name
        DOC_INTERNAL_2=$(curl -s "$BACKEND_URL/documents" | jq -r ".documents[] | select(.name == \"$DOC_NAME_2\") | .internal_name" 2>/dev/null)
        
        if [[ -n "$DOC_INTERNAL_2" ]]; then
            echo -e "${GREEN}✅ Selected Document 2: $DOC_NAME_2${NC}"
            echo -e "${PURPLE}🔄 Multi-document analysis mode enabled!${NC}"
            MULTI_DOC=true
            DOC_NAMES="$DOC_NAME_1, $DOC_NAME_2"
            ACTIVE_DOCS="[\"$DOC_INTERNAL_1\", \"$DOC_INTERNAL_2\"]"
            break
        else
            echo -e "${RED}❌ Document not found! Please try again.${NC}"
        fi
    done
fi

# Create markdown file
ANALYSIS_TYPE="Single-Document"
if [[ "$MULTI_DOC" == "true" ]]; then
    ANALYSIS_TYPE="Multi-Document"
fi

cat > "$OUTPUT_FILE" <<EOF
# Simple Backend Test Results ($ANALYSIS_TYPE Analysis)

**Date:** $(date)
**Documents:** $DOC_NAMES
**Session:** $SESSION_ID
**Analysis Type:** $ANALYSIS_TYPE

---

EOF

# Define questions based on mode
if [[ "$MULTI_DOC" == "true" ]]; then
    # Multi-document questions
    declare -a QUESTIONS=(
        "compare the key themes between these documents"
        "what are the common topics mentioned in both documents?"
        "how do these documents complement each other?"
    )
else
    # Single document questions
    declare -a QUESTIONS=(
        "explain what is cet ratio?"
        "how many times was risk mentioned in document?"
        "what is the chapter name we are working with?"
    )
fi

# Run tests
for i in "${!QUESTIONS[@]}"; do
    QUESTION="${QUESTIONS[$i]}"
    
    if [[ "$MULTI_DOC" == "true" ]]; then
        echo -e "${PURPLE}🔄 Multi-Doc Question $((i+1)): $QUESTION${NC}"
    else
        echo -e "${BLUE}📝 Question $((i+1)): $QUESTION${NC}"
    fi
    
    RESPONSE=$(curl -s -X POST "$BACKEND_URL/chat" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"$QUESTION\", \"session_id\": \"$SESSION_ID\", \"active_documents\": $ACTIVE_DOCS}" \
        | jq -r '.final_answer // "Error: No response"')
    
    QUESTION_LABEL="Question $((i+1)): $QUESTION"
    if [[ "$MULTI_DOC" == "true" ]]; then
        QUESTION_LABEL="$QUESTION_LABEL 🔄 Multi-Document"
    fi
    
    cat >> "$OUTPUT_FILE" <<EOF
## $QUESTION_LABEL

$RESPONSE

---

EOF
    
    echo -e "${GREEN}✅ Completed${NC}"
    sleep 2
done

# Add completion summary
cat >> "$OUTPUT_FILE" <<EOF

## Test Summary

**Analysis Type:** $ANALYSIS_TYPE
**Documents Analyzed:** $DOC_NAMES
**Questions Asked:** ${#QUESTIONS[@]}
**Session ID:** $SESSION_ID

$(if [[ "$MULTI_DOC" == "true" ]]; then
cat <<MULTI_SUMMARY
### Multi-Document Analysis Features:
- ✅ Cross-document theme comparison
- ✅ Common topic identification  
- ✅ Document relationship analysis
- ✅ Synthetic content generation from multiple sources
MULTI_SUMMARY
else
cat <<SINGLE_SUMMARY
### Single-Document Analysis Features:
- ✅ Specific information extraction
- ✅ Term frequency analysis
- ✅ Document structure identification
SINGLE_SUMMARY
fi)

EOF

echo ""
echo -e "${GREEN}🎉 Test completed!${NC}"
echo -e "${BLUE}📄 Results saved to: $OUTPUT_FILE${NC}"
echo -e "${BLUE}📊 File size: $(du -h "$OUTPUT_FILE" | cut -f1)${NC}"

if [[ "$MULTI_DOC" == "true" ]]; then
    echo -e "${PURPLE}🔄 Multi-document analysis results available in output file${NC}"
fi