"""
Summary module for PDF table extraction
"""
import pandas as pd
import json
from loguru import logger
from .config import OUTPUT_DIR

def generate_extraction_summary(tables, pdf_path, output_formats):
    """
    Generate a summary of the extraction process
    
    Args:
        tables (list): List of extracted tables
        pdf_path (str): Path to the PDF file
        output_formats (list): List of output formats used
        
    Returns:
        dict: Summary information
    """
    logger.info("Generating extraction summary...")
    
    # Calculate statistics
    total_tables = len(tables)
    
    # Calculate row and column statistics
    row_counts = [table.df.shape[0] for table in tables]
    col_counts = [table.df.shape[1] for table in tables]
    
    summary = {
        'pdf_file': pdf_path,
        'total_tables': total_tables,
        'output_formats': output_formats,
        'table_statistics': {
            'total_rows': sum(row_counts),
            'total_columns': sum(col_counts),
            'avg_rows_per_table': sum(row_counts) / total_tables if total_tables > 0 else 0,
            'avg_columns_per_table': sum(col_counts) / total_tables if total_tables > 0 else 0,
            'max_rows': max(row_counts) if row_counts else 0,
            'min_rows': min(row_counts) if row_counts else 0,
            'max_columns': max(col_counts) if col_counts else 0,
            'min_columns': min(col_counts) if col_counts else 0
        },
        'accuracy_stats': {
            'avg_accuracy': sum([table.accuracy for table in tables]) / total_tables if total_tables > 0 else 0,
            'max_accuracy': max([table.accuracy for table in tables]) if tables else 0,
            'min_accuracy': min([table.accuracy for table in tables]) if tables else 0
        }
    }
    
    logger.success("Extraction summary generated successfully")
    return summary

def save_summary(summary, format='json'):
    """
    Save summary to file
    
    Args:
        summary (dict): Summary information
        format (str): Output format ('json', 'txt')
    """
    logger.info(f"Saving summary as {format}...")
    
    filepath = f"{OUTPUT_DIR}/extraction_summary.{format}"
    
    try:
        if format == 'json':
            with open(filepath, 'w') as f:
                json.dump(summary, f, indent=2)
        elif format == 'txt':
            with open(filepath, 'w') as f:
                f.write("PDF Table Extraction Summary\n")
                f.write("=" * 30 + "\n\n")
                f.write(f"PDF File: {summary['pdf_file']}\n")
                f.write(f"Total Tables Extracted: {summary['total_tables']}\n")
                f.write(f"Output Formats: {', '.join(summary['output_formats'])}\n\n")
                
                f.write("Table Statistics:\n")
                f.write("-" * 20 + "\n")
                stats = summary['table_statistics']
                f.write(f"Total Rows: {stats['total_rows']}\n")
                f.write(f"Total Columns: {stats['total_columns']}\n")
                f.write(f"Average Rows per Table: {stats['avg_rows_per_table']:.2f}\n")
                f.write(f"Average Columns per Table: {stats['avg_columns_per_table']:.2f}\n")
                f.write(f"Max Rows in a Table: {stats['max_rows']}\n")
                f.write(f"Min Rows in a Table: {stats['min_rows']}\n")
                f.write(f"Max Columns in a Table: {stats['max_columns']}\n")
                f.write(f"Min Columns in a Table: {stats['min_columns']}\n\n")
                
                f.write("Accuracy Statistics:\n")
                f.write("-" * 20 + "\n")
                acc_stats = summary['accuracy_stats']
                f.write(f"Average Accuracy: {acc_stats['avg_accuracy']:.2f}%\n")
                f.write(f"Maximum Accuracy: {acc_stats['max_accuracy']:.2f}%\n")
                f.write(f"Minimum Accuracy: {acc_stats['min_accuracy']:.2f}%\n")
        
        logger.success(f"Summary saved to {filepath}")
        
    except Exception as e:
        logger.error(f"Failed to save summary: {str(e)}")