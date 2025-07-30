# Comprehensive Node-by-Node Testing Plan

This document outlines a detailed testing plan for each critical node within the Q&A and Document Analysis Pods. The objective is to validate the functionality, robustness, and business logic of each component individually.

---

## Part 1: Q&A Pod Testing

### **Node: `generate_without_context`**
**Objective:** To verify that the agent can provide accurate and relevant answers using its general knowledge when no specific BMO context is available.

| Test Case ID | Description | Test Steps | Expected Result |
| :--- | :--- | :--- | :--- |
| **1.1.1** | **Simple Finance Query** | Ask: "What is the difference between debt and equity financing?" | The agent provides a clear, accurate definition of both concepts and highlights their key differences. The source is cited as "General LLM Knowledge". |
| **1.1.2** | **Complex Risk Management Query** | Ask: "Explain the concept of Value at Risk (VaR) and its main limitations in portfolio management." | The agent defines VaR, explains how it's used, and critically discusses at least two major limitations (e.g., assumption of normal distributions, not capturing tail risk). |
| **1.1.3** | **Comparative Financial Analysis Query** | Ask: "Compare and contrast the Capital Asset Pricing Model (CAPM) with the Fama-French Three-Factor Model." | The agent explains the basics of CAPM (market risk) and then describes how the Fama-French model extends it by adding the size (SMB) and value (HML) factors. |

---

## Part 2: Document Analysis Pod Testing

### **Node: `_load_documents`**
**Objective:** To ensure the system can reliably ingest, parse, and chunk various file types and sizes.

| Test Case ID | Description | Test Steps | Expected Result |
| :--- | :--- | :--- | :--- |
| **2.1.1** | **File Type - PDF** | Upload `test_files/bmo_tech_strategy.pdf`. | The file is processed without errors. The logs show the document was successfully loaded and split into text chunks. The reasoning UI shows "Loading Documents" completed. |
| **2.1.2** | **File Type - DOCX** | Upload `test_files/bmo_quarterly_review.docx`. | The file is processed without errors. The logs show the document was successfully loaded and split into text chunks. The reasoning UI shows "Loading Documents" completed. |
| **2.1.3** | **File Type - CSV** | Upload `test_files/quarterly_report.csv`. | The file is processed without errors. The text content of the CSV is correctly extracted into chunks. The reasoning UI shows "Loading Documents" completed. |
| **2.1.4** | **File Type - XLSX** | Upload `test_files/bmo_business_data.xlsx`. | The file is processed without errors. The text content from the Excel sheet is correctly extracted into chunks. The reasoning UI shows "Loading Documents" completed. |
| **2.1.5** | **File Size - Large** | Upload a valid PDF or DOCX file that is approximately 5MB in size. | The file is processed successfully within a reasonable timeframe (e.g., under 30 seconds). |
| **2.1.6** | **File Integrity - Corrupted** | Upload a corrupted or zero-byte file. | The system gracefully handles the error, does not crash, and presents a user-friendly error message like "The uploaded file appears to be corrupted or empty." |

### **Node: `_planner_node`**
**Objective:** To verify that the Planner can generate appropriate and effective analysis prompts based on different user instructions.

| Test Case ID | Description | Test Steps | Expected Result |
| :--- | :--- | :--- | :--- |
| **2.2.1** | **Instruction - Simple Summarization** | Upload a document and ask: "Give me a quick summary of this." | The logs should show that the Planner generated an `initial_prompt` focused on high-level summarization and a `refine_prompt` designed to build upon an existing summary. |
| **2.2.2** | **Instruction - Specific Extraction** | Upload a document and ask: "Extract all mentions of revenue, targets, and strategic goals from this report." | The generated prompts should be highly specific, instructing the AI to look for and list keywords related to "revenue," "targets," and "goals." |
| **2.2.3** | **Instruction - Comparative Analysis** | Upload two documents and ask: "What are the main differences in the financial outlook between these two reports?" | The Planner should generate prompts that first instruct the AI to analyze the first document for financial outlook, and the refine prompt should instruct it to compare that analysis with the content of the second document. |

### **Node: `_executor_node`**
**Objective:** To ensure the Executor correctly applies the Planner's prompts to analyze the document content.

| Test Case ID | Description | Test Steps | Expected Result |
| :--- | :--- | :--- | :--- |
| **2.3.1** | **Execution - Simple Summary** | Use the plan from Test Case 2.2.1. | The raw output from the executor node (before synthesis) should be a coherent, multi-paragraph summary of the document. |
| **2.3.2** | **Execution - Complex Analysis** | Use the plan from Test Case 2.2.2. | The raw output should be a list or structured text containing the specific information requested (revenue figures, goals, etc.). |
| **2.3.3** | **Execution - Long Document** | Use a document that gets split into 10+ chunks. | The executor should successfully process all chunks using the refine chain, and the final raw output should be a cohesive analysis that covers the entire document. |

### **Node: `_synthesizer_node`**
**Objective:** To verify that the Synthesizer can format the raw analysis from the Executor into a polished, user-friendly final response.

| Test Case ID | Description | Test Steps | Expected Result |
| :--- | :--- | :--- | :--- |
| **2.4.1** | **Formatting - Bullet Points** | Use the output from Test Case 2.3.2 and ask for "a bulleted list of the key findings." | The final response presented to the user should be a well-formatted markdown list, not a plain block of text. |
| **2.4.2** | **Formatting - Table** | Upload a CSV and ask: "Show me the revenue and profit by department in a table." | The Synthesizer should correctly format the extracted data into a markdown table in the final response. |
| **2.4.3** | **Formatting - Narrative** | Use the output from Test Case 2.3.1. | The final response should be a polished narrative, starting with a clear topic sentence (e.g., "Here is a summary of the document:") and presented in well-structured paragraphs. |

