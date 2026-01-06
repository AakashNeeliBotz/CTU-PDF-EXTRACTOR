"""
Main script for extracting tables from PDF files
"""
import os
import sys
from loguru import logger
from pdf_extractor.config import DEFAULT_PDF_PATH, OUTPUT_DIR, create_output_directory, PDFS_DIR
from pdf_extractor.core import extract_tables, save_consolidated_excel, extract_required_fields_from_excel
from pdf_extractor.utils import preview_table, get_table_info
from pdf_extractor.summary import generate_extraction_summary, save_summary

def main():
    """Main function to extract tables from PDF"""
    logger.info("PDF Table Extraction Tool")
    logger.info("=" * 30)
    
    # Create output directory
    create_output_directory()
    
    # Check if PDF file exists
    if not os.path.exists(DEFAULT_PDF_PATH):
        logger.error(f"PDF file not found at {DEFAULT_PDF_PATH}")
        logger.error("Please check the file path in config.py")
        return
    
    try:
        # Extract tables
        logger.info("Extracting tables from PDF...")
        tables = extract_tables(DEFAULT_PDF_PATH)
        
        if not tables:
            logger.warning("No tables found in the PDF.")
            return
            
        # Display information about extracted tables
        logger.info(f"\nExtracted {len(tables)} tables:")
        for i, table in enumerate(tables):
            info = get_table_info(table)
            logger.info(f"Table {i+1}: {info['rows']} rows x {info['columns']} columns (Accuracy: {info['accuracy']:.2f}%)")
        
        # Preview first table
        logger.info("\nPreview of first table:")
        preview_table(tables[0])
        
        # Save consolidated Excel file
        logger.info("Creating consolidated Excel file...")
        pdf_filename = os.path.basename(DEFAULT_PDF_PATH)
        save_consolidated_excel(tables, pdf_filename)
        
        # Extract required fields from the consolidated Excel file
        logger.info("Extracting required fields from consolidated Excel file...")
        consolidated_excel_path = os.path.join(OUTPUT_DIR, os.path.splitext(pdf_filename)[0] + '_consolidated.xlsx')
        extract_required_fields_from_excel(consolidated_excel_path)
        
        # Generate and save summary
        logger.info("Generating extraction summary...")
        summary = generate_extraction_summary(tables, DEFAULT_PDF_PATH, ['consolidated_excel', 'required_fields_excel'])
        save_summary(summary, 'json')
        save_summary(summary, 'txt')
        
        logger.success(f"\nAll tables saved to '{OUTPUT_DIR}' directory.")
        logger.success("Extraction process completed successfully!")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return

if __name__ == "__main__":
    main()