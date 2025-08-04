# 🔧 Orchestrator V2 Fix Plan - Phased Approach

**Created:** August 3, 2025  
**Objective:** Remove mock responses, implement detailed error logging, and enable DAG replanning  

---

## 🎯 **Fix Strategy Overview**

### **Current Issues Identified:**
1. **Mock Responses** - Tools returning fake data instead of real execution
2. **Planning Engine** - LLM condition parsing failures  
3. **Tool Registry** - Parameter validation mismatches
4. **Execution Engine** - Not actually invoking tools
5. **Error Handling** - Poor error reporting and no replanning

### **Fix Approach:**
- **Phased implementation** for systematic debugging
- **Replace all mocks** with real implementations or detailed errors
- **Implement error-driven replanning** using DAG capabilities
- **Enhanced logging** for full execution traceability

---

## 📋 **Phase-by-Phase Fix Plan**

### **🔥 Phase 1: Remove Mock Responses & Error Handling**
**Status:** In Progress  
**Priority:** Critical  

#### **Target Files:**
- `tools/search_tools.py` - Remove mock knowledge base responses
- `tools/document_tools.py` - Remove MockConfig fallbacks  
- `tools/synthesis_tools.py` - Remove FallbackMockLLM

#### **Changes Required:**
1. **Replace mock knowledge base** with real error when no data available
2. **Remove MockConfig** and use real config or detailed error
3. **Replace FallbackMockLLM** with proper error handling
4. **Implement structured error responses** for replanning

#### **Expected Outcome:**
- No more mock data masking real issues
- Clear error messages for missing functionality
- Tools return actionable error data for replanning

---

### **⚙️ Phase 2: Fix Planning Engine LLM Integration**
**Status:** Pending  
**Priority:** High  

#### **Target Files:**
- `orchestrator_v2/planning_engine.py` - Fix condition parsing
- `orchestrator_v2/tool_registry.py` - Parameter validation

#### **Issues to Fix:**
```
ERROR: 'len($step_1.output) > 0' is not a valid ConditionType
ERROR: 'if_no_active_documents' is not a valid ConditionType  
ERROR: 'document_exists' is not a valid ConditionType
```

#### **Changes Required:**
1. **Fix condition type definitions** in planning engine
2. **Update JSON schema validation** for plan generation
3. **Repair parameter signature matching** between tools and registry
4. **Implement fallback condition parsing** for unknown types

#### **Expected Outcome:**
- Planning engine generates valid execution plans
- Conditions properly parsed and evaluated
- Tool parameters correctly validated

---

### **🚀 Phase 3: Repair Execution Engine Tool Invocation**
**Status:** Pending  
**Priority:** High  

#### **Target Files:**
- `orchestrator_v2/execution_engine.py` - Fix tool execution
- `orchestrator_v2/orchestrator_v2.py` - Integration fixes

#### **Issues to Fix:**
- Tools planned but not executed
- Execution traces showing no tool usage
- System falling back to mock responses

#### **Changes Required:**
1. **Fix tool discovery and invocation** in execution engine
2. **Ensure planned steps actually execute** tools
3. **Remove fallbacks** to mock responses during execution
4. **Implement proper step dependency** resolution

#### **Expected Outcome:**
- Planned tools actually execute
- Execution traces show real tool usage
- No more fallback to mock responses

---

### **📊 Phase 4: Detailed Error Logging & Replanning**
**Status:** Pending  
**Priority:** Medium  

#### **Target Files:**
- `orchestrator_v2/state_management.py` - Error state tracking
- `orchestrator_v2/execution_engine.py` - Error handling
- `orchestrator_v2/planning_engine.py` - Replanning logic

#### **Features to Implement:**
1. **Structured error logging** with actionable information
2. **Error classification** system (retryable, planning, tool, system)
3. **DAG replanning** based on error feedback
4. **Execution retry logic** with different strategies

#### **Error Response Format:**
```json
{
  "error_type": "tool_execution_failed",
  "error_code": "PARAM_VALIDATION_FAILED", 
  "message": "Required parameter 'doc_name' missing",
  "suggested_action": "replan_with_document_discovery",
  "retryable": true,
  "replanning_hints": {
    "add_step": "discover_documents",
    "parameter_source": "document_list_output"
  }
}
```

#### **Expected Outcome:**
- Rich error information for debugging and replanning
- Automatic replanning for recoverable errors
- Better execution success rates through adaptive planning

---

### **✅ Phase 5: Comprehensive Testing & Validation**
**Status:** Pending  
**Priority:** Medium  

#### **Testing Strategy:**
1. **Individual tool testing** - Verify each tool works independently
2. **Planning validation** - Test plan generation and validation
3. **Execution verification** - Confirm tools are actually invoked
4. **Error handling** - Test replanning and recovery mechanisms
5. **Full coverage retest** - Re-run original coverage test

#### **Success Criteria:**
- **>80% tool coverage** in comprehensive test
- **>90% successful tool executions** when tools are available
- **100% error logging** with actionable information
- **>50% automatic recovery** from planning errors

---

## 🛠️ **Implementation Timeline**

### **Phase 1** (Today)
- Remove mock responses
- Implement structured error handling
- Test individual tool error responses

### **Phase 2** (Next)
- Fix planning engine condition parsing
- Update tool registry parameter validation
- Test plan generation

### **Phase 3** (Following)
- Fix execution engine tool invocation
- Implement proper tool execution
- Test end-to-end execution

### **Phase 4** (Then)
- Add detailed error logging
- Implement DAG replanning
- Test error recovery

### **Phase 5** (Finally)
- Comprehensive testing
- Performance validation
- Production readiness assessment

---

## 📈 **Success Metrics**

### **Phase 1 Success:**
- ✅ 0 mock responses in execution
- ✅ Structured error messages
- ✅ Clear tool failure reasons

### **Overall Success:**
- ✅ >80% tool coverage rate
- ✅ >90% tool execution success
- ✅ <3s average execution time
- ✅ Actionable error messages
- ✅ Automatic replanning capability

---

**Next Action:** Begin Phase 1 implementation with mock response removal and error handling.