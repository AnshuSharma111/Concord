#!/usr/bin/env python3
"""Debug script to test API section detection."""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from ingest.readme_extractor import _find_api_sections

# Read the README content
readme_path = '../samples/sample_readme_disagree.md'
with open(readme_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("🔧 README content:")
print(repr(content))
print("\n" + "="*50 + "\n")

lines = content.split('\n')
print("📋 Lines:")
for i, line in enumerate(lines, 1):
    print(f"{i:2}: {repr(line)}")

print("\n" + "="*50 + "\n")

# Test API detection
sections = _find_api_sections(lines)
print(f"🔍 Found {len(sections)} API sections:")
for i, (start, end, content) in enumerate(sections, 1):
    print(f"  Section {i}: lines {start}-{end}")
    print(f"    Content preview: {repr(content[:100])}...")

# Manual debugging of the detection logic
print("\n" + "="*50 + "\n")
print("🧠 Manual detection analysis:")

API_ROOT_HEADERS = {"api", "endpoints", "routes", "rest api", "http api"}
API_KEYWORDS = {
    "api", "endpoint", "route", "request", "response", "http", "rest",
    "status", "error", "get", "post", "put", "delete", "patch"
}

for i, line in enumerate(lines, 1):
    stripped = line.lstrip()
    if stripped.startswith("#"):
        level = len(stripped) - len(stripped.lstrip("#"))
        header_text = line.lower().strip("# ").strip(":")
        api_signal = sum(1 for kw in API_KEYWORDS if kw in line.lower())
        
        print(f"Line {i}: level={level}, text='{header_text}', signal={api_signal}")
        
        is_api_header = header_text in API_ROOT_HEADERS
        has_signal = api_signal >= 2
        
        if is_api_header:
            print(f"  ✅ MATCHES API_ROOT_HEADERS!")
        if has_signal:
            print(f"  ✅ HAS STRONG API SIGNAL!")
        
        print()