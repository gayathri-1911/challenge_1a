# Quick Test Guide - Challenge 1a PDF Processor

## 🚀 Super Quick Test (5 Minutes)

### Prerequisites:
- Git installed
- Docker Desktop running

### Commands to Run:

```bash
# 1. Clone and navigate
git clone https://github.com/dineshkarthik18/persona-driven.git
cd persona-driven/Challenge_1a

# 2. Build Docker image
docker build --platform linux/amd64 -t test-pdf-processor .

# 3. Run processing
# Mac/Linux:
docker run --rm -v $(pwd)/input:/app/input:ro -v $(pwd)/output/repoidentifier:/app/output --network none test-pdf-processor

# Windows PowerShell:
docker run --rm -v "${PWD}/input:/app/input:ro" -v "${PWD}/output/repoidentifier:/app/output" --network none test-pdf-processor

# Windows CMD:
docker run --rm -v "%cd%/input:/app/input:ro" -v "%cd%/output/repoidentifier:/app/output" --network none test-pdf-processor

# 4. Check results
ls output/repoidentifier/
```

### Expected Results:
- ✅ 5 JSON files generated
- ✅ Processing completes in <15 seconds
- ✅ Console shows "PDF processing completed!"

### Sample Output:
```
Starting PDF processing...
Found 5 PDF files to process
Processing /app/input/file01.pdf...
✓ Processed file01.pdf -> file01.json
  Title: Application form for grant of LTC advance
  Outline items: 20
...
PDF processing completed!
```

### Generated Files:
- `file01.json` - Application form processing
- `file02.json` - Overview document
- `file03.json` - Ontario's Libraries
- `file04.json` - STEM Pathways
- `file05.json` - Address document

## 🔍 What Each JSON Contains:
- **Title**: Extracted document title
- **Outline**: Hierarchical headings with 0-based page numbers
- **Metadata**: Page count, word count, language
- **Key Phrases**: Important terms identified
- **Important Fields**: Emails, dates, URLs (when found)

## 🛠️ If Something Goes Wrong:

### Docker not running?
```bash
# Check Docker status
docker --version
docker ps
```

### Build fails?
```bash
# Clean and retry
docker system prune -f
docker build --no-cache --platform linux/amd64 -t test-pdf-processor .
```

### Path issues on Windows?
Use full paths:
```powershell
docker run --rm -v "C:\full\path\to\persona-driven\Challenge_1a\input:/app/input:ro" -v "C:\full\path\to\persona-driven\Challenge_1a\output\repoidentifier:/app/output" --network none test-pdf-processor
```

## ✅ Success Indicators:
- Build completes without errors
- All 5 PDFs processed successfully
- 5 JSON files created in `output/repoidentifier/`
- Total time under 15 seconds

**That's it! You've successfully tested the Challenge 1a solution!** 🎉

For detailed troubleshooting, see [TESTING_GUIDE.md](TESTING_GUIDE.md)
