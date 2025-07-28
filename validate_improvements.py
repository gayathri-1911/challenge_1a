#!/usr/bin/env python3
"""
Validation script for Challenge 1a improvements
Tests the enhanced PDF processing capabilities including:
- Japanese text handling
- Fragmented line merging
- Improved heading detection
- Better font size classification
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List
import re

def load_json_output(file_path: str) -> Dict:
    """Load and parse JSON output file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}

def validate_json_structure(data: Dict, filename: str) -> List[str]:
    """Validate the basic JSON structure"""
    issues = []
    
    # Check required fields
    if 'title' not in data:
        issues.append(f"{filename}: Missing 'title' field")
    elif not data['title'] or data['title'] == "Untitled Document":
        issues.append(f"{filename}: Title is empty or default")
    
    if 'outline' not in data:
        issues.append(f"{filename}: Missing 'outline' field")
    elif not isinstance(data['outline'], list):
        issues.append(f"{filename}: 'outline' is not a list")
    elif len(data['outline']) == 0:
        issues.append(f"{filename}: 'outline' is empty")
    
    return issues

def validate_outline_quality(outline: List[Dict], filename: str) -> List[str]:
    """Validate the quality of outline extraction"""
    issues = []
    
    if not outline:
        return [f"{filename}: No outline items found"]
    
    # Check outline item structure
    for i, item in enumerate(outline):
        if not isinstance(item, dict):
            issues.append(f"{filename}: Outline item {i} is not a dictionary")
            continue
        
        # Required fields in outline items
        required_fields = ['title', 'level', 'page']
        for field in required_fields:
            if field not in item:
                issues.append(f"{filename}: Outline item {i} missing '{field}' field")
        
        # Validate field values
        if 'title' in item:
            if not item['title'] or len(item['title'].strip()) < 2:
                issues.append(f"{filename}: Outline item {i} has empty or too short title")
            
            # Check for fragmented text (common issue)
            if len(item['title']) < 10 and not re.match(r'^\d+\.', item['title']):
                issues.append(f"{filename}: Possible fragmented title: '{item['title']}'")
        
        if 'level' in item:
            if not isinstance(item['level'], int) or item['level'] < 1 or item['level'] > 6:
                issues.append(f"{filename}: Invalid level {item['level']} in outline item {i}")
        
        if 'page' in item:
            if not isinstance(item['page'], int) or item['page'] < 0:
                issues.append(f"{filename}: Invalid page number {item['page']} in outline item {i}")
    
    # Check for reasonable heading hierarchy
    levels = [item.get('level', 1) for item in outline]
    if levels:
        min_level = min(levels)
        max_level = max(levels)
        
        # Should have some level 1 headings
        if min_level > 2:
            issues.append(f"{filename}: No major headings found (minimum level is {min_level})")
        
        # Shouldn't have too deep nesting without intermediate levels
        if max_level - min_level > 3:
            issues.append(f"{filename}: Heading hierarchy too deep ({min_level} to {max_level})")
    
    return issues

def check_text_quality_improvements(outline: List[Dict], filename: str) -> List[str]:
    """Check for improvements in text quality"""
    improvements = []
    issues = []
    
    for item in outline:
        title = item.get('title', '')
        
        # Check for Japanese text handling
        if contains_japanese(title):
            improvements.append(f"{filename}: Successfully processed Japanese text: '{title[:30]}...'")
        
        # Check for merged fragmented lines
        if len(title) > 50 and not title.endswith(('...', '-')):
            improvements.append(f"{filename}: Good length heading (likely merged fragments): '{title[:50]}...'")
        
        # Check for cleaned formatting
        if not re.search(r'[^\w\s\-.,;:()[\]{}\'\"!?/\\&@#$%^*+=<>|~`]', title):
            improvements.append(f"{filename}: Clean text formatting in: '{title[:30]}...'")
        
        # Check for gibberish or artifacts
        if re.search(r'[^\w\s]{3,}|(.)\1{4,}', title):
            issues.append(f"{filename}: Possible gibberish or artifacts: '{title}'")
        
        # Check for address fragments
        if re.match(r'^\d+\s*$|^[A-Za-z]+\s*$', title) and len(title) < 15:
            issues.append(f"{filename}: Possible address fragment: '{title}'")
    
    return improvements + issues

