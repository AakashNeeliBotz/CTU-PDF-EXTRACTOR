"""
Utility module for PDF table extraction
"""
import pandas as pd
import os
from loguru import logger

def preview_table(table, rows=5):
    """
    Display a preview of a table
    
    Args:
        table (camelot.Table): Table object to preview
        rows (int): Number of rows to display
    """
    logger.info(f"Table preview ({min(rows, len(table.df))} rows):")
    print(table.df.head(rows))
    print("-" * 50)

def get_table_info(table):
    """
    Get information about a table
    
    Args:
        table (camelot.Table): Table object to analyze
        
    Returns:
        dict: Dictionary containing table information
    """
    info = {
        'shape': table.df.shape,
        'rows': table.df.shape[0],
        'columns': table.df.shape[1],
        'accuracy': table.accuracy
    }
    return info

def merge_tables(tables):
    """
    Merge multiple tables into one DataFrame
    
    Args:
        tables (list): List of camelot Table objects
        
    Returns:
        pandas.DataFrame: Merged DataFrame
    """
    if not tables:
        return pd.DataFrame()
    
    # Concatenate all tables
    merged_df = pd.concat([table.df for table in tables], ignore_index=True)
    return merged_df