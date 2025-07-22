# Challenge 1a: PDF Processing Solution

## 🚀 Quick Execution Guide
**For step-by-step execution instructions, see [EXECUTION_GUIDE.md](EXECUTION_GUIDE.md)**

### Quick Commands:
```bash
# Build
docker build --platform linux/amd64 -t dinesh.challenge1a .

# Run
docker run --rm -v $(pwd)/input:/app/input:ro -v $(pwd)/output/repoidentifier/:/app/output --network none dinesh.challenge1a
```

## Overview
This is a **comprehensive solution** for Challenge 1a of the Adobe India Hackathon 2025. The solution extracts structured data from PDF documents including titles, outlines, metadata, and important fields. The solution is containerized using Docker and meets all performance and resource constraints.

## Official Challenge Guidelines

### Submission Requirements
- **GitHub Project**: Complete code repository with working solution
- **Dockerfile**: Must be present in the root directory and functional
- **README.md**:  Documentation explaining the solution, models, and libraries used

### Build Command
```bash
docker build --platform linux/amd64 -t <reponame.someidentifier> .
```

### Run Command
```bash
docker run --rm -v $(pwd)/input:/app/input:ro -v $(pwd)/output/repoidentifier/:/app/output --network none <reponame.someidentifier>
```

### Critical Constraints
- **Execution Time**: ≤ 10 seconds for a 50-page PDF
- **Model Size**: ≤ 200MB (if using ML models)
- **Network**: No internet access allowed during runtime execution
- **Runtime**: Must run on CPU (amd64) with 8 CPUs and 16 GB RAM
- **Architecture**: Must work on AMD64, not ARM-specific

### Key Requirements
- **Automatic Processing**: Process all PDFs from `/app/input` directory
- **Output Format**: Generate `filename.json` for each `filename.pdf`
- **Input Directory**: Read-only access only
- **Open Source**: All libraries, models, and tools must be open source
- **Cross-Platform**: Test on both simple and complex PDFs

## Sample Solution Structure
```
Challenge_1a/
├── sample_dataset/
│   ├── outputs/         # JSON files provided as outputs.
│   ├── pdfs/            # Input PDF files
│   └── schema/          # Output schema definition
│       └── output_schema.json
├── Dockerfile           # Docker container configuration
├── process_pdfs.py      # Sample processing script
└── README.md           # This file
```

## Implementation

### Current Solution
The provided `process_pdfs.py` is a **comprehensive implementation** that:
- Extracts text from PDF files using PyPDF2
- Analyzes document structure and identifies headings
- Generates structured JSON output with title and outline
- Handles various heading patterns (numbered, all-caps, title case)
- Estimates heading hierarchy based on text characteristics
- **Extracts important fields** (emails, dates, URLs, versions, etc.)
- **Generates document metadata** (page count, word count, language)
- **Identifies key phrases** and technical terms
- Processes all PDFs from input directory automatically

### Enhanced Features
- **Text Extraction**: Uses PyPDF2 for reliable PDF text extraction
- **Heading Detection**: Multiple pattern-based approaches for identifying headings
- **Structure Analysis**: Classifies headings into H1, H2, H3 levels
- **Title Extraction**: Automatically identifies document title from first page
- **Field Extraction**: Automatically detects emails, phone numbers, dates, URLs, versions, addresses, prices, ID numbers, and references
- **Metadata Generation**: Provides document statistics (page count, word count, language)
- **Key Phrase Extraction**: Identifies important terms and technical phrases
- **Error Handling**: Robust error handling with fallback mechanisms
- **Performance Optimized**: Lightweight implementation for fast processing

### Processing Script Architecture (`process_pdfs.py`)
```python
class PDFProcessor:
    def extract_text_with_formatting(self, pdf_path: str) -> List[Dict]:
        # Extract text using PyPDF2 with font size estimation

    def extract_title(self, pages_data: List[Dict]) -> str:
        # Identify document title from first page

    def detect_headings(self, pages_data: List[Dict]) -> List[Dict]:
        # Analyze text patterns to identify headings

    def process_single_pdf(self, pdf_path: str) -> Dict:
        # Main processing pipeline for each PDF
```

### Docker Configuration
```dockerfile
FROM --platform=linux/amd64 python:3.10-slim
WORKDIR /app
RUN pip install --no-cache-dir PyPDF2==3.0.1
COPY process_pdfs.py .
CMD ["python", "process_pdfs.py"]
```

## Enhanced Output Format

### Core JSON Structure (Required)
Each PDF generates a JSON file that **conforms to the base schema** defined in `sample_dataset/schema/output_schema.json`:
```json
{
  "title": "Document Title",
  "outline": [
    {
      "level": "H1",
      "text": "Heading Text",
      "page": 0
    }
  ]
}
```

**Note**: Page numbers use **0-based indexing** (first page = 0, second page = 1, etc.)

### Enhanced JSON Structure (Additional Features)
The implementation also provides **additional valuable information**:
```json
{
  "title": "Document Title",
  "outline": [...],
  "metadata": {
    "total_pages": 12,
    "estimated_word_count": 2426,
    "language": "en"
  },
  "key_phrases": [
    "Important Term",
    "Technical Phrase",
    "Key Concept"
  ],
  "important_fields": {
    "emails": ["contact@example.com"],
    "dates": ["May 31, 2014"],
    "urls": ["www.example.com"],
    "versions": ["1.0", "2014"],
    "addresses": ["123 Main Street"],
    "phones": ["(555) 123-4567"]
  }
}
```


## Implementation Details

### Libraries Used
- **PyPDF2 3.0.1**: Lightweight PDF text extraction library
- **Python Standard Library**: re, json, pathlib for text processing
- **No ML Models**: Keeps solution under 200MB constraint

### Heading Detection Algorithm
1. **Font Size Analysis**: Estimates font sizes based on text characteristics
2. **Pattern Matching**: Identifies numbered headings (1., 1.1, etc.)
3. **Text Analysis**: Detects ALL CAPS and Title Case patterns
4. **Hierarchy Classification**: Assigns H1, H2, H3 levels based on patterns
5. **Filtering**: Removes duplicates and limits to top 20 headings

### Performance Optimizations
- **Lightweight Dependencies**: Only PyPDF2, no heavy ML libraries
- **Efficient Text Processing**: Regex-based pattern matching
- **Memory Management**: Processes one PDF at a time
- **Fast Execution**: Optimized for sub-10-second processing


## Testing Your Solution

### Local Testing
```bash
# Build the Docker image
docker build --platform linux/amd64 -t pdf-processor .

# Test with sample data
docker run --rm -v $(pwd)/sample_dataset/pdfs:/app/input:ro -v $(pwd)/sample_dataset/outputs:/app/output --network none pdf-processor
```

### Validation Checklist
- [ ] All PDFs in input directory are processed
- [ ] JSON output files are generated for each PDF
- [ ] Output format matches required structure
- [ ] **Output conforms to schema** in `sample_dataset/schema/output_schema.json`
- [ ] Processing completes within 10 seconds for 50-page PDFs
- [ ] Solution works without internet access
- [ ] Memory usage stays within 16GB limit
- [ ] Compatible with AMD64 architecture

---

## Solution Summary

This implementation provides a complete PDF processing solution that:
- ✅ Extracts text from PDF documents using PyPDF2
- ✅ Identifies document titles and heading structures
- ✅ Generates JSON output conforming to the required schema
- ✅ Processes all PDFs automatically from input directory
- ✅ Handles errors gracefully with fallback mechanisms
- ✅ Meets performance constraints (lightweight, fast execution)
- ✅ Uses only open-source libraries
- ✅ Works on AMD64 architecture without internet access

The solution is production-ready and meets all the official challenge requirements.