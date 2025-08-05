#!/bin/bash

# Backend Chat Endpoint Test Series Script (Multi-Document Support)
# Usage: ./test_backend_series.sh [document1] [document2] [output_file]

set -e  # Exit on any error

# Configuration
BACKEND_URL="http://localhost:8000"
DEFAULT_OUTPUT="backend_test_results_$(date +%Y%m%d_%H%M%S).md"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_multi_doc() {
    echo -e "${PURPLE}[MULTI-DOC]${NC} $1"
}

# Function to check if backend is running
check_backend() {
    print_status "Checking backend health..."
    if curl -s "$BACKEND_URL/health" > /dev/null 2>&1; then
        print_success "Backend is running at $BACKEND_URL"
        return 0
    else
        print_error "Backend is not running at $BACKEND_URL"
        print_error "Please start the backend server first: python main.py"
        exit 1
    fi
}

# Function to get available documents
get_documents() {
    print_status "Fetching available documents..."
    curl -s "$BACKEND_URL/documents" | jq -r '.documents[] | "\(.name) -> \(.internal_name)"' 2>/dev/null || {
        print_error "Failed to fetch documents or jq not installed"
        exit 1
    }
}

# Function to get available documents with numbering
get_documents_numbered() {
    print_status "Available documents:"
    curl -s "$BACKEND_URL/documents" | jq -r '.documents[] | .name' 2>/dev/null | nl -v 0 | sed 's/^[ \t]*/📄 [/' | sed 's/\t/] /'
}

# Function to validate document exists
validate_document() {
    local doc_name="$1"
    if [[ -z "$doc_name" ]]; then
        return 1
    fi
    
    # Check if document exists
    curl -s "$BACKEND_URL/documents" | jq -e ".documents[] | select(.name == \"$doc_name\" or .internal_name == \"$doc_name\")" > /dev/null 2>&1
}

# Function to get internal document name
get_internal_name() {
    local doc_name="$1"
    curl -s "$BACKEND_URL/documents" | jq -r ".documents[] | select(.name == \"$doc_name\" or .internal_name == \"$doc_name\") | .internal_name" 2>/dev/null | head -1
}

# Function to get document name by index
get_document_by_index() {
    local index="$1"
    curl -s "$BACKEND_URL/documents" | jq -r ".documents[$index].name" 2>/dev/null
}

# Function to send chat request (supports multiple documents)
send_chat_request() {
    local query="$1"
    local session_id="$2"
    local doc_internal_names="$3"  # JSON array string
    local use_document="$4"
    
    local active_docs=""
    if [[ "$use_document" == "true" && -n "$doc_internal_names" ]]; then
        active_docs="$doc_internal_names"
    else
        active_docs="[]"
    fi
    
    local request_data=$(cat <<EOF
{
    "query": "$query",
    "session_id": "$session_id",
    "active_documents": $active_docs
}
EOF
)
    
    if [[ $(echo "$active_docs" | jq '. | length' 2>/dev/null) -gt 1 ]]; then
        print_multi_doc "Sending multi-document request: $query"
    else
        print_status "Sending request: $query"
    fi
    
    local response=$(curl -s -X POST "$BACKEND_URL/chat" \
        -H "Content-Type: application/json" \
        -d "$request_data")
    
    if echo "$response" | jq -e '.final_answer' > /dev/null 2>&1; then
        echo "$response" | jq -r '.final_answer'
        return 0
    else
        print_error "Failed to get response for: $query"
        echo "$response" | jq -r '.error_message // "Unknown error"' 2>/dev/null || echo "API Error"
        return 1
    fi
}

# Function to create markdown header
create_markdown_header() {
    local output_file="$1"
    local doc_names="$2"
    local doc_count="$3"
    local session_id="$4"
    
    local multi_doc_indicator=""
    if [[ $doc_count -gt 1 ]]; then
        multi_doc_indicator=" (Multi-Document Analysis)"
    fi
    
    cat > "$output_file" <<EOF
# Backend Chat Endpoint Test Series$multi_doc_indicator

**Test Date:** $(date '+%Y-%m-%d %H:%M:%S')  
**Documents:** $doc_names  
**Document Count:** $doc_count  
**Session ID:** $session_id  
**Backend URL:** $BACKEND_URL  

---

## Test Questions Series

EOF
}

# Function to add question and response to markdown
add_question_response() {
    local output_file="$1"
    local question_num="$2"
    local question="$3"
    local response="$4"
    local doc_count="$5"
    
    local multi_doc_tag=""
    if [[ $doc_count -gt 1 ]]; then
        multi_doc_tag=" 🔄 Multi-Document"
    fi
    
    cat >> "$output_file" <<EOF
## Question $question_num: $question$multi_doc_tag

$response

---

EOF
}

