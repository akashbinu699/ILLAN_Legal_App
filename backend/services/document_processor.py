"""Document processing service using Unstructured.io."""
from unstructured.partition.auto import partition
from unstructured.chunking.title import chunk_by_title
from typing import List, Dict, Optional
import base64
import io
from pathlib import Path

class DocumentProcessor:
    """Service for processing PDFs and extracting text."""
    
    @staticmethod
    def process_pdf(file_data: bytes, filename: str) -> Dict:
        """Process PDF file and extract text."""
        try:
            # Create file-like object from bytes
            file_obj = io.BytesIO(file_data)
            
            # Partition document using unstructured
            elements = partition(
                file=file_obj,
                strategy="hi_res",  # High resolution for better accuracy
                infer_table_structure=True,  # Extract tables
            )
            
            # Extract text content
            text_content = "\n\n".join([str(el) for el in elements])
            
            # Extract tables
            tables = []
            for element in elements:
                if hasattr(element, 'metadata') and element.metadata.get('category') == 'Table':
                    # Convert table to structured format
                    table_data = {
                        'text': str(element),
                        'metadata': element.metadata.to_dict() if hasattr(element.metadata, 'to_dict') else {}
                    }
                    tables.append(table_data)
            
            # Get page count (if available)
            page_count = 1
            if elements:
                # Try to get page numbers from metadata
                page_numbers = [
                    el.metadata.page_number 
                    for el in elements 
                    if hasattr(el, 'metadata') and hasattr(el.metadata, 'page_number')
                ]
                if page_numbers:
                    page_count = max(page_numbers)
            
            return {
                'text': text_content,
                'tables': tables,
                'page_count': page_count,
                'elements_count': len(elements)
            }
        except Exception as e:
            print(f"Error processing PDF {filename}: {str(e)}")
            # Fallback: try basic text extraction
            return {
                'text': f"Error processing document: {str(e)}",
                'tables': [],
                'page_count': 1,
                'elements_count': 0
            }
    
    @staticmethod
    def process_image(file_data: bytes, filename: str, mime_type: str) -> Dict:
        """Process image file with OCR."""
        try:
            # Use unstructured for image OCR
            file_obj = io.BytesIO(file_data)
            
            elements = partition(
                file=file_obj,
                strategy="ocr_only",  # OCR for images
            )
            
            text_content = "\n\n".join([str(el) for el in elements])
            
            return {
                'text': text_content,
                'tables': [],
                'page_count': 1,
                'elements_count': len(elements)
            }
        except Exception as e:
            print(f"Error processing image {filename}: {str(e)}")
            return {
                'text': f"Error processing image: {str(e)}",
                'tables': [],
                'page_count': 1,
                'elements_count': 0
            }
    
    @staticmethod
    def process_document(file_data: bytes, filename: str, mime_type: str) -> Dict:
        """Process document based on MIME type."""
        if mime_type == 'application/pdf':
            return DocumentProcessor.process_pdf(file_data, filename)
        elif mime_type.startswith('image/'):
            return DocumentProcessor.process_image(file_data, filename, mime_type)
        else:
            # Try to process as generic document
            try:
                file_obj = io.BytesIO(file_data)
                elements = partition(file=file_obj)
                text_content = "\n\n".join([str(el) for el in elements])
                return {
                    'text': text_content,
                    'tables': [],
                    'page_count': 1,
                    'elements_count': len(elements)
                }
            except Exception as e:
                return {
                    'text': f"Unsupported file type: {mime_type}",
                    'tables': [],
                    'page_count': 1,
                    'elements_count': 0
                }

