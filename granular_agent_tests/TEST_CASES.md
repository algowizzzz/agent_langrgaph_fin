# Granular Agent Test Cases

This document outlines the business-critical test cases for the dynamic agent. Each test must be evaluated not just for technical success (i.e., no errors), but for the business value and relevance of its final output.

---

### **Test Case 1: Comprehensive Summarization**

*   **User Query**: `"Summarize the entire document."`
*   **Acceptance Criterion**: The agent must produce a concise, accurate summary that synthesizes all major sections of the document. The output must not be a generic refusal to answer. It must correctly identify and mention the core themes, such as the ethical AI framework, its key principles (fairness, accountability, transparency), and the establishment of a governance board.

---

### **Test Case 2: Section-Specific Summarization**

*   **User Query**: `"Summarize the 'Risk Factors' section only."`
*   **Acceptance Criterion**: The agent must demonstrate its ability to surgically target a specific subsection of the document. The summary must be focused exclusively on the content of the 'Risk Factors' section and must mention "wrong-way risk." It must not include information from other sections.

---

### **Test Case 3: Information Extraction and Formatting**

*   **User Query**: `"Give me all the regulations as a bullet list from this document."`
*   **Acceptance Criterion**: The agent must be able to scan the document for mentions of "regulation" or "regulatory," extract the relevant sentences, and present them in the requested bullet-point format. This tests the agent's ability to follow formatting instructions.

---

### **Test Case 4: Content Analysis and Improvement**

*   **User Query**: `"Identify grammatical issues, list them, and write an improved version of the entire document."`
*   **Acceptance Criterion**: This is a complex, multi-step task. The agent must first identify the grammatical issue mentioned in the text ("The grammar in this section could be improved"). It must then generate a rewritten, grammatically correct version of the document. A simple confirmation is not enough; it must produce the improved content.

---

### **Test Case 5: Deep-Dive Research**

*   **User Query**: `"Do a deep research on everything related to 'wrong-way risk' in the document."`
*   **Acceptance Criterion**: The agent must go beyond a simple search. It should identify the sentence containing "wrong-way risk" and provide a detailed explanation or synthesis of that concept based *only* on the information present in the document. This tests its ability to perform a focused analysis on a specific topic.

---

### **Test Case 6: Keyword Search and Retrieval**

*   **User Query**: `"Search the entire document for the mention of the word 'regulatory'."`
*   **Acceptance Criterion**: The agent must find all instances of the word "regulatory" and present them to the user. The output should be a clear and direct presentation of the search results, not a summary.