def contains_japanese(text: str) -> bool:
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

def analyze_heading_levels(outline: List[Dict], filename: str) -> List[str]:
    """Analyze heading level distribution and quality"""
    analysis = []
    
    if not outline:
        return [f"{filename}: No headings to analyze"]
    
    # Count headings by level
    level_counts = {}
    for item in outline:
        level = item.get('level', 1)
        level_counts[level] = level_counts.get(level, 0) + 1
    
    analysis.append(f"{filename}: Heading level distribution: {level_counts}")
    
    # Check for reasonable distribution
    total_headings = len(outline)
    level1_count = level_counts.get(1, 0)
    
    if level1_count == 0:
        analysis.append(f"{filename}: WARNING: No level 1 headings found")
    elif level1_count / total_headings > 0.8:
        analysis.append(f"{filename}: WARNING: Too many level 1 headings ({level1_count}/{total_headings})")
    else:
        analysis.append(f"{filename}: Good heading hierarchy balance")
    
    return analysis

def main():
    """Main validation function"""
    output_dir = Path("output/repoidentifier")
    
    if not output_dir.exists():
        print("❌ Output directory not found. Run the PDF processor first.")
        sys.exit(1)
    
    json_files = list(output_dir.glob("*.json"))
    
    if not json_files:
        print("❌ No JSON output files found.")
        sys.exit(1)
    
    print(f"🔍 Validating {len(json_files)} output files...")
    print("=" * 60)
    
    total_issues = 0
    total_improvements = 0
    
    for json_file in sorted(json_files):
        print(f"\n📄 Analyzing {json_file.name}:")
        
        # Load and validate JSON
        data = load_json_output(json_file)
        if not data:
            print(f"❌ Failed to load {json_file.name}")
            total_issues += 1
            continue
        
        # Basic structure validation
        structure_issues = validate_json_structure(data, json_file.name)
        for issue in structure_issues:
            print(f"❌ {issue}")
            total_issues += 1
        
        # Outline quality validation
        outline = data.get('outline', [])
        quality_issues = validate_outline_quality(outline, json_file.name)
        for issue in quality_issues:
            if "Possible fragmented" in issue or "gibberish" in issue:
                print(f"⚠️  {issue}")
            else:
                print(f"❌ {issue}")
            total_issues += 1
        
        # Text quality improvements
        quality_results = check_text_quality_improvements(outline, json_file.name)
        for result in quality_results:
            if "Successfully processed" in result or "Good length" in result or "Clean text" in result:
                print(f"✅ {result}")
                total_improvements += 1
            else:
                print(f"⚠️  {result}")
        
        # Heading level analysis
        level_analysis = analyze_heading_levels(outline, json_file.name)
        for analysis in level_analysis:
            if "WARNING" in analysis:
                print(f"⚠️  {analysis}")
            else:
                print(f"ℹ️  {analysis}")
        
        # Summary for this file
        print(f"   📊 Total outline items: {len(outline)}")
        if outline:
            avg_title_length = sum(len(item.get('title', '')) for item in outline) / len(outline)
            print(f"   📏 Average title length: {avg_title_length:.1f} characters")
    
    print("\n" + "=" * 60)
    print("📋 VALIDATION SUMMARY:")
    print(f"✅ Improvements detected: {total_improvements}")
    print(f"❌ Issues found: {total_issues}")
    
    if total_issues == 0:
        print("🎉 All validations passed! The improvements are working well.")
        return 0
    elif total_issues < 5:
        print("👍 Minor issues found, but overall quality is good.")
        return 0
    else:
        print("⚠️  Several issues found. Consider further improvements.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