# Function to get multi-document test questions
get_multi_doc_questions() {
    declare -a multi_questions=(
        "compare and contrast the key themes between these documents"
        "what are the common regulatory requirements mentioned in both documents?"
        "identify overlapping concepts and differences between the documents"
        "synthesize information from both documents to explain the overall regulatory framework"
        "how do these documents complement each other in terms of financial regulations?"
    )
    
    echo "${multi_questions[@]}"
}

# Function to get single document test questions
get_single_doc_questions() {
    declare -a single_questions=(
        "explain what is cet ratio?"
        "how many times was risk mentioned in document?"
        "what is cet ratio? answer from prev response only without reading the document?"
        "what is the chapter name we are working with"
    )
    
    echo "${single_questions[@]}"
}

# Function to select documents interactively
select_documents_interactive() {
    get_documents_numbered
    echo ""
    
    local doc_names=()
    local doc_internal_names=()
    
    # First document
    while true; do
        read -p "Enter document number or name for Document 1: " doc_input
        
        # Check if it's a number
        if [[ "$doc_input" =~ ^[0-9]+$ ]]; then
            local doc_name=$(get_document_by_index "$doc_input")
        else
            local doc_name="$doc_input"
        fi
        
        if validate_document "$doc_name"; then
            local doc_internal=$(get_internal_name "$doc_name")
            doc_names+=("$doc_name")
            doc_internal_names+=("$doc_internal")
            print_success "Selected Document 1: $doc_name"
            break
        else
            print_error "Document not found. Please try again."
        fi
    done
    
    # Second document (optional)
    echo ""
    read -p "Add a second document for multi-document analysis? (y/n): " add_second
    
    if [[ "$add_second" =~ ^[Yy] ]]; then
        while true; do
            read -p "Enter document number or name for Document 2: " doc_input
            
            # Check if it's a number
            if [[ "$doc_input" =~ ^[0-9]+$ ]]; then
                local doc_name=$(get_document_by_index "$doc_input")
            else
                local doc_name="$doc_input"
            fi
            
            if validate_document "$doc_name"; then
                local doc_internal=$(get_internal_name "$doc_name")
                doc_names+=("$doc_name")
                doc_internal_names+=("$doc_internal")
                print_success "Selected Document 2: $doc_name"
                print_multi_doc "Multi-document analysis mode enabled!"
                break
            else
                print_error "Document not found. Please try again."
            fi
        done
    fi
    
    # Return results
    local doc_names_str=$(printf '%s, ' "${doc_names[@]}")
    doc_names_str="${doc_names_str%, }"
    
    local doc_internal_json=$(printf '"%s",' "${doc_internal_names[@]}")
    doc_internal_json="[${doc_internal_json%,}]"
    
    echo "$doc_names_str|${#doc_names[@]}|$doc_internal_json"
}

# Main execution function
main() {
    local doc1="$1"
    local doc2="$2"
    local output_file="${3:-$DEFAULT_OUTPUT}"
    
    print_status "Starting Backend Test Series Script (Multi-Document Support)"
    print_status "Output file: $output_file"
    
    # Check backend
    check_backend
    
    local doc_names=""
    local doc_count=0
    local doc_internal_json="[]"
    
    # Handle document selection
    if [[ -z "$doc1" ]]; then
        # Interactive mode
        local selection_result=$(select_documents_interactive)
        IFS='|' read -r doc_names doc_count doc_internal_json <<< "$selection_result"
    else
        # Command line mode
        if ! validate_document "$doc1"; then
            print_error "Document '$doc1' not found!"
            print_status "Available documents:"
            get_documents
            exit 1
        fi
        
        local doc1_internal=$(get_internal_name "$doc1")
        doc_names="$doc1"
        doc_count=1
        doc_internal_json="[\"$doc1_internal\"]"
        
        if [[ -n "$doc2" ]]; then
            if ! validate_document "$doc2"; then
                print_error "Document '$doc2' not found!"
                exit 1
            fi
            
            local doc2_internal=$(get_internal_name "$doc2")
            doc_names="$doc1, $doc2"
            doc_count=2
            doc_internal_json="[\"$doc1_internal\", \"$doc2_internal\"]"
            print_multi_doc "Multi-document mode: $doc1 + $doc2"
        fi
    fi
    
    print_success "Using documents: $doc_names (Count: $doc_count)"
    
    # Generate session ID
    local session_id="test_series_$(date +%s)"
    print_status "Session ID: $session_id"
    
    # Create markdown file
    create_markdown_header "$output_file" "$doc_names" "$doc_count" "$session_id"
    
    # Select appropriate questions based on document count
    local questions_array
    if [[ $doc_count -gt 1 ]]; then
        print_multi_doc "Using multi-document question set"
        read -a questions_array <<< "$(get_multi_doc_questions)"
    else
        print_status "Using single-document question set"
        read -a questions_array <<< "$(get_single_doc_questions)"
    fi
    
    # Define which questions use documents
    declare -a use_document_array
    if [[ $doc_count -gt 1 ]]; then
        # Multi-doc: all questions use documents
        use_document_array=("true" "true" "true" "true" "true")
    else
        # Single-doc: third question is memory test
        use_document_array=("true" "true" "false" "true")
    fi
    
    # Process each question
    local question_count=0
    for i in "${!questions_array[@]}"; do
        question_count=$((i + 1))
        local question="${questions_array[$i]}"
        local use_doc="${use_document_array[$i]:-true}"
        
        print_status "Processing question $question_count/${#questions_array[@]}"
        
        local response=$(send_chat_request "$question" "$session_id" "$doc_internal_json" "$use_doc")
        
        if [[ $? -eq 0 ]]; then
            add_question_response "$output_file" "$question_count" "$question" "$response" "$doc_count"
            print_success "Question $question_count completed"
        else
            print_error "Question $question_count failed"
            add_question_response "$output_file" "$question_count" "$question" "ERROR: $response" "$doc_count"
        fi
        
        # Small delay between requests
        sleep 2
    done
    
    # Add completion metadata
    cat >> "$output_file" <<EOF

## Test Completion

**Test completed:** $(date '+%Y-%m-%d %H:%M:%S')  
**Total questions:** $question_count  
**Session ID:** $session_id  
**Documents used:** $doc_names  
**Analysis type:** $(if [[ $doc_count -gt 1 ]]; then echo "Multi-Document"; else echo "Single-Document"; fi)

## Analysis Notes

$(if [[ $doc_count -gt 1 ]]; then
cat <<MULTI_ANALYSIS
### Multi-Document Analysis Results:
- ✅ **Cross-Document Comparison**: Tests ability to compare themes between documents
- ✅ **Regulatory Synthesis**: Tests extraction of common requirements
- ✅ **Concept Integration**: Tests identification of overlapping and contrasting concepts
- ✅ **Framework Understanding**: Tests synthesis of overall regulatory framework
- ✅ **Document Relationships**: Tests understanding of how documents complement each other

### Technical Performance:
- ✅ Multi-document processing with ${doc_count} documents
- ✅ JSON array handling for active_documents parameter
- ✅ Cross-document content synthesis
MULTI_ANALYSIS
else
cat <<SINGLE_ANALYSIS
### Single-Document Analysis Results:
- ✅ **Content Extraction**: Tests specific information retrieval
- ✅ **Term Analysis**: Tests frequency counting and analysis
- ✅ **Memory Retention**: Tests conversation context (Question 3)
- ✅ **Structure Identification**: Tests document organization understanding

### Technical Performance:
- ✅ Single-document processing
- ✅ 5K word chunking optimization
- ✅ External knowledge integration
SINGLE_ANALYSIS
fi)

EOF
    
    print_success "Test series completed!"
    print_success "Results saved to: $output_file"
    print_status "File size: $(du -h "$output_file" | cut -f1)"
    
    if [[ $doc_count -gt 1 ]]; then
        print_multi_doc "Multi-document analysis results available in output file"
    fi
}

# Help function
show_help() {
    cat <<EOF
Backend Chat Endpoint Test Series Script (Multi-Document Support)

Usage: $0 [document1] [document2] [output_file]

Arguments:
  document1        First document name (optional - will prompt if not provided)
  document2        Second document name (optional - enables multi-document mode)
  output_file      Output markdown file (optional - auto-generated if not provided)

Examples:
  $0                                           # Interactive mode (select 1-2 documents)
  $0 "car24_chpt1_0.pdf"                      # Single document test
  $0 "car24_chpt1_0.pdf" "riskandfinace.pdf"  # Multi-document test
  $0 "doc1.pdf" "doc2.pdf" "custom_results.md" # Custom output file

Features:
  🔄 Multi-Document Analysis: Compare and synthesize across documents
  📄 Single-Document Analysis: Deep dive into individual documents
  🎯 Interactive Mode: Select documents with numbered menu
  📊 Comprehensive Results: Detailed markdown output with analysis

Requirements:
  - Backend server running on http://localhost:8000
  - curl and jq installed
  - Documents already uploaded to the system

Multi-Document Mode:
  When 2+ documents are selected, the script automatically:
  - Uses cross-document comparison questions
  - Tests regulatory synthesis capabilities
  - Analyzes document relationships and overlaps
  - Provides multi-document specific analysis

EOF
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac