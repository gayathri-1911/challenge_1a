# Testing Guide: Challenge 1a Docker Solution

## 🎯 Overview
This guide helps anyone test the Challenge 1a PDF processing solution directly from the GitHub repository. No prior knowledge of the codebase is required - just follow these steps!

## 📋 Prerequisites

### Required Software:
1. **Git** - For cloning the repository
   - Windows: Download from [git-scm.com](https://git-scm.com/)
   - Mac: `brew install git` or download from git-scm.com
   - Linux: `sudo apt install git` (Ubuntu) or `sudo yum install git` (CentOS)

2. **Docker Desktop** - For running the containerized solution
   - Windows/Mac: Download from [docker.com](https://www.docker.com/products/docker-desktop)
   - Linux: Follow Docker installation guide for your distribution

### System Requirements:
- **RAM**: At least 4GB available
- **Storage**: 2GB free space
- **Architecture**: AMD64/x86_64 (Intel/AMD processors)
- **OS**: Windows 10+, macOS 10.14+, or modern Linux

## 🚀 Step-by-Step Testing Instructions

### Step 1: Clone the Repository
Open terminal/command prompt and run:

```bash
git clone https://github.com/dineshkarthik18/persona-driven.git
cd persona-driven/Challenge_1a
```

**What this does:**
- Downloads the complete solution from GitHub
- Navigates to the Challenge 1a directory

### Step 2: Verify Directory Structure
Check that you have all required files:

```bash
# On Windows (Command Prompt)
dir

# On Windows (PowerShell)
ls

# On Mac/Linux
ls -la
```

**You should see:**
```
Challenge_1a/
├── Dockerfile                    # Docker configuration
├── process_pdfs.py              # Main processing script
├── README.md                    # Quick reference
├── EXECUTION_GUIDE.md           # Detailed instructions
├── TESTING_GUIDE.md             # This file
├── input/                       # PDF files to process
├── output/                      # Results will appear here
└── sample_dataset/              # Reference samples
```

### Step 3: Start Docker Desktop
- **Windows/Mac**: Launch Docker Desktop from your applications
- **Linux**: Start Docker service: `sudo systemctl start docker`
- **Wait** for Docker to fully start (green whale icon in system tray)

### Step 4: Verify Docker is Running
```bash
docker --version
docker ps
```

**Expected output:**
```
Docker version 24.x.x, build xxxxx
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```

### Step 5: Build the Docker Image
```bash
docker build --platform linux/amd64 -t test-pdf-processor .
```

**What this does:**
- Creates a Docker image from the solution
- Downloads required dependencies (PyPDF2)
- Takes 1-2 minutes on first run

**Expected output:**
```
[+] Building 45.2s (8/8) FINISHED
 => [internal] load build definition from Dockerfile
 => [internal] load .dockerignore
 => [internal] load metadata for docker.io/library/python:3.10-slim
 => [1/3] FROM docker.io/library/python:3.10-slim
 => [2/3] RUN pip install --no-cache-dir PyPDF2==3.0.1
 => [3/3] COPY process_pdfs.py .
 => exporting to image
 => => naming to docker.io/library/test-pdf-processor
```

### Step 6: Run the PDF Processing
```bash
# For Mac/Linux (bash/zsh)
docker run --rm -v $(pwd)/input:/app/input:ro -v $(pwd)/output/repoidentifier:/app/output --network none test-pdf-processor

# For Windows PowerShell
docker run --rm -v "${PWD}/input:/app/input:ro" -v "${PWD}/output/repoidentifier:/app/output" --network none test-pdf-processor

# For Windows Command Prompt
docker run --rm -v "%cd%/input:/app/input:ro" -v "%cd%/output/repoidentifier:/app/output" --network none test-pdf-processor
```

**Expected output:**
```
Starting PDF processing...
Found 5 PDF files to process
Processing /app/input/file01.pdf...
✓ Processed file01.pdf -> file01.json
  Title: Application form for grant of LTC advance
  Outline items: 20
Processing /app/input/file02.pdf...
✓ Processed file02.pdf -> file02.json
  Title: Overview
  Outline items: 20
Processing /app/input/file03.pdf...
✓ Processed file03.pdf -> file03.json
  Title: Ontario's Libraries
  Outline items: 20
Processing /app/input/file04.pdf...
✓ Processed file04.pdf -> file04.json
  Title: Parsippany -Troy Hills STEM Pathways
  Outline items: 20
Processing /app/input/file05.pdf...
✓ Processed file05.pdf -> file05.json
  Title: ADDRESS:
  Outline items: 12
PDF processing completed!
```

### Step 7: Verify Results
Check the generated JSON files:

```bash
# List generated files
ls output/repoidentifier/

# View a sample result (first 20 lines)
head -20 output/repoidentifier/file01.json
```

**You should see 5 JSON files:**
- `file01.json` (~3.4KB)
- `file02.json` (~4.5KB)
- `file03.json` (~6.1KB)
- `file04.json` (~3.1KB)
- `file05.json` (~1.8KB)

## 📊 What to Expect in Results

### Sample JSON Output Structure:
```json
{
  "title": "Document Title",
  "outline": [
    {
      "level": "H1",
      "text": "Heading Text",
      "page": 0
    }
  ],
  "metadata": {
    "total_pages": 12,
    "estimated_word_count": 2426,
    "language": "en"
  },
  "key_phrases": [
    "Important Terms",
    "Technical Phrases"
  ],
  "important_fields": {
    "emails": ["contact@example.com"],
    "dates": ["May 31, 2014"],
    "urls": ["www.example.com"]
  }
}
```

### Key Features to Verify:
- ✅ **Document titles** are extracted correctly
- ✅ **Outline structure** with hierarchical headings (H1, H2, H3)
- ✅ **0-based page indexing** (pages start from 0)
- ✅ **Enhanced metadata** (page count, word count)
- ✅ **Important fields** (emails, dates, URLs when present)
- ✅ **Key phrases** identification

## 🛠️ Troubleshooting

### Issue: Docker Build Fails
**Solution:**
```bash
# Clean Docker cache and retry
docker system prune -f
docker build --no-cache --platform linux/amd64 -t test-pdf-processor .
```

### Issue: Permission Denied (Linux/Mac)
**Solution:**
```bash
# Add your user to docker group
sudo usermod -aG docker $USER
# Logout and login again, or restart terminal
```

### Issue: Path Not Found (Windows)
**Solution:**
Use absolute paths:
```powershell
docker run --rm -v "C:\full\path\to\persona-driven\Challenge_1a\input:/app/input:ro" -v "C:\full\path\to\persona-driven\Challenge_1a\output\repoidentifier:/app/output" --network none test-pdf-processor
```

### Issue: No Output Files Generated
**Check:**
1. Ensure `output/repoidentifier/` directory exists
2. Check Docker has permission to write to the directory
3. Verify input PDFs exist in `input/` directory

## ⏱️ Performance Benchmarks

**Expected Performance:**
- **Build Time**: 1-2 minutes (first time)
- **Processing Time**: 5-10 seconds total for 5 PDFs
- **Memory Usage**: <500MB peak
- **Docker Image Size**: ~139MB
- **Output Size**: ~19KB total JSON files

## 🎯 Success Criteria

Your test is successful if:
- ✅ Docker build completes without errors
- ✅ All 5 PDF files are processed
- ✅ 5 JSON files are generated in `output/repoidentifier/`
- ✅ JSON files contain structured data with titles and outlines
- ✅ Processing completes in under 15 seconds
- ✅ No error messages in console output

## 📞 Getting Help

If you encounter issues:

1. **Check Prerequisites**: Ensure Docker Desktop is running
2. **Verify Paths**: Make sure you're in the `Challenge_1a` directory
3. **Clean Environment**: Try `docker system prune -f` and rebuild
4. **Check Logs**: Look for error messages in the console output
5. **Platform Issues**: Ensure you're using AMD64 architecture

## 🏆 What This Tests

This solution demonstrates:
- **Advanced PDF Processing**: Beyond basic text extraction
- **Structured Data Extraction**: Titles, headings, metadata
- **Enhanced Features**: Important fields, key phrases
- **Performance Optimization**: Fast processing, small footprint
- **Production Readiness**: Robust error handling, Docker containerization
- **Hackathon Compliance**: Meets all Adobe India Hackathon 2025 requirements

**Happy Testing!** 🚀

---
*This solution was developed for Adobe India Hackathon 2025 Challenge 1a*
