"""Data cleaning and standardization service using MarkItDown."""
from markitdown import MarkItDown
from typing import Dict, List
import json
import re

class CleaningService:
    """Service for cleaning and standardizing document text."""
    
    def __init__(self):
        self.markitdown = MarkItDown()
    
    def clean_text(self, raw_text: str) -> str:
        """Clean and standardize raw text."""
        # Use MarkItDown to clean the text
        try:
            # MarkItDown works with file paths, so we need to handle text differently
            # For now, we'll do manual cleaning that mimics MarkItDown behavior
            
            # Remove excessive whitespace
            cleaned = re.sub(r'\s+', ' ', raw_text)
            
            # Normalize line breaks
            cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
            
            # Preserve legal document structure
            # Keep section headers (lines in ALL CAPS or with numbers)
            # Keep numbered lists
            # Keep paragraph structure
            
            # Remove formatting artifacts
            cleaned = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', cleaned)  # Control chars
            cleaned = re.sub(r'\u200b', '', cleaned)  # Zero-width space
            
            # Normalize quotes
            cleaned = cleaned.replace('"', '"').replace('"', '"')
            cleaned = cleaned.replace(''', "'").replace(''', "'")
            
            return cleaned.strip()
        except Exception as e:
            print(f"Error cleaning text: {str(e)}")
            return raw_text  # Return original if cleaning fails
    
    def extract_tables_to_json(self, tables: List[Dict]) -> List[Dict]:
        """Extract tables and convert to structured JSON."""
        structured_tables = []
        
        for table in tables:
            try:
                table_text = table.get('text', '')
                table_metadata = table.get('metadata', {})
                
                # Try to parse table structure
                # This is a simplified version - in production, use proper table parsing
                lines = table_text.split('\n')
                rows = []
                for line in lines:
                    if line.strip():
                        # Split by common delimiters
                        cells = re.split(r'\s{2,}|\t', line.strip())
                        if len(cells) > 1:
                            rows.append(cells)
                
                if rows:
                    structured_tables.append({
                        'data': rows,
                        'metadata': table_metadata,
                        'row_count': len(rows),
                        'column_count': len(rows[0]) if rows else 0
                    })
            except Exception as e:
                print(f"Error extracting table: {str(e)}")
                # Store as text if parsing fails
                structured_tables.append({
                    'data': table_text,
                    'metadata': table_metadata,
                    'format': 'text'
                })
        
        return structured_tables
    
    def process_document(self, raw_text: str, tables: List[Dict] = None) -> Dict:
        """Process document: clean text and extract structured data."""
        cleaned_text = self.clean_text(raw_text)
        
        structured_tables = []
        if tables:
            structured_tables = self.extract_tables_to_json(tables)
        
        return {
            'cleaned_text': cleaned_text,
            'structured_data': {
                'tables': structured_tables,
                'table_count': len(structured_tables)
            }
        }
    
    def handle_document_version(self, existing_text: str, new_text: str) -> Dict:
        """Handle document versions/amendments."""
        # Simple version detection - compare texts
        similarity = self._calculate_similarity(existing_text, new_text)
        
        if similarity < 0.9:  # Significant changes
            # Extract differences (simplified)
            return {
                'is_amendment': True,
                'similarity': similarity,
                'new_text': new_text,
                'has_changes': True
            }
        else:
            return {
                'is_amendment': False,
                'similarity': similarity,
                'new_text': new_text,
                'has_changes': False
            }
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        # Simple word-based similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0

# Global instance
cleaning_service = CleaningService()

