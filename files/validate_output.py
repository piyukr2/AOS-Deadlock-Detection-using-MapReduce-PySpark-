#!/usr/bin/env python3
"""
Output Format Validator for AOS Assignment 4
This script validates that outputs.txt matches the required format
"""

import sys
import re
from datetime import datetime

def validate_outputs(filename="outputs.txt"):
    """Validate the outputs.txt file format"""
    errors = []
    warnings = []
    
    try:
        with open(filename, 'r') as f:
            lines = [line.rstrip('\n') for line in f.readlines()]
    except FileNotFoundError:
        print(f"❌ ERROR: File '{filename}' not found!")
        return False
    
    if not lines:
        print("❌ ERROR: Output file is empty!")
        return False
    
    line_idx = 0
    
    # Section 1: Q1.2a - Process count
    try:
        process_count = int(lines[line_idx])
        print(f"✓ Q1.2a: Process count = {process_count}")
        line_idx += 1
    except (ValueError, IndexError):
        errors.append(f"Line {line_idx + 1}: Expected integer for process count")
        return False
    
    # Section 2: Q1.2b - Resource count
    try:
        resource_count = int(lines[line_idx])
        print(f"✓ Q1.2b: Resource count = {resource_count}")
        line_idx += 1
    except (ValueError, IndexError):
        errors.append(f"Line {line_idx + 1}: Expected integer for resource count")
        return False
    
    # Section 3: Q1.2c - Edge count
    try:
        edge_count = int(lines[line_idx])
        print(f"✓ Q1.2c: Edge count = {edge_count}")
        line_idx += 1
    except (ValueError, IndexError):
        errors.append(f"Line {line_idx + 1}: Expected integer for edge count")
        return False
    
    # Section 4: Q2.1 - Execution time
    try:
        exec_time = float(lines[line_idx])
        if not re.match(r'^\d+\.\d{2}$', lines[line_idx]):
            warnings.append(f"Line {line_idx + 1}: Execution time should have exactly 2 decimal places")
        print(f"✓ Q2.1: Execution time = {exec_time:.2f}s")
        line_idx += 1
    except (ValueError, IndexError):
        errors.append(f"Line {line_idx + 1}: Expected float for execution time")
        return False
    
    # Section 5: Q2.2 - Number of cycles
    try:
        num_cycles = int(lines[line_idx])
        print(f"✓ Q2.2: Number of cycles = {num_cycles}")
        line_idx += 1
    except (ValueError, IndexError):
        errors.append(f"Line {line_idx + 1}: Expected integer for cycle count")
        return False
    
    # Section 6: Cycle listings
    cycles = []
    for i in range(num_cycles):
        if line_idx >= len(lines):
            errors.append(f"Expected {num_cycles} cycles, but only found {i}")
            break
        
        cycle_line = lines[line_idx]
        nodes = cycle_line.split()
        
        # Validate node format
        for node in nodes:
            if not (node.startswith('P') or node.startswith('R')):
                errors.append(f"Line {line_idx + 1}: Invalid node '{node}' (must start with P or R)")
        
        # Check cycle forms a valid path (alternating P and R)
        for j in range(len(nodes) - 1):
            if nodes[j].startswith('P') and not nodes[j + 1].startswith('R'):
                warnings.append(f"Line {line_idx + 1}: Expected alternating P->R pattern in cycle")
            elif nodes[j].startswith('R') and not nodes[j + 1].startswith('P'):
                warnings.append(f"Line {line_idx + 1}: Expected alternating R->P pattern in cycle")
        
        cycles.append((len(nodes), nodes))
        line_idx += 1
    
    # Verify cycles are sorted
    prev_length = 0
    prev_cycle = None
    for length, cycle_nodes in cycles:
        if length < prev_length:
            warnings.append("Cycles are not sorted by length")
        elif length == prev_length and prev_cycle and cycle_nodes < prev_cycle:
            warnings.append("Cycles of same length are not sorted lexicographically")
        prev_length = length
        prev_cycle = cycle_nodes
    
    print(f"✓ Q2.2: Validated {len(cycles)} cycle listings")
    
    # Section 7: Q2.3 - Process count in deadlocks
    try:
        deadlock_process_count = int(lines[line_idx])
        print(f"✓ Q2.3: Processes in deadlocks = {deadlock_process_count}")
        line_idx += 1
    except (ValueError, IndexError):
        errors.append(f"Line {line_idx + 1}: Expected integer for deadlock process count")
        return False
    
    # Section 8: Process list
    if line_idx >= len(lines):
        errors.append("Missing process list")
        return False
    
    process_list = lines[line_idx].split()
    if len(process_list) != deadlock_process_count:
        warnings.append(f"Process count mismatch: expected {deadlock_process_count}, found {len(process_list)}")
    
    # Check if sorted alphabetically
    if process_list != sorted(process_list):
        warnings.append("Process list is not sorted alphabetically")
    
    # Validate all are process nodes
    for proc in process_list:
        if not proc.startswith('P'):
            errors.append(f"Invalid process node '{proc}' in process list")
    
    print(f"✓ Q2.3: Process list validated ({len(process_list)} processes)")
    line_idx += 1
    
    # Section 9: Q3.1 - Deadlock formation timeline
    print("✓ Q3.1: Deadlock formation timeline:")
    timeline = []
    while line_idx < len(lines):
        line = lines[line_idx]
        
        # Check if it's a date line (format: YYYY-MM-DD count)
        date_match = re.match(r'^(\d{4}-\d{2}-\d{2})\s+(\d+)$', line)
        if date_match:
            date_str, count = date_match.groups()
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
                timeline.append((date_str, int(count)))
                print(f"  - {date_str}: {count} deadlock(s)")
                line_idx += 1
            except ValueError:
                errors.append(f"Line {line_idx + 1}: Invalid date format '{date_str}'")
                line_idx += 1
        else:
            break
    
    # Verify timeline is chronologically sorted
    if timeline and timeline != sorted(timeline, key=lambda x: x[0]):
        warnings.append("Timeline dates are not in chronological order")
    
    # Section 10: Q4 - Top 5 resources by in-degree
    print("✓ Q4: Top 5 resources by in-degree:")
    resources = []
    for i in range(5):
        if line_idx >= len(lines):
            warnings.append(f"Expected 5 resources, found only {i}")
            break
        
        resource_match = re.match(r'^(R\d+)\s+(\d+)$', lines[line_idx])
        if resource_match:
            resource_id, degree = resource_match.groups()
            resources.append((resource_id, int(degree)))
            print(f"  - {resource_id}: {degree}")
            line_idx += 1
        else:
            errors.append(f"Line {line_idx + 1}: Expected resource format 'RXXX degree'")
            break
    
    # Verify sorted by degree (descending)
    if resources:
        degrees = [deg for _, deg in resources]
        if degrees != sorted(degrees, reverse=True):
            warnings.append("Resources are not sorted by in-degree (descending)")
    
    # Section 11: Q4 - Top 5 processes by out-degree
    print("✓ Q4: Top 5 processes by out-degree:")
    processes = []
    for i in range(5):
        if line_idx >= len(lines):
            warnings.append(f"Expected 5 processes, found only {i}")
            break
        
        process_match = re.match(r'^(P\d+)\s+(\d+)$', lines[line_idx])
        if process_match:
            process_id, degree = process_match.groups()
            processes.append((process_id, int(degree)))
            print(f"  - {process_id}: {degree}")
            line_idx += 1
        else:
            errors.append(f"Line {line_idx + 1}: Expected process format 'PXXX degree'")
            break
    
    # Verify sorted by degree (descending)
    if processes:
        degrees = [deg for _, deg in processes]
        if degrees != sorted(degrees, reverse=True):
            warnings.append("Processes are not sorted by out-degree (descending)")
    
    # Check for extra lines
    if line_idx < len(lines):
        warnings.append(f"Found {len(lines) - line_idx} unexpected extra line(s) at end of file")
    
    # Print summary
    print("\n" + "="*60)
    if errors:
        print("❌ VALIDATION FAILED!")
        print(f"\n{len(errors)} Error(s):")
        for error in errors:
            print(f"  • {error}")
    else:
        print("✅ VALIDATION PASSED!")
    
    if warnings:
        print(f"\n⚠️  {len(warnings)} Warning(s):")
        for warning in warnings:
            print(f"  • {warning}")
    
    print("="*60)
    
    return len(errors) == 0

if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else "outputs.txt"
    success = validate_outputs(filename)
    sys.exit(0 if success else 1)
