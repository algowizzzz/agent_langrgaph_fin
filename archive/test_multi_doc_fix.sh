#!/bin/bash

# Quick Multi-Document Fix Verification Test
# This test uses very simple documents to verify the fix works

BACKEND_URL="http://localhost:8000"
SESSION_ID="fix_test_$(date +%s)"

echo "🧪 MULTI-DOCUMENT FIX VERIFICATION"
echo "=================================="
echo "Session: $SESSION_ID"
echo ""

# Create simple test documents with clear content
echo "📄 Creating test documents..."
echo "Test Document A: This document discusses FINANCIAL RISK MANAGEMENT strategies." > test_doc_a.txt
echo "Test Document B: This document covers CREDIT RISK ASSESSMENT procedures." > test_doc_b.txt

echo "✅ Created test documents:"
echo "   Doc A: $(cat test_doc_a.txt)"
echo "   Doc B: $(cat test_doc_b.txt)"
echo ""

# Check backend
echo "🔍 Checking backend..."
if ! curl -s "$BACKEND_URL/health" > /dev/null; then
    echo "❌ Backend not running! Please start with:"
    echo "   cd /Users/saadahmed/Desktop/Apps/AWS_Extra"
    echo "   source Agent/venv/bin/activate && cd Agent && python main.py &"
    exit 1
fi
echo "✅ Backend is running"

# Upload documents
echo ""
echo "📤 Uploading test documents..."

DOC_A_RESPONSE=$(curl -s -X POST "$BACKEND_URL/upload?session_id=$SESSION_ID" -F "file=@test_doc_a.txt")
DOC_A_STATUS=$(echo "$DOC_A_RESPONSE" | jq -r '.status // "error"')

if [[ "$DOC_A_STATUS" == "success" ]]; then
    echo "✅ Uploaded test_doc_a.txt"
else
    echo "❌ Failed to upload test_doc_a.txt"
    exit 1
fi

DOC_B_RESPONSE=$(curl -s -X POST "$BACKEND_URL/upload?session_id=$SESSION_ID" -F "file=@test_doc_b.txt")
DOC_B_STATUS=$(echo "$DOC_B_RESPONSE" | jq -r '.status // "error"')

if [[ "$DOC_B_STATUS" == "success" ]]; then
    echo "✅ Uploaded test_doc_b.txt"
else
    echo "❌ Failed to upload test_doc_b.txt"
    exit 1
fi

# Get document internal names
echo ""
echo "📚 Getting document names..."
DOCS_JSON=$(curl -s "$BACKEND_URL/documents")

DOC_A_INTERNAL=$(echo "$DOCS_JSON" | jq -r '.documents[] | select(.name | contains("test_doc_a.txt")) | .internal_name' | head -1)
DOC_B_INTERNAL=$(echo "$DOCS_JSON" | jq -r '.documents[] | select(.name | contains("test_doc_b.txt")) | .internal_name' | head -1)

if [[ -z "$DOC_A_INTERNAL" || -z "$DOC_B_INTERNAL" ]]; then
    echo "❌ Could not find uploaded documents"
    exit 1
fi

echo "✅ Found documents:"
echo "   Doc A: $DOC_A_INTERNAL"
echo "   Doc B: $DOC_B_INTERNAL"

# Test the multi-document comparison
echo ""
echo "🧪 TESTING MULTI-DOCUMENT COMPARISON..."
echo "======================================="

QUESTION="Compare these two documents and tell me what each one discusses"

REQUEST='{
    "query": "'$QUESTION'",
    "session_id": "'$SESSION_ID'",
    "active_documents": ["'$DOC_A_INTERNAL'", "'$DOC_B_INTERNAL'"]
}'

echo "🔄 Sending request..."
echo "Query: $QUESTION"
echo "Documents: [Doc A, Doc B]"
echo ""

RESPONSE=$(curl -s -X POST "$BACKEND_URL/chat" \
    -H "Content-Type: application/json" \
    -d "$REQUEST")

ANSWER=$(echo "$RESPONSE" | jq -r '.final_answer // "Error: No response"')

echo "📄 AI RESPONSE:"
echo "==============="
echo "$ANSWER"
echo ""

# Analysis
echo "🔍 ANALYSIS:"
echo "============"

# Check if response contains content from both documents
if echo "$ANSWER" | grep -qi "financial risk management"; then
    echo "✅ Found content from Document A (financial risk management)"
else
    echo "❌ Missing content from Document A"
fi

if echo "$ANSWER" | grep -qi "credit risk assessment"; then
    echo "✅ Found content from Document B (credit risk assessment)"
else
    echo "❌ Missing content from Document B"
fi

if echo "$ANSWER" | grep -qi "compare\|comparison\|both\|documents"; then
    echo "✅ AI performed comparison"
else
    echo "❌ AI did not perform comparison"
fi

if echo "$ANSWER" | grep -qi "haven't shared\|don't have access\|please provide"; then
    echo "❌ AI still says it doesn't have access to documents (BUG NOT FIXED)"
else
    echo "✅ AI has access to document content (FIX WORKING)"
fi

echo ""
echo "🎯 VERDICT:"
if echo "$ANSWER" | grep -qi "financial risk management" && echo "$ANSWER" | grep -qi "credit risk assessment"; then
    echo "✅ MULTI-DOCUMENT FIX IS WORKING!"
    echo "   AI successfully accessed and compared both documents."
else
    echo "❌ MULTI-DOCUMENT FIX STILL HAS ISSUES"
    echo "   AI did not access full content from both documents."
fi

# Cleanup
rm -f test_doc_a.txt test_doc_b.txt

echo ""
echo "🧹 Test completed and cleaned up."