#!/usr/bin/env python3
"""
Submission Preparation Script for AOS Assignment 4
This script helps prepare the submission folder in the correct format
"""

import os
import sys
import shutil
import zipfile

def validate_files():
    """Check if all required files exist"""
    required_files = ['AOS_Assignment4.py', 'README.md']
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"  • {file}")
        return False
    
    # Check for Report.pdf
    if not os.path.exists('Report.pdf'):
        print("⚠️  Warning: Report.pdf not found!")
        response = input("Do you want to continue without Report.pdf? (y/n): ")
        if response.lower() != 'y':
            return False
    
    return True

def check_forbidden_files():
    """Check for files that should NOT be in submission"""
    forbidden_files = ['outputs.txt', 'requirements.txt', '__pycache__']
    found_forbidden = []
    
    if os.path.exists('outputs.txt'):
        found_forbidden.append('outputs.txt')
    
    if os.path.exists('requirements.txt'):
        found_forbidden.append('requirements.txt')
    
    if os.path.exists('__pycache__'):
        found_forbidden.append('__pycache__/')
    
    if found_forbidden:
        print("\n⚠️  Found files that should NOT be in submission:")
        for file in found_forbidden:
            print(f"  • {file}")
        
        response = input("\nRemove these files before creating submission? (y/n): ")
        if response.lower() == 'y':
            for file in found_forbidden:
                try:
                    if os.path.isdir(file.rstrip('/')):
                        shutil.rmtree(file.rstrip('/'))
                    else:
                        os.remove(file)
                    print(f"  ✓ Removed {file}")
                except Exception as e:
                    print(f"  ✗ Error removing {file}: {e}")

def create_submission(roll_number):
    """Create submission folder and zip file"""
    folder_name = f"{roll_number}_Assignment4"
    zip_name = f"{folder_name}.zip"
    
    # Create submission folder
    if os.path.exists(folder_name):
        print(f"\n⚠️  Folder '{folder_name}' already exists.")
        response = input("Overwrite? (y/n): ")
        if response.lower() == 'y':
            shutil.rmtree(folder_name)
        else:
            print("Submission cancelled.")
            return False
    
    os.makedirs(folder_name)
    print(f"\n✓ Created folder: {folder_name}/")
    
    # Copy required files
    files_to_copy = ['AOS_Assignment4.py', 'README.md']
    if os.path.exists('Report.pdf'):
        files_to_copy.append('Report.pdf')
    
    for file in files_to_copy:
        try:
            shutil.copy(file, folder_name)
            print(f"  ✓ Copied {file}")
        except Exception as e:
            print(f"  ✗ Error copying {file}: {e}")
            return False
    
    # Create zip file
    if os.path.exists(zip_name):
        print(f"\n⚠️  Zip file '{zip_name}' already exists.")
        response = input("Overwrite? (y/n): ")
        if response.lower() == 'y':
            os.remove(zip_name)
        else:
            print("Submission cancelled.")
            shutil.rmtree(folder_name)
            return False
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_name):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, '.')
                zipf.write(file_path, arcname)
                print(f"  ✓ Added to zip: {arcname}")
    
    print(f"\n✅ Created submission: {zip_name}")
    
    # Show structure
    print(f"\nSubmission structure:")
    print(f"{zip_name}")
    print(f"└── {folder_name}/")
    for file in files_to_copy:
        print(f"    ├── {file}")
    
    return True

def verify_code():
    """Basic verification of Python script"""
    print("\n🔍 Verifying AOS_Assignment4.py...")
    
    with open('AOS_Assignment4.py', 'r') as f:
        content = f.read()
    
    issues = []
    
    # Check for hardcoded paths
    if '../test_files/' in content and 'sys.argv' not in content:
        issues.append("⚠️  Possible hardcoded path detected")
    
    # Check for required imports
    required_imports = ['sys', 'SparkContext', 'time']
    for imp in required_imports:
        if imp not in content:
            issues.append(f"⚠️  Missing import: {imp}")
    
    # Check for output file writing
    if 'outputs.txt' not in content:
        issues.append("❌ Script doesn't appear to write to outputs.txt")
    
    if 'open' not in content or '"w"' not in content:
        issues.append("⚠️  Check if opening outputs.txt in write mode")
    
    if issues:
        print("\nCode verification issues:")
        for issue in issues:
            print(f"  {issue}")
        response = input("\nContinue anyway? (y/n): ")
        return response.lower() == 'y'
    else:
        print("  ✓ Code looks good!")
    
    return True

def main():
    print("="*60)
    print("AOS Assignment 4 - Submission Preparation Tool")
    print("="*60)
    
    # Get roll number
    if len(sys.argv) > 1:
        roll_number = sys.argv[1]
    else:
        roll_number = input("\nEnter your roll number: ").strip()
    
    if not roll_number:
        print("❌ Roll number is required!")
        sys.exit(1)
    
    print(f"\nPreparing submission for: {roll_number}")
    
    # Step 1: Validate required files
    print("\n📋 Step 1: Checking required files...")
    if not validate_files():
        print("\n❌ Submission preparation failed!")
        sys.exit(1)
    
    print("  ✓ All required files found!")
    
    # Step 2: Check for forbidden files
    print("\n📋 Step 2: Checking for forbidden files...")
    check_forbidden_files()
    
    # Step 3: Verify code
    print("\n📋 Step 3: Verifying code...")
    if not verify_code():
        print("\n❌ Submission preparation cancelled!")
        sys.exit(1)
    
    # Step 4: Create submission
    print("\n📋 Step 4: Creating submission...")
    if not create_submission(roll_number):
        print("\n❌ Submission preparation failed!")
        sys.exit(1)
    
    # Final checklist
    print("\n" + "="*60)
    print("✅ SUBMISSION READY!")
    print("="*60)
    print("\n📝 Final Checklist:")
    print("  [ ] Test the script with sample data")
    print("  [ ] Verify outputs.txt format")
    print("  [ ] Complete Report.pdf with graphs and observations")
    print("  [ ] Update README.md with your roll number")
    print("  [ ] Test with spark-submit command")
    print("  [ ] Verify zip file structure")
    print(f"\n📦 Submit: {roll_number}_Assignment4.zip")
    print("\n⚠️  Do NOT include outputs.txt in submission!")
    print("    (It will be generated when script runs)")
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
