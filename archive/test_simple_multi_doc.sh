#!/bin/bash

# Test with simple text documents to isolate multi-document issues

BACKEND_URL="http://localhost:8000"
SESSION_ID="simple_multi_test_$(date +%s)"

echo "🔍 SIMPLE MULTI-DOCUMENT TEST"
echo "=============================="
echo "Session: $SESSION_ID"
echo ""

# Check backend
echo "🔍 Checking backend..."
if ! curl -s "$BACKEND_URL/health" > /dev/null; then
    echo "❌ Backend not running!"
    exit 1
fi
echo "✅ Backend is running"

# Upload simple test documents
echo ""
echo "📤 Uploading test documents..."

# Upload doc 1
DOC1_RESPONSE=$(curl -s -X POST "$BACKEND_URL/upload?session_id=$SESSION_ID" \
    -F "file=@test_doc1.txt")

DOC1_STATUS=$(echo "$DOC1_RESPONSE" | jq -r '.status // "error"')
if [[ "$DOC1_STATUS" == "success" ]]; then
    echo "✅ Uploaded test_doc1.txt"
else
    echo "❌ Failed to upload test_doc1.txt: $DOC1_RESPONSE"
    exit 1
fi

# Upload doc 2
DOC2_RESPONSE=$(curl -s -X POST "$BACKEND_URL/upload?session_id=$SESSION_ID" \
    -F "file=@test_doc2.txt")

DOC2_STATUS=$(echo "$DOC2_RESPONSE" | jq -r '.status // "error"')
if [[ "$DOC2_STATUS" == "success" ]]; then
    echo "✅ Uploaded test_doc2.txt"
else
    echo "❌ Failed to upload test_doc2.txt: $DOC2_RESPONSE"
    exit 1
fi

# Get documents to find internal names
echo ""
echo "📚 Finding uploaded documents..."
DOCS_JSON=$(curl -s "$BACKEND_URL/documents")

DOC1_INTERNAL=$(echo "$DOCS_JSON" | jq -r '.documents[] | select(.name | contains("test_doc1.txt")) | .internal_name' | head -1)
DOC2_INTERNAL=$(echo "$DOCS_JSON" | jq -r '.documents[] | select(.name | contains("test_doc2.txt")) | .internal_name' | head -1)

if [[ -z "$DOC1_INTERNAL" || -z "$DOC2_INTERNAL" ]]; then
    echo "❌ Could not find uploaded test documents"
    echo "Available documents:"
    echo "$DOCS_JSON" | jq -r '.documents[].name'
    exit 1
fi

echo "✅ Found documents:"
echo "   Doc 1: $DOC1_INTERNAL"
echo "   Doc 2: $DOC2_INTERNAL"

# Test multi-document query
echo ""
echo "📝 Testing multi-document comparison..."

QUESTION="compare the content of both documents and tell me what each one mentions"

REQUEST='{
    "query": "'$QUESTION'",
    "session_id": "'$SESSION_ID'",
    "active_documents": ["'$DOC1_INTERNAL'", "'$DOC2_INTERNAL'"]
}'

echo "🔄 Sending multi-document request..."
echo "Request: $REQUEST"

RESPONSE=$(curl -s -X POST "$BACKEND_URL/chat" \
    -H "Content-Type: application/json" \
    -d "$REQUEST")

ANSWER=$(echo "$RESPONSE" | jq -r '.final_answer // "Error: No response"')

echo ""
echo "📄 RESPONSE:"
echo "$ANSWER"
echo ""

# Save results
OUTPUT_FILE="simple_multi_doc_test_$(date +%Y%m%d_%H%M%S).md"

cat > "$OUTPUT_FILE" <<EOF
# Simple Multi-Document Test Results

**Test Date:** $(date)
**Session:** $SESSION_ID
**Documents:** test_doc1.txt + test_doc2.txt
**Question:** $QUESTION

## Document Contents

**test_doc1.txt:**
$(cat test_doc1.txt)

**test_doc2.txt:**
$(cat test_doc2.txt)

## AI Response

$ANSWER

## Analysis

Check if the AI response mentions BOTH documents:
- ✅ Should mention "Document 1" or "Chapter 1" or "capital requirements"
- ✅ Should mention "Document 2" or "Chapter 7" or "settlement risk"
- ✅ Should show comparison between both documents
- ❌ Should NOT say "information not provided" or "only one document"

EOF

echo "💾 Results saved to: $OUTPUT_FILE"
echo ""
echo "🎯 KEY DIAGNOSTIC QUESTIONS:"
echo "   1. Did the AI see BOTH documents?"
echo "   2. Did it mention content from BOTH files?"
echo "   3. Did it compare them properly?"
echo ""
echo "Check the output file for analysis!"