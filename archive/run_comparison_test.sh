#!/bin/bash

# Multi-Document Comparison Test
# Tests: car24_chpt1_0.pdf + car24_chpt7.pdf

BACKEND_URL="http://localhost:8000"
SESSION_ID="comparison_test_$(date +%s)"

echo "🔍 MULTI-DOCUMENT COMPARISON TEST"
echo "=================================="
echo "Session: $SESSION_ID"
echo "Time: $(date)"
echo ""

# Check backend health
echo "🔍 Checking backend..."
if ! curl -s "$BACKEND_URL/health" > /dev/null; then
    echo "❌ Backend not running! Start with: python main.py"
    exit 1
fi
echo "✅ Backend is running"

# Get documents and find car24 files
echo ""
echo "📚 Getting available documents..."
DOCS_JSON=$(curl -s "$BACKEND_URL/documents")

# Find car24 documents
CHAP1_INTERNAL=$(echo "$DOCS_JSON" | jq -r '.documents[] | select(.name | contains("car24_chpt1_0.pdf")) | .internal_name' | head -1)
CHAP7_INTERNAL=$(echo "$DOCS_JSON" | jq -r '.documents[] | select(.name | contains("car24_chpt7.pdf")) | .internal_name' | head -1)

if [[ -z "$CHAP1_INTERNAL" || -z "$CHAP7_INTERNAL" ]]; then
    echo "❌ Could not find both car24 documents"
    echo "Available documents:"
    echo "$DOCS_JSON" | jq -r '.documents[].name'
    exit 1
fi

echo "✅ Found documents:"
echo "   Chapter 1: $CHAP1_INTERNAL"
echo "   Chapter 7: $CHAP7_INTERNAL"

# Question 1: Comparison analysis
echo ""
echo "📝 QUESTION 1: Compare and contrast the policy, requirements and procedures"
echo "============================================================================"

QUESTION1="compare and contrast the policy, requirements and procedures mentioned in the two chapters?"

REQUEST1='{
    "query": "'$QUESTION1'",
    "session_id": "'$SESSION_ID'",
    "active_documents": ["'$CHAP1_INTERNAL'", "'$CHAP7_INTERNAL'"]
}'

echo "🔄 Sending comparison request..."
RESPONSE1=$(curl -s -X POST "$BACKEND_URL/chat" \
    -H "Content-Type: application/json" \
    -d "$REQUEST1")

ANSWER1=$(echo "$RESPONSE1" | jq -r '.final_answer // "Error: No response"')

echo ""
echo "📄 RESPONSE 1:"
echo "$ANSWER1"

# Save to file
OUTPUT1="comparison_q1_$(date +%Y%m%d_%H%M%S).txt"
cat > "$OUTPUT1" << EOF
MULTI-DOCUMENT COMPARISON TEST - QUESTION 1
===========================================
Session: $SESSION_ID
Time: $(date)
Documents: car24_chpt1_0.pdf + car24_chpt7.pdf
Question: $QUESTION1

Response:
$ANSWER1
EOF

echo ""
echo "💾 Response 1 saved to: $OUTPUT1"

# Wait before follow-up
echo ""
echo "⏱️  Waiting 3 seconds before follow-up question..."
sleep 3

# Question 2: Follow-up bullet list
echo ""
echo "📝 QUESTION 2: List them all down in concise bullet form"
echo "======================================================="

QUESTION2="list them all down in concise bullet from above response"

REQUEST2='{
    "query": "'$QUESTION2'",
    "session_id": "'$SESSION_ID'",
    "active_documents": ["'$CHAP1_INTERNAL'", "'$CHAP7_INTERNAL'"]
}'

echo "🔄 Sending follow-up request..."
RESPONSE2=$(curl -s -X POST "$BACKEND_URL/chat" \
    -H "Content-Type: application/json" \
    -d "$REQUEST2")

ANSWER2=$(echo "$RESPONSE2" | jq -r '.final_answer // "Error: No response"')

echo ""
echo "📄 RESPONSE 2:"
echo "$ANSWER2"

# Save to file
OUTPUT2="comparison_q2_$(date +%Y%m%d_%H%M%S).txt"
cat > "$OUTPUT2" << EOF
MULTI-DOCUMENT COMPARISON TEST - QUESTION 2
===========================================
Session: $SESSION_ID
Time: $(date)
Documents: car24_chpt1_0.pdf + car24_chpt7.pdf
Question: $QUESTION2

Response:
$ANSWER2
EOF

echo ""
echo "💾 Response 2 saved to: $OUTPUT2"

# Analysis summary
echo ""
echo "🎯 TEST COMPLETE - ANALYSIS SUMMARY"
echo "==================================="
echo "Session: $SESSION_ID"
echo "Documents tested: car24_chpt1_0.pdf + car24_chpt7.pdf"
echo "Questions: 2 (comparison + follow-up)"
echo "Output files: $OUTPUT1, $OUTPUT2"
echo ""
echo "📊 Key things to check in responses:"
echo "   ✅ Did Q1 cover BOTH chapters (not just one)?"
echo "   ✅ Did Q1 show real comparison/contrast?"
echo "   ✅ Did Q2 properly extract bullets from Q1?"
echo "   ✅ Did Q2 maintain session context?"
echo ""
echo "Check the output files for detailed analysis!"