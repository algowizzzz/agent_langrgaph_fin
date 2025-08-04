#!/bin/bash

# Demo Multi-Document Testing Script
# Shows the new multi-document capabilities

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🎯 Demo: Multi-Document Backend Testing${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""

# Check if we're in the right directory
if [[ ! -f "test_backend_series.sh" ]]; then
    echo -e "${RED}❌ Please run this from the 'backend query testing' folder${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 This demo will show you:${NC}"
echo "  🔄 Multi-document selection"
echo "  📊 Cross-document analysis questions"
echo "  📝 Comparative analysis results"
echo "  🎯 Single vs multi-document modes"
echo ""

# Check backend
echo -e "${BLUE}🔍 Checking backend status...${NC}"
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${RED}❌ Backend not running! Please start with: python main.py${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Backend is healthy${NC}"
echo ""

# Show available documents
echo -e "${BLUE}📚 Available documents for testing:${NC}"
curl -s http://localhost:8000/documents | jq -r '.documents[] | .name' 2>/dev/null | nl -v 0 | sed 's/^[ \t]*/📄 [/' | sed 's/\t/] /'

DOC_COUNT=$(curl -s http://localhost:8000/documents | jq '.documents | length' 2>/dev/null)
echo ""
echo -e "${BLUE}📊 Total documents available: $DOC_COUNT${NC}"

if [[ $DOC_COUNT -lt 2 ]]; then
    echo -e "${YELLOW}⚠️  You need at least 2 documents for multi-document testing${NC}"
    echo -e "${YELLOW}   Upload more documents through the frontend first${NC}"
    echo ""
fi

echo ""
echo -e "${PURPLE}🚀 Ready to test! Choose your testing mode:${NC}"
echo ""
echo -e "${GREEN}1.${NC} 📄 Single document test (simple_backend_test.sh)"
echo -e "${GREEN}2.${NC} 🔄 Multi-document test (test_backend_series.sh)"
echo -e "${GREEN}3.${NC} 📖 Show help and exit"
echo ""

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo -e "${BLUE}🚀 Starting single document test...${NC}"
        echo -e "${YELLOW}Follow the prompts and select 'n' when asked about adding a second document${NC}"
        echo ""
        sleep 2
        ./simple_backend_test.sh
        ;;
    2)
        echo -e "${PURPLE}🔄 Starting multi-document test...${NC}"
        echo -e "${YELLOW}Follow the prompts and select 'y' when asked about adding a second document${NC}"
        echo ""
        sleep 2
        ./test_backend_series.sh
        ;;
    3)
        echo -e "${BLUE}📖 Help and Usage Examples:${NC}"
        echo ""
        echo -e "${GREEN}Single Document Testing:${NC}"
        echo "  ./simple_backend_test.sh"
        echo "  - Select one document"
        echo "  - Answer 'n' for second document"
        echo "  - Get focused analysis questions"
        echo ""
        echo -e "${PURPLE}Multi-Document Testing:${NC}"
        echo "  ./test_backend_series.sh"
        echo "  - Select first document"
        echo "  - Answer 'y' for second document"
        echo "  - Select second document"
        echo "  - Get cross-document comparison questions"
        echo ""
        echo -e "${YELLOW}Recommended Document Pairs:${NC}"
        echo "  📄 car24_chpt1_0.pdf + riskandfinace.pdf"
        echo "  📄 Any two regulatory documents"
        echo "  📄 Policy + implementation documents"
        echo ""
        echo -e "${BLUE}Advanced Usage:${NC}"
        echo "  ./test_backend_series.sh \"doc1.pdf\" \"doc2.pdf\" \"results.md\""
        echo "  ./simple_backend_test.sh"
        echo ""
        ;;
    *)
        echo -e "${YELLOW}Invalid choice. Run the script again and choose 1, 2, or 3.${NC}"
        ;;
esac

echo ""
echo -e "${BLUE}🎉 Demo complete! Check your results file for detailed analysis.${NC}"
echo -e "${YELLOW}💡 Tip: Try both single and multi-document modes to see the difference!${NC}"