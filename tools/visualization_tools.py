"""
Data visualization and chart generation tools for document intelligence.
Creates charts, graphs, and visual content from document data.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from wordcloud import WordCloud
import base64
import io
from typing import Dict, List, Any, Optional
import os

# Set style for better-looking charts
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

async def create_chart(data: Dict[str, List], chart_type: str, title: str = "", 
                      save_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """
    Creates various types of charts from data.
    
    Args:
        data: Dictionary with 'x' and 'y' keys containing data lists
        chart_type: Type of chart (bar, line, pie, scatter, histogram)
        title: Chart title
        save_path: Optional path to save chart image
        **kwargs: Additional styling parameters
        
    Returns:
        Dictionary with chart info and base64 encoded image
    """
    try:
        fig, ax = plt.subplots(figsize=kwargs.get('figsize', (10, 6)))
        
        if chart_type == 'bar':
            ax.bar(data['x'], data['y'], color=kwargs.get('color', 'skyblue'))
            ax.set_xlabel(kwargs.get('xlabel', 'Categories'))
            ax.set_ylabel(kwargs.get('ylabel', 'Values'))
            
        elif chart_type == 'line':
            ax.plot(data['x'], data['y'], marker='o', linewidth=2, markersize=6)
            ax.set_xlabel(kwargs.get('xlabel', 'X Axis'))
            ax.set_ylabel(kwargs.get('ylabel', 'Y Axis'))
            ax.grid(True, alpha=0.3)
            
        elif chart_type == 'pie':
            ax.pie(data['y'], labels=data['x'], autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            
        elif chart_type == 'scatter':
            ax.scatter(data['x'], data['y'], alpha=0.7, s=60)
            ax.set_xlabel(kwargs.get('xlabel', 'X Values'))
            ax.set_ylabel(kwargs.get('ylabel', 'Y Values'))
            
        elif chart_type == 'histogram':
            ax.hist(data['y'], bins=kwargs.get('bins', 20), alpha=0.7, color='lightcoral')
            ax.set_xlabel(kwargs.get('xlabel', 'Values'))
            ax.set_ylabel('Frequency')
            
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()
        
        # Save to file if path provided
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        # Convert to base64 for inline display
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        plt.close()
        
        return {
            "status": "success",
            "chart_type": chart_type,
            "title": title,
            "image_base64": img_base64,
            "save_path": save_path
        }
        
    except Exception as e:
        plt.close()
        return {
            "status": "error",
            "error": str(e)
        }

async def create_wordcloud(text: str, max_words: int = 100, 
                          save_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """
    Generates a word cloud from text content.
    
    Args:
        text: Input text for word cloud
        max_words: Maximum number of words to include
        save_path: Optional path to save image
        **kwargs: WordCloud parameters
        
    Returns:
        Dictionary with word cloud info and base64 image
    """
    try:
        # Create WordCloud
        wordcloud = WordCloud(
            width=kwargs.get('width', 800),
            height=kwargs.get('height', 400),
            max_words=max_words,
            background_color=kwargs.get('background_color', 'white'),
            colormap=kwargs.get('colormap', 'viridis'),
            relative_scaling=0.5,
            random_state=42
        ).generate(text)
        
        # Create plot
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        ax.set_title(kwargs.get('title', 'Word Cloud'), fontsize=16, fontweight='bold')
        
        # Save if path provided
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        # Convert to base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        plt.close()
        
        return {
            "status": "success",
            "word_count": len(wordcloud.words_),
            "image_base64": img_base64,
            "save_path": save_path,
            "top_words": list(wordcloud.words_.keys())[:10]
        }
        
    except Exception as e:
        plt.close()
        return {
            "status": "error", 
            "error": str(e)
        }

async def create_statistical_plot(data: List[float], plot_type: str = "box", 
                                 title: str = "", save_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Creates statistical plots (box plot, distribution, etc.).
    
    Args:
        data: Numerical data for plotting
        plot_type: Type of plot (box, dist, violin)
        title: Plot title
        save_path: Optional save path
        
    Returns:
        Dictionary with plot info and image
    """
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if plot_type == "box":
            ax.boxplot(data, vert=True, patch_artist=True,
                      boxprops=dict(facecolor='lightblue', alpha=0.7))
            ax.set_ylabel('Values')
            ax.set_title(title or 'Box Plot')
            
        elif plot_type == "dist":
            ax.hist(data, bins=30, alpha=0.7, color='lightgreen', density=True)
            ax.set_xlabel('Values')
            ax.set_ylabel('Density')
            ax.set_title(title or 'Distribution Plot')
            
        elif plot_type == "violin":
            ax.violinplot(data, vert=True)
            ax.set_ylabel('Values')
            ax.set_title(title or 'Violin Plot')
            
        plt.tight_layout()
        
        # Save if requested
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        # Convert to base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        plt.close()
        
        return {
            "status": "success",
            "plot_type": plot_type,
            "data_points": len(data),
            "image_base64": img_base64,
            "save_path": save_path
        }
        
    except Exception as e:
        plt.close()
        return {
            "status": "error",
            "error": str(e)
        }

async def create_comparison_chart(datasets: Dict[str, List], chart_type: str = "bar", 
                                 title: str = "", save_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Creates comparison charts with multiple datasets.
    
    Args:
        datasets: Dictionary with dataset names as keys and data lists as values
        chart_type: Type of comparison chart
        title: Chart title
        save_path: Optional save path
        
    Returns:
        Dictionary with chart results
    """
    try:
        fig, ax = plt.subplots(figsize=(12, 6))
        
        if chart_type == "bar":
            x_pos = np.arange(len(list(datasets.values())[0]))
            width = 0.8 / len(datasets)
            
            for i, (name, values) in enumerate(datasets.items()):
                ax.bar(x_pos + i * width, values, width, label=name, alpha=0.8)
            
            ax.set_xlabel('Categories')
            ax.set_ylabel('Values')
            ax.legend()
            
        elif chart_type == "line":
            for name, values in datasets.items():
                ax.plot(values, marker='o', label=name, linewidth=2)
            ax.set_xlabel('Data Points')
            ax.set_ylabel('Values')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
        ax.set_title(title or 'Comparison Chart', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        # Convert to base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        plt.close()
        
        return {
            "status": "success",
            "datasets": list(datasets.keys()),
            "image_base64": img_base64,
            "save_path": save_path
        }
        
    except Exception as e:
        plt.close()
        return {
            "status": "error",
            "error": str(e)
        }