import os
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import PyPDF2
from collections import defaultdict
import unicodedata

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
        """Extract text using PyPDF2 with improved text processing"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                pages_data = []

                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()

                    # Pre-process text to handle common issues
                    text = self.preprocess_extracted_text(text)
                    lines = text.split('\n')

                    # Merge fragmented lines (especially for Japanese and addresses)
                    lines = self.merge_fragmented_lines(lines)

                    text_elements = []
                    for line in lines:
                        line = line.strip()
                        if line and self.is_valid_text_line(line):
                            # Estimate font size based on text characteristics
                            font_size = self.estimate_font_size_improved(line)
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

    def preprocess_extracted_text(self, text: str) -> str:
        """Preprocess extracted text to handle encoding and formatting issues"""
        # Normalize Unicode characters
        text = unicodedata.normalize('NFKC', text)

        # Fix common PDF extraction issues
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between camelCase
        text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', text)  # Add space between numbers and letters
        text = re.sub(r'([A-Za-z])(\d)', r'\1 \2', text)  # Add space between letters and numbers

        # Fix broken words that got split across lines
        text = re.sub(r'([a-z])-\s*\n\s*([a-z])', r'\1\2', text)

        return text

    def merge_fragmented_lines(self, lines: List[str]) -> List[str]:
        """Merge fragmented lines, especially for Japanese text and addresses"""
        if not lines:
            return lines

        merged_lines = []
        current_line = ""

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                if current_line:
                    merged_lines.append(current_line)
                    current_line = ""
                continue

            # Check if this line should be merged with the previous one
            should_merge = False

            if current_line:
                # Merge if current line ends with incomplete patterns
                if (self.is_incomplete_line(current_line) or
                    self.is_continuation_line(line) or
                    self.should_merge_japanese_lines(current_line, line) or
                    self.should_merge_address_lines(current_line, line)):
                    should_merge = True

            if should_merge:
                # Add appropriate separator
                separator = "" if self.is_japanese_text(current_line) or self.is_japanese_text(line) else " "
                current_line += separator + line
            else:
                if current_line:
                    merged_lines.append(current_line)
                current_line = line

        # Don't forget the last line
        if current_line:
            merged_lines.append(current_line)

        return merged_lines

    def is_incomplete_line(self, line: str) -> bool:
        """Check if a line appears to be incomplete"""
        # Line ends with comma, conjunction, or preposition
        if re.search(r'[,、]$|(?:and|or|of|in|at|to|for|with|by)$', line, re.IGNORECASE):
            return True
        # Line is very short and doesn't end with punctuation
        if len(line) < 20 and not re.search(r'[.!?。！？]$', line):
            return True
        # Line ends with a hyphen (word break)
        if line.endswith('-'):
            return True
        return False

    def is_continuation_line(self, line: str) -> bool:
        """Check if a line appears to be a continuation of the previous line"""
        # Starts with lowercase letter (likely continuation)
        if re.match(r'^[a-z]', line):
            return True
        # Starts with common continuation words
        if re.match(r'^(?:and|or|but|however|therefore|thus|also|furthermore)', line, re.IGNORECASE):
            return True
        return False

    def should_merge_japanese_lines(self, line1: str, line2: str) -> bool:
        """Check if Japanese lines should be merged"""
        if not (self.is_japanese_text(line1) or self.is_japanese_text(line2)):
            return False

        # Japanese text often gets split inappropriately
        # Merge if neither line ends with proper Japanese punctuation
        japanese_endings = r'[。！？、]$'
        if not re.search(japanese_endings, line1) and len(line1) < 50:
            return True
        return False

    def should_merge_address_lines(self, line1: str, line2: str) -> bool:
        """Check if address lines should be merged"""
        # Common address patterns
        address_patterns = [
            r'\d+\s*$',  # Line ending with just a number
            r'[A-Za-z]+\s*$',  # Line ending with just letters (street name)
            r'(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)\s*$',
            r'(?:Suite|Ste|Unit|Apt|Apartment)\s*\d*\s*$',
        ]

        for pattern in address_patterns:
            if re.search(pattern, line1, re.IGNORECASE):
                return True
        return False

    def is_japanese_text(self, text: str) -> bool:
        """Check if text contains Japanese characters"""
        japanese_ranges = [
            (0x3040, 0x309F),  # Hiragana
            (0x30A0, 0x30FF),  # Katakana
            (0x4E00, 0x9FAF),  # CJK Unified Ideographs
        ]

        for char in text:
            char_code = ord(char)
            for start, end in japanese_ranges:
                if start <= char_code <= end:
                    return True
        return False

    def is_valid_text_line(self, line: str) -> bool:
        """Check if a line contains valid, meaningful text"""
        # Filter out gibberish and very short fragments
        if len(line) < 2:
            return False

        # Filter out lines that are mostly special characters or numbers
        if re.match(r'^[^\w\s]*$', line):
            return False

        # Filter out lines with too many repeated characters (likely formatting artifacts)
        if len(set(line.replace(' ', ''))) < 3 and len(line) > 10:
            return False

        # Filter out obvious OCR errors (too many random single characters)
        single_chars = re.findall(r'\b\w\b', line)
        if len(single_chars) > len(line.split()) * 0.5:
            return False

        return True

    def estimate_font_size_improved(self, text: str) -> float:
        """Improved font size estimation based on multiple text characteristics"""
        score = 10  # Base font size for body text

        # Length-based scoring (shorter text more likely to be headings)
        if len(text) < 20:
            score += 3
        elif len(text) < 40:
            score += 2
        elif len(text) < 60:
            score += 1
        elif len(text) > 200:
            score -= 1

        # Pattern-based scoring
        # All caps (strong heading indicator)
        if text.isupper() and len(text) < 80:
            score += 4

        # Numbered headings (1., 1.1, etc.)
        if re.match(r'^\d+(?:\.\d+)*\.?\s+', text):
            score += 3

        # Title case (proper nouns, headings)
        title_case_words = re.findall(r'\b[A-Z][a-z]+\b', text)
        if len(title_case_words) >= len(text.split()) * 0.7:
            score += 2

        # Common heading words
        heading_keywords = [
            'introduction', 'conclusion', 'summary', 'overview', 'background',
            'methodology', 'results', 'discussion', 'references', 'appendix',
            'chapter', 'section', 'part', 'abstract', 'acknowledgments'
        ]
        if any(keyword in text.lower() for keyword in heading_keywords):
            score += 2

        # Structural indicators
        if text.startswith(('Chapter', 'Section', 'Part', 'Appendix')):
            score += 3

        # Bullet points or list items (usually subheadings)
        if re.match(r'^[•▪▫◦\-\*]\s+', text):
            score += 1

        # Japanese heading patterns
        if self.is_japanese_text(text):
            # Japanese section markers
            if re.search(r'[第章節項目]', text):
                score += 3
            # Japanese punctuation patterns for headings
            if re.search(r'^[「『].*[」』]$', text):
                score += 2

        # Penalize very long text (unlikely to be headings)
        if len(text) > 150:
            score -= 2

        # Penalize text with too much punctuation (likely body text)
        punct_ratio = len(re.findall(r'[.,;:!?]', text)) / len(text) if text else 0
        if punct_ratio > 0.1:
            score -= 1

        # Ensure reasonable bounds
        return max(8, min(18, score))

    def estimate_font_size(self, text: str) -> float:
        """Legacy method for backward compatibility"""
        return self.estimate_font_size_improved(text)

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
        """Improved heading detection with better level classification"""
        outline = []
        font_sizes_seen = []

        # First pass: collect all font sizes to establish relative hierarchy
        for page_data in pages_data:
            for element in page_data["text_elements"]:
                font_sizes_seen.append(element.get("font_size", 10))

        # Establish font size thresholds based on actual content
        font_size_thresholds = self.calculate_dynamic_font_thresholds(font_sizes_seen)

        for page_data in pages_data:
            page_num = page_data["page_num"]  # Already 0-based

            for element in page_data["text_elements"]:
                text = element["text"].strip()
                font_size = element.get("font_size", 10)

                if not text or len(text) < 3:
                    continue

                # Enhanced heading detection
                heading_level = self.classify_heading_improved(text, font_size, font_size_thresholds)

                if heading_level:
                    clean_text = self.clean_heading_text_improved(text)
                    if clean_text and len(clean_text) > 2:
                        # Calculate confidence score
                        confidence = self.calculate_heading_confidence(text, font_size, font_size_thresholds)

                        outline.append({
                            "title": clean_text,
                            "level": heading_level,
                            "page": page_num,  # 0-based page number
                            "confidence": confidence,
                            "original_text": text
                        })

        return self.filter_and_rank_headings_improved(outline)

    def calculate_dynamic_font_thresholds(self, font_sizes: List[float]) -> Dict[str, float]:
        """Calculate font size thresholds based on actual document content"""
        if not font_sizes:
            return {'H1': 14, 'H2': 12, 'H3': 11}

        font_sizes = sorted(set(font_sizes), reverse=True)

        # Use percentiles to establish thresholds
        if len(font_sizes) >= 3:
            h1_threshold = font_sizes[0]  # Largest font
            h2_threshold = font_sizes[1] if len(font_sizes) > 1 else font_sizes[0] - 1
            h3_threshold = font_sizes[2] if len(font_sizes) > 2 else font_sizes[1] - 1
        else:
            # Fallback for documents with limited font variation
            max_size = max(font_sizes)
            h1_threshold = max_size
            h2_threshold = max_size - 1
            h3_threshold = max_size - 2

        return {
            'H1': h1_threshold,
            'H2': h2_threshold,
            'H3': h3_threshold
        }

    def classify_heading_improved(self, text: str, font_size: float, thresholds: Dict[str, float]) -> Optional[int]:
        """Improved heading classification combining multiple factors"""
        # Start with pattern-based classification
        pattern_level = self.classify_heading_by_pattern_improved(text)

        # Font size based classification
        font_level = None
        if font_size >= thresholds['H1']:
            font_level = 1
        elif font_size >= thresholds['H2']:
            font_level = 2
        elif font_size >= thresholds['H3']:
            font_level = 3

        # Content-based classification
        content_level = self.classify_heading_by_content(text)

        # Combine classifications with priority: pattern > font > content
        if pattern_level:
            return pattern_level
        elif font_level:
            return font_level
        elif content_level:
            return content_level

        return None

    def classify_heading_by_pattern_improved(self, text: str) -> Optional[int]:
        """Improved pattern-based heading classification"""
        # Level 1 patterns (major headings)
        level1_patterns = [
            r'^(?:Chapter|CHAPTER|第\d+章)\s+\d+',  # Chapter headings
            r'^\d+\.\s+[A-Z]',  # 1. Major Section
            r'^[A-Z][A-Z\s]{10,}$',  # ALL CAPS HEADINGS
            r'^(?:INTRODUCTION|CONCLUSION|SUMMARY|ABSTRACT|REFERENCES)$',
        ]

        # Level 2 patterns (sub-headings)
        level2_patterns = [
            r'^\d+\.\d+\s+',  # 1.1 Subsection
            r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}$',  # Title Case Headings
            r'^(?:Background|Methodology|Results|Discussion)',
        ]

        # Level 3 patterns (sub-sub-headings)
        level3_patterns = [
            r'^\d+\.\d+\.\d+\s+',  # 1.1.1 Sub-subsection
            r'^[a-z]\)\s+',  # a) List item
            r'^[•▪▫◦]\s+[A-Z]',  # Bullet points with capital letters
        ]

        for pattern in level1_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return 1

        for pattern in level2_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return 2

        for pattern in level3_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return 3

        return None

    def classify_heading_by_content(self, text: str) -> Optional[int]:
        """Classify headings based on content and context"""
        # Major section keywords (Level 1)
        major_keywords = [
            'introduction', 'background', 'literature review', 'methodology',
            'results', 'discussion', 'conclusion', 'summary', 'abstract',
            'references', 'bibliography', 'appendix', 'acknowledgments'
        ]

        # Minor section keywords (Level 2)
        minor_keywords = [
            'overview', 'approach', 'analysis', 'findings', 'implications',
            'limitations', 'future work', 'related work', 'case study'
        ]

        text_lower = text.lower()

        if any(keyword in text_lower for keyword in major_keywords):
            return 1
        elif any(keyword in text_lower for keyword in minor_keywords):
            return 2
        elif len(text) < 50 and text[0].isupper():
            return 3

        return None

    def calculate_heading_confidence(self, text: str, font_size: float, thresholds: Dict[str, float]) -> float:
        """Calculate confidence score for heading classification"""
        confidence = 0.5  # Base confidence

        # Font size contribution
        if font_size >= thresholds['H1']:
            confidence += 0.3
        elif font_size >= thresholds['H2']:
            confidence += 0.2
        elif font_size >= thresholds['H3']:
            confidence += 0.1

        # Length contribution (shorter = more likely heading)
        if len(text) < 30:
            confidence += 0.2
        elif len(text) < 60:
            confidence += 0.1

        # Pattern contribution
        if re.match(r'^\d+\.', text):
            confidence += 0.2
        if text.isupper() and len(text) < 50:
            confidence += 0.3

        return min(1.0, confidence)

    def classify_heading_by_font_size(self, font_size: float) -> Optional[str]:
        """Legacy method for backward compatibility"""
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

    def clean_heading_text_improved(self, text: str) -> str:
        """Improved heading text cleaning with better handling of various formats"""
        if not text:
            return ""

        # Store original for reference
        original = text

        # Normalize Unicode
        text = unicodedata.normalize('NFKC', text)

        # Remove common PDF artifacts
        text = re.sub(r'[^\w\s\-.,;:()[\]{}\'\"!?/\\&@#$%^*+=<>|~`]', ' ', text)

        # Handle numbered headings more carefully
        # Keep the number if it's part of a clear heading structure
        if re.match(r'^\d+(?:\.\d+)*\.?\s+[A-Z]', text):
            # This looks like a proper numbered heading, keep the number
            pass
        else:
            # Remove leading numbers and dots for other cases
            text = re.sub(r'^\d+(?:\.\d+)*\.?\s*', '', text)

        # Remove bullet points and list markers
        text = re.sub(r'^[•▪▫◦\-\*]\s*', '', text)

        # Remove excessive punctuation
        text = re.sub(r'[.]{3,}', '...', text)  # Multiple dots to ellipsis
        text = re.sub(r'[-]{2,}', '--', text)   # Multiple dashes to em-dash

        # Clean up spacing
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single space
        text = text.strip()

        # Remove trailing punctuation that doesn't belong in headings
        text = re.sub(r'[.,;:]+$', '', text)

        # Handle Japanese text cleaning
        if self.is_japanese_text(text):
            # Remove common Japanese formatting artifacts
            text = re.sub(r'^[「『]|[」』]$', '', text)  # Remove quote marks

        # Final validation
        if len(text) < 2 or len(text) > 200:
            return ""

        return text.strip()

    def clean_heading_text(self, text: str) -> str:
        """Legacy method for backward compatibility"""
        return self.clean_heading_text_improved(text)

    def filter_and_rank_headings_improved(self, outline: List[Dict]) -> List[Dict]:
        """Improved filtering and ranking of headings with confidence scoring"""
        if not outline:
            return []

        # Remove duplicates while preserving order and keeping highest confidence
        seen = {}
        for item in outline:
            key = (item["title"], item["page"])
            if key not in seen or item.get("confidence", 0) > seen[key].get("confidence", 0):
                seen[key] = item

        filtered_outline = list(seen.values())

        # Sort by page number first, then by confidence
        filtered_outline.sort(key=lambda x: (x["page"], -x.get("confidence", 0)))

        # Filter out low-confidence headings if we have too many
        if len(filtered_outline) > 25:
            # Keep only high-confidence headings
            high_confidence = [item for item in filtered_outline if item.get("confidence", 0) > 0.7]
            if len(high_confidence) >= 10:
                filtered_outline = high_confidence

        # Convert to the expected output format
        final_outline = []
        for item in filtered_outline[:25]:  # Limit to 25 headings
            final_outline.append({
                "title": item["title"],
                "level": item["level"],
                "page": item["page"]
            })

        return final_outline

    def filter_and_rank_headings(self, outline: List[Dict]) -> List[Dict]:
        """Legacy method for backward compatibility"""
        # Handle both old and new formats
        if not outline:
            return []

        # Check if this is the new format (has 'title' key) or old format (has 'text' key)
        if outline and 'title' in outline[0]:
            # New format, use improved method
            return self.filter_and_rank_headings_improved(outline)
        else:
            # Old format, convert and process
            new_format_outline = []
            for item in outline:
                new_format_outline.append({
                    "title": item.get("text", ""),
                    "level": item.get("level", 1),
                    "page": item.get("page", 0),
                    "confidence": 0.5  # Default confidence
                })

            return self.filter_and_rank_headings_improved(new_format_outline)

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