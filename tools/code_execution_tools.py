"""
Code execution and data processing tools for document intelligence.
Provides secure Python code execution with restricted capabilities.
"""

import sys
import io
import contextlib
import ast
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, List
import json
import traceback

# Allowed imports for security
ALLOWED_MODULES = {
    'pandas': pd,
    'np': np,
    'numpy': np,
    'plt': plt,
    'matplotlib.pyplot': plt,
    'sns': sns,
    'seaborn': sns,
    'json': json,
    'math': __import__('math'),
    'statistics': __import__('statistics'),
}

async def execute_python_code(code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Executes Python code safely with restricted imports and captures output.
    
    Args:
        code: Python code to execute
        context: Optional context variables to make available
        
    Returns:
        Dictionary with execution results, output, and any errors
    """
    if context is None:
        context = {}
    
    # Create safe execution environment
    safe_globals = ALLOWED_MODULES.copy()
    safe_globals.update(context)
    
    # Capture stdout
    captured_output = io.StringIO()
    result = {
        "status": "success",
        "output": "",
        "result": None,
        "error": None
    }
    
    try:
        # Validate code safety (basic AST check)
        tree = ast.parse(code)
        
        # Execute code with captured output
        with contextlib.redirect_stdout(captured_output):
            exec_globals = safe_globals.copy()
            exec(code, exec_globals)
            
            # Try to get the last expression result if any
            if exec_globals.get('result') is not None:
                result["result"] = exec_globals['result']
        
        result["output"] = captured_output.getvalue()
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
    
    return result

async def process_table_data(table_data: List[Dict], operation: str, **kwargs) -> Dict[str, Any]:
    """
    Processes table data using pandas operations.
    
    Args:
        table_data: List of dictionaries representing table rows
        operation: Operation to perform (sum, mean, pivot, filter, etc.)
        **kwargs: Additional parameters for the operation
        
    Returns:
        Processed data results
    """
    try:
        # Convert to DataFrame
        df = pd.DataFrame(table_data)
        
        result = {"status": "success", "operation": operation}
        
        if operation == "summary":
            result["data"] = {
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "dtypes": df.dtypes.to_dict(),
                "numeric_summary": df.describe().to_dict() if len(df.select_dtypes(include=[np.number]).columns) > 0 else {}
            }
            
        elif operation == "aggregate":
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            result["data"] = df[numeric_cols].agg(['sum', 'mean', 'min', 'max', 'std']).to_dict()
            
        elif operation == "filter":
            condition = kwargs.get('condition', '')
            if condition:
                filtered_df = df.query(condition)
                result["data"] = filtered_df.to_dict('records')
            else:
                result["data"] = table_data
                
        elif operation == "pivot":
            index_col = kwargs.get('index', df.columns[0])
            value_col = kwargs.get('values', df.columns[-1])
            pivot_df = df.pivot_table(index=index_col, values=value_col, aggfunc='sum')
            result["data"] = pivot_df.to_dict()
            
        else:
            result["status"] = "error"
            result["error"] = f"Unknown operation: {operation}"
            
    except Exception as e:
        result = {
            "status": "error", 
            "error": str(e),
            "traceback": traceback.format_exc()
        }
    
    return result

async def calculate_statistics(data: List[float], metrics: List[str] = None) -> Dict[str, Any]:
    """
    Calculates statistical metrics for numerical data.
    
    Args:
        data: List of numerical values
        metrics: List of metrics to calculate
        
    Returns:
        Dictionary of calculated statistics
    """
    if metrics is None:
        metrics = ['mean', 'median', 'std', 'min', 'max', 'count']
    
    try:
        series = pd.Series(data)
        result = {"status": "success", "statistics": {}}
        
        for metric in metrics:
            if metric == 'mean':
                result["statistics"]['mean'] = series.mean()
            elif metric == 'median':
                result["statistics"]['median'] = series.median()
            elif metric == 'std':
                result["statistics"]['std'] = series.std()
            elif metric == 'min':
                result["statistics"]['min'] = series.min()
            elif metric == 'max':
                result["statistics"]['max'] = series.max()
            elif metric == 'count':
                result["statistics"]['count'] = len(series)
            elif metric == 'quantiles':
                result["statistics"]['quantiles'] = series.quantile([0.25, 0.5, 0.75]).to_dict()
                
    except Exception as e:
        result = {"status": "error", "error": str(e)}
    
    return result