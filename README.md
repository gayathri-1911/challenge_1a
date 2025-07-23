# Challenge 1a: PDF Processing Solution

## 📋 Overview
This solution processes PDF files and extracts structured information including titles and document outlines. It uses Docker for containerized execution and processes multiple PDF files in batch.

## 🚀 Quick Start

### Prerequisites
- Git installed
- Docker Desktop running

### Repository
```bash
git clone https://github.com/gayathri-1911/challenge_1a.git
cd challenge_1a
```

## 🔧 Commands to Run

### 1. Build Docker Image
```bash
docker build --platform linux/amd64 -t challenge1a-processor .
```

### 2. Run Processing

**Mac/Linux:**
```bash
docker run --rm -v $(pwd)/input:/app/input:ro -v $(pwd)/output/repoidentifier:/app/output --network none challenge1a-processor
```

**Windows PowerShell:**
```bash
docker run --rm -v "${PWD}/input:/app/input:ro" -v "${PWD}/output/repoidentifier:/app/output" --network none challenge1a-processor
```

**Windows CMD:**
```bash
docker run --rm -v "%cd%/input:/app/input:ro" -v "%cd%/output/repoidentifier:/app/output" --network none challenge1a-processor
```

### 3. Check Results
```bash
ls output/repoidentifier/
# Should see: file01.json, file02.json, file03.json, file04.json, file05.json
```

## 📊 Expected Output

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
...
PDF processing completed!
```

## ✅ Verification Commands

### Check Generated Files
```bash
# Count lines in output files
wc -l output/repoidentifier/*.json

# View sample output
head -20 output/repoidentifier/file01.json
```

## 📈 Performance Expectations
- **Build Time**: 1-2 minutes
- **Processing Time**: 5-10 seconds
- **Output**: 5 JSON files (~19KB total)
- **Memory Usage**: <500MB peak

## 🔧 Troubleshooting

### If Docker Build Fails
```bash
# Clean Docker cache
docker system prune -f

# Retry build with no cache
docker build --no-cache --platform linux/amd64 -t challenge1a-processor .
```

### If Path Issues (Windows)
```bash
# Use absolute paths
docker run --rm -v "C:\full\path\to\challenge_1a\input:/app/input:ro" -v "C:\full\path\to\challenge_1a\output\repoidentifier:/app/output" --network none challenge1a-processor
```

### Check Docker Status
```bash
docker --version
docker ps
docker images
```

## ✅ Success Criteria
- ✅ 5 JSON files generated in `output/repoidentifier/`
- ✅ Each JSON contains `title` and `outline` fields
- ✅ Page numbers are 0-based indexed
- ✅ Processing completes in <15 seconds

## 📁 Project Structure
```
challenge_1a/
├── input/                  # Input PDF files
│   ├── file01.pdf
│   ├── file02.pdf
│   ├── file03.pdf
│   ├── file04.pdf
│   └── file05.pdf
├── output/
│   └── repoidentifier/     # Generated JSON outputs
├── process_pdfs.py         # Main processing script
├── Dockerfile              # Container configuration
└── README.md              # This file
```

---

*Ready for hackathon evaluation!* 🚀