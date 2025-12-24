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
        file_obj = io.BytesIO(file_data)
        
        # Try multiple strategies in order of preference
        strategies = [
            ("fast", False),  # Fast strategy - no OCR, no poppler needed
            ("hi_res", True),  # High resolution - requires poppler
            ("ocr_only", True),  # OCR only - requires poppler
        ]
        
        last_error = None
        for strategy, requires_poppler in strategies:
            try:
                print(f"[DocumentProcessor] Trying strategy: {strategy} (requires_poppler={requires_poppler})")
                
                # Partition document using unstructured
                elements = partition(
                    file=file_obj,
                    strategy=strategy,
                    infer_table_structure=True,  # Extract tables
                )
                
                if not elements:
                    raise ValueError("No elements extracted from PDF")
                
                # Extract text content
                text_content = "\n\n".join([str(el) for el in elements])
                
                if not text_content or len(text_content.strip()) < 10:
                    raise ValueError("Extracted text is too short or empty")
                
                # Extract tables
                tables = []
                for element in elements:
                    if hasattr(element, 'metadata'):
                        metadata = element.metadata
                        # Check if it's a table (different ways to check)
                        is_table = (
                            (hasattr(metadata, 'category') and metadata.category == 'Table') or
                            (hasattr(metadata, 'get') and metadata.get('category') == 'Table') or
                            str(type(element)).lower().find('table') != -1
                        )
                        if is_table:
                            table_data = {
                                'text': str(element),
                                'metadata': metadata.to_dict() if hasattr(metadata, 'to_dict') else {}
                            }
                            tables.append(table_data)
                
                # Get page count (if available)
                page_count = 1
                if elements:
                    # Try to get page numbers from metadata
                    page_numbers = []
                    for el in elements:
                        if hasattr(el, 'metadata'):
                            metadata = el.metadata
                            if hasattr(metadata, 'page_number'):
                                page_numbers.append(metadata.page_number)
                            elif hasattr(metadata, 'get'):
                                page_num = metadata.get('page_number')
                                if page_num:
                                    page_numbers.append(page_num)
                    
                    if page_numbers:
                        page_count = max(page_numbers)
                    else:
                        # Estimate from element count (rough heuristic)
                        page_count = max(1, len(elements) // 50)  # Rough estimate
                
                print(f"[DocumentProcessor] Success with strategy '{strategy}': {len(elements)} elements, {len(text_content)} chars, {page_count} pages")
                
                return {
                    'text': text_content,
                    'tables': tables,
                    'page_count': page_count,
                    'elements_count': len(elements)
                }
                
            except Exception as e:
                last_error = e
                print(f"[DocumentProcessor] Strategy '{strategy}' failed: {type(e).__name__}: {str(e)}")
                # Reset file object for next try
                file_obj.seek(0)
                continue
        
        # All unstructured strategies failed, try pypdf as final fallback
        try:
            print(f"[DocumentProcessor] Trying pypdf fallback...")
            import pypdf
            
            file_obj.seek(0)
            pdf_reader = pypdf.PdfReader(file_obj)
            
            text_parts = []
            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            
            if text_parts:
                text_content = "\n\n".join(text_parts)
                page_count = len(pdf_reader.pages)
                
                print(f"[DocumentProcessor] pypdf fallback success: {page_count} pages, {len(text_content)} chars")
                
                return {
                    'text': text_content,
                    'tables': [],
                    'page_count': page_count,
                    'elements_count': page_count
                }
        except Exception as e:
            print(f"[DocumentProcessor] pypdf fallback also failed: {type(e).__name__}: {str(e)}")
        
        # All strategies failed
        error_msg = f"All PDF processing strategies failed. Last error: {str(last_error)}"
        print(f"[DocumentProcessor] {error_msg}")
        return {
            'text': f"Error processing document: {error_msg}",
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

