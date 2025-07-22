import os
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import PyPDF2
from collections import defaultdict

class PDFProcessor:
    def __init__(self):
        # Common heading patterns - ordered by priority
        self.heading_patterns = [
            # Numbered headings (1., 1.1, 1.1.1, etc.)
            (r'^(\d+(?:\.\d+)*\.?)\s+(.+)', 'H1'),
            # Chapter/Section patterns
            (r'^(Chapter|CHAPTER|Section|SECTION)\s+(\d+[.\s]*)?(.+)', 'H1'),
            # All caps headings (likely major headings)
            (r'^([A-Z][A-Z\s]{3,}[A-Z])$', 'H1'),
            # Title case headings with specific formatting
            (r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*$', 'H2'),
            # Headings with special characters
            (r'^([•▪▫◦]\s*)?([A-Z].{5,50})$', 'H2'),
        ]

        # Font size thresholds for heading detection
        self.font_size_thresholds = {
            'title': 16,
            'H1': 14,
            'H2': 12,
            'H3': 10
        }

        # Patterns for extracting important fields
        self.field_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            'date': r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b',
            'url': r'(?:https?://|www\.)[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/[^\s]*)?',
            'version': r'(?:version|ver|v\.?)\s*(\d+(?:\.\d+)*)',
            'copyright': r'©\s*(\d{4}(?:-\d{4})?)|copyright\s*(?:©)?\s*(\d{4}(?:-\d{4})?)',
            'address': r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Parkway|Pkwy)',
            'price': r'\$\s*\d+(?:,\d{3})*(?:\.\d{2})?',
            'id_number': r'\b(?:ID|id|Id)[\s:]*([A-Z0-9]{5,})\b',
            'reference': r'\b(?:Ref|REF|Reference)[\s:]*([A-Z0-9-]{3,})\b',
        }

    def extract_text_with_formatting(self, pdf_path: str) -> List[Dict]:
        """Extract text using PyPDF2 (fallback method)"""
        return self.fallback_text_extraction(pdf_path)

    def fallback_text_extraction(self, pdf_path: str) -> List[Dict]:
        """Extract text using PyPDF2"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                pages_data = []

                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    lines = text.split('\n')

                    text_elements = []
                    for line in lines:
                        line = line.strip()
                        if line:
                            # Estimate font size based on text characteristics
                            font_size = self.estimate_font_size(line)
                            text_elements.append({
                                "text": line,
                                "font_size": font_size,
                                "font": "unknown",
                                "flags": 0,
                                "bbox": [0, 0, 0, 0]
                            })

                    pages_data.append({
                        "page_num": page_num,  # 0-based indexing
                        "text_elements": text_elements
                    })

                return pages_data

        except Exception as e:
            print(f"Error in text extraction: {e}")
            return []

    def estimate_font_size(self, text: str) -> float:
        """Estimate font size based on text characteristics"""
        # All caps and short = likely heading
        if text.isupper() and len(text) < 50:
            return 14
        # Numbered patterns
        if re.match(r'^\d+\.', text):
            return 13
        # Title case patterns that look like headings
        if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$', text) and len(text) < 60:
            return 12
        # Default body text
        return 10

    def extract_title(self, pages_data: List[Dict]) -> str:
        """Extract document title from the first page"""
        if not pages_data:
            return "Untitled Document"

        first_page = pages_data[0]
        title_candidates = []

        # Look for title in first page elements
        for element in first_page["text_elements"][:10]:  # Check first 10 elements
            text = element["text"].strip()
            font_size = element["font_size"]

            # Skip very short text or common non-title patterns
            if len(text) < 3 or text.lower() in ['page', 'of', 'the', 'and']:
                continue

            # Title candidates: large font size or positioned at top
            if font_size >= self.font_size_thresholds['title'] or len(title_candidates) == 0:
                title_candidates.append((text, font_size))

        if title_candidates:
            # Return the text with largest font size
            title_candidates.sort(key=lambda x: x[1], reverse=True)
            return title_candidates[0][0]

        return "Untitled Document"

    def detect_headings(self, pages_data: List[Dict]) -> List[Dict]:
        """Detect headings and create outline"""
        outline = []

        for page_data in pages_data:
            page_num = page_data["page_num"]  # Already 0-based

            for element in page_data["text_elements"]:
                text = element["text"].strip()
                font_size = element["font_size"]

                if not text or len(text) < 3:
                    continue

                # Determine if this is a heading based on font size
                heading_level = self.classify_heading_by_font_size(font_size)

                if not heading_level:
                    # Try pattern matching
                    heading_level = self.classify_heading_by_pattern(text)

                if heading_level:
                    # Clean up the heading text
                    clean_text = self.clean_heading_text(text)
                    if clean_text:
                        outline.append({
                            "level": heading_level,
                            "text": clean_text,
                            "page": page_num  # 0-based page number
                        })

        return self.filter_and_rank_headings(outline)

    def classify_heading_by_font_size(self, font_size: float) -> Optional[str]:
        """Classify heading level based on font size"""
        if font_size >= self.font_size_thresholds['H1']:
            return 'H1'
        elif font_size >= self.font_size_thresholds['H2']:
            return 'H2'
        elif font_size >= self.font_size_thresholds['H3']:
            return 'H3'
        return None

    def classify_heading_by_pattern(self, text: str) -> Optional[str]:
        """Classify heading level based on text patterns"""
        for pattern, level in self.heading_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return level
        return None

    def clean_heading_text(self, text: str) -> str:
        """Clean and normalize heading text"""
        # Remove leading numbers and dots
        text = re.sub(r'^\d+(?:\.\d+)*\.?\s*', '', text)
        # Remove bullet points
        text = re.sub(r'^[•▪▫◦]\s*', '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text.strip()

    def filter_and_rank_headings(self, outline: List[Dict]) -> List[Dict]:
        """Filter out false positives and rank headings"""
        if not outline:
            return []

        # Remove duplicates while preserving order
        seen = set()
        filtered_outline = []
        for item in outline:
            key = (item["text"].lower(), item["page"])
            if key not in seen:
                seen.add(key)
                filtered_outline.append(item)

        # Limit to reasonable number of headings
        return filtered_outline[:20]

    def extract_document_metadata(self, pages_data: List[Dict]) -> Dict:
        """Extract document metadata like author, creation date, etc."""
        metadata = {
            'total_pages': len(pages_data),
            'estimated_word_count': 0,
            'language': 'en',  # Default to English
        }

        # Count approximate words
        for page_data in pages_data:
            for element in page_data["text_elements"]:
                words = len(element["text"].split())
                metadata['estimated_word_count'] += words

        return metadata

    def extract_important_fields(self, pages_data: List[Dict]) -> Dict:
        """Extract important fields like emails, dates, URLs, etc."""
        fields = {
            'emails': [],
            'phones': [],
            'dates': [],
            'urls': [],
            'versions': [],
            'copyrights': [],
            'addresses': [],
            'prices': [],
            'id_numbers': [],
            'references': []
        }

        # Combine all text from all pages
        all_text = ""
        for page_data in pages_data:
            for element in page_data["text_elements"]:
                all_text += element["text"] + " "

        # Extract each type of field
        for field_type, pattern in self.field_patterns.items():
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            if matches:
                if field_type == 'email':
                    fields['emails'] = list(set(matches))  # Remove duplicates
                elif field_type == 'phone':
                    # Format phone numbers
                    formatted_phones = []
                    for match in matches:
                        if isinstance(match, tuple):
                            phone = f"({match[0]}) {match[1]}-{match[2]}"
                        else:
                            phone = match
                        formatted_phones.append(phone)
                    fields['phones'] = list(set(formatted_phones))
                elif field_type == 'date':
                    fields['dates'] = list(set(matches))
                elif field_type == 'url':
                    fields['urls'] = list(set(matches))
                elif field_type == 'version':
                    fields['versions'] = list(set(matches))
                elif field_type == 'copyright':
                    # Handle tuple matches from copyright pattern
                    copyright_years = []
                    for match in matches:
                        if isinstance(match, tuple):
                            year = match[0] or match[1]  # Get non-empty group
                            if year:
                                copyright_years.append(year)
                        else:
                            copyright_years.append(match)
                    fields['copyrights'] = list(set(copyright_years))
                elif field_type == 'address':
                    fields['addresses'] = list(set(matches))
                elif field_type == 'price':
                    fields['prices'] = list(set(matches))
                elif field_type == 'id_number':
                    fields['id_numbers'] = list(set(matches))
                elif field_type == 'reference':
                    fields['references'] = list(set(matches))

        # Clean up empty fields
        return {k: v for k, v in fields.items() if v}

    def extract_key_phrases(self, pages_data: List[Dict]) -> List[str]:
        """Extract key phrases and important terms"""
        # Combine all text
        all_text = ""
        for page_data in pages_data:
            for element in page_data["text_elements"]:
                all_text += element["text"] + " "

        # Simple key phrase extraction based on patterns
        key_phrases = []

        # Look for important phrases (capitalized multi-word terms)
        important_phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b', all_text)
        key_phrases.extend(important_phrases[:10])  # Limit to top 10

        # Look for technical terms (words with numbers/special chars)
        technical_terms = re.findall(r'\b[A-Za-z]+[0-9]+[A-Za-z0-9]*\b|\b[A-Z]{2,}\b', all_text)
        key_phrases.extend(technical_terms[:5])  # Limit to top 5

        # Remove duplicates and return
        return list(set(key_phrases))[:15]  # Max 15 key phrases

    def process_single_pdf(self, pdf_path: str) -> Dict:
        """Process a single PDF and return structured data"""
        print(f"Processing {pdf_path}...")

        # Extract text with formatting information
        pages_data = self.extract_text_with_formatting(pdf_path)

        if not pages_data:
            return {
                "title": "Error: Could not process PDF",
                "outline": []
            }

        # Extract title
        title = self.extract_title(pages_data)

        # Detect headings and create outline
        outline = self.detect_headings(pages_data)

        # Extract additional information
        metadata = self.extract_document_metadata(pages_data)
        important_fields = self.extract_important_fields(pages_data)
        key_phrases = self.extract_key_phrases(pages_data)

        # Create enhanced result
        result = {
            "title": title,
            "outline": outline,
            "metadata": metadata,
            "key_phrases": key_phrases
        }

        # Add important fields if found
        if important_fields:
            result["important_fields"] = important_fields

        return result

def process_pdfs():
    """Main processing function"""
    # Get input and output directories
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize processor
    processor = PDFProcessor()

    # Get all PDF files
    pdf_files = list(input_dir.glob("*.pdf"))

    if not pdf_files:
        print("No PDF files found in input directory")
        return

    print(f"Found {len(pdf_files)} PDF files to process")

    for pdf_file in pdf_files:
        try:
            # Process the PDF
            result = processor.process_single_pdf(str(pdf_file))

            # Create output JSON file
            output_file = output_dir / f"{pdf_file.stem}.json"
            with open(output_file, "w", encoding='utf-8') as f:
                json.dump(result, f, indent=4, ensure_ascii=False)

            print(f"✓ Processed {pdf_file.name} -> {output_file.name}")
            print(f"  Title: {result['title']}")
            print(f"  Outline items: {len(result['outline'])}")

        except Exception as e:
            print(f"✗ Error processing {pdf_file.name}: {e}")
            # Create error output
            error_result = {
                "title": f"Error processing {pdf_file.name}",
                "outline": []
            }
            output_file = output_dir / f"{pdf_file.stem}.json"
            with open(output_file, "w", encoding='utf-8') as f:
                json.dump(error_result, f, indent=4)

if __name__ == "__main__":
    print("Starting PDF processing...")
    process_pdfs()
    print("PDF processing completed!")