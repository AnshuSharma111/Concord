import sys
import os
import json
from pathlib import Path

# Add the backend app to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'app'))

from backend.app.ingest.extract import extract_evidence_from_file
from backend.app.claims.claim_model import ArtifactSource
from backend.app.evidence.evidence_model import Evidence, EvidenceType

def print_evidence(evidence_list, file_path, file_type):
    """Print evidence in a readable format."""
    print(f"\n{'='*80}")
    print(f"RESULTS FOR: {file_path}")
    print(f"FILE TYPE: {file_type.value}")
    print(f"EVIDENCE COUNT: {len(evidence_list)}")
    print(f"{'='*80}")
    
    if not evidence_list:
        print("❌ No evidence extracted from this file.")
        return
    
    for i, evidence in enumerate(evidence_list, 1):
        print(f"\n📋 EVIDENCE #{i}")
        print(f"├─ Type: {evidence.type.value}")
        print(f"├─ Endpoint: {evidence.endpoint}")
        print(f"├─ Observation: {evidence.observation}")
        print(f"├─ Source File: {evidence.source_file}")
        print(f"├─ Source Location: {evidence.source_location}")
        print(f"└─ Raw Snippet:")
        
        # Format the raw snippet nicely
        if evidence.raw_snippet:
            snippet_lines = evidence.raw_snippet.split('\n')
            for line in snippet_lines:
                print(f"   │ {line}")
        else:
            print(f"   │ (No snippet available)")

def test_single_file(file_path, file_type):
    """Test extraction on a single file."""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    try:
        evidence_list = extract_evidence_from_file(file_path, file_type)
        print_evidence(evidence_list, file_path, file_type)
        return True
    except Exception as e:
        print(f"❌ Error extracting evidence from {file_path}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_directory(directory_path):
    """Test extraction on common files in a directory."""
    if not os.path.exists(directory_path):
        print(f"❌ Directory not found: {directory_path}")
        return
    
    # Common file patterns and their types
    file_patterns = [
        ("README.md", ArtifactSource.README),
        ("readme.md", ArtifactSource.README),
        ("README.txt", ArtifactSource.README),
        ("api.yaml", ArtifactSource.API_SPEC),
        ("api.yml", ArtifactSource.API_SPEC),
        ("openapi.yaml", ArtifactSource.API_SPEC),
        ("openapi.yml", ArtifactSource.API_SPEC),
        ("swagger.yaml", ArtifactSource.API_SPEC),
        ("swagger.yml", ArtifactSource.API_SPEC),
        ("api.json", ArtifactSource.API_SPEC),
        ("openapi.json", ArtifactSource.API_SPEC),
        ("swagger.json", ArtifactSource.API_SPEC),
    ]
    
    # Look for test files (common patterns)
    test_extensions = ['.py', '.js', '.java', '.ts', '.go', '.rb']
    
    found_files = []
    
    # Check for README and API spec files
    for filename, file_type in file_patterns:
        full_path = os.path.join(directory_path, filename)
        if os.path.exists(full_path):
            found_files.append((full_path, file_type))
    
    # Look for test files recursively
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if any(file.endswith(ext) for ext in test_extensions):
                if 'test' in file.lower() or 'spec' in file.lower():
                    full_path = os.path.join(root, file)
                    found_files.append((full_path, ArtifactSource.TEST))
    
    if not found_files:
        print(f"❌ No recognizable files found in {directory_path}")
        return
    
    print(f"🔍 Found {len(found_files)} files to test in {directory_path}")
    for file_path, file_type in found_files:
        test_single_file(file_path, file_type)

def interactive_mode():
    """Interactive mode for testing individual files."""
    print("\n🧪 INTERACTIVE EVIDENCE EXTRACTION TESTER")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Test a single file")
        print("2. Test all files in a directory")
        print("3. Quit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            file_path = input("Enter file path: ").strip().strip('"')
            
            print("\nFile types:")
            print("1. README (markdown/text documentation)")
            print("2. API_SPEC (OpenAPI/Swagger YAML/JSON)")
            print("3. TEST (test files with assertions)")
            
            type_choice = input("Enter file type (1-3): ").strip()
            
            type_map = {
                "1": ArtifactSource.README,
                "2": ArtifactSource.API_SPEC,
                "3": ArtifactSource.TEST
            }
            
            if type_choice in type_map:
                test_single_file(file_path, type_map[type_choice])
            else:
                print("❌ Invalid file type choice")
        
        elif choice == "2":
            directory_path = input("Enter directory path: ").strip().strip('"')
            test_directory(directory_path)
        
        elif choice == "3":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice")

def main():
    """Main function - handle command line arguments or start interactive mode."""
    if len(sys.argv) == 1:
        # No arguments - start interactive mode
        interactive_mode()
    elif len(sys.argv) == 3:
        # File path and type provided
        file_path = sys.argv[1]
        file_type_str = sys.argv[2].upper()
        
        try:
            file_type = ArtifactSource(file_type_str.lower())
            test_single_file(file_path, file_type)
        except ValueError:
            print(f"❌ Invalid file type: {file_type_str}")
            print("Valid types: README, API_SPEC, TEST")
    elif len(sys.argv) == 2:
        # Directory path provided
        directory_path = sys.argv[1]
        if os.path.isdir(directory_path):
            test_directory(directory_path)
        else:
            print(f"❌ Not a directory: {directory_path}")
    else:
        print("Usage:")
        print("  python test_extract.py                    # Interactive mode")
        print("  python test_extract.py <file> <type>      # Test single file")
        print("  python test_extract.py <directory>        # Test directory")
        print("")
        print("File types: README, API_SPEC, TEST")

if __name__ == "__main__":
    main()