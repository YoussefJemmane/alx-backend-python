# coding: utf-8
import re
issues_found = False

with open("test_utils.py", "r") as f:
    lines = f.readlines()
    for i, line in enumerate(lines, 1):
        if len(line.rstrip("\n")) > 79:
            print(f"Line {i} in test_utils.py is too long: {len(line.rstrip('\n'))} chars")
            issues_found = True
    if lines[-1].strip() != "":
        print("test_utils.py does not end with a newline")
        issues_found = True

with open("test_client.py", "r") as f:
    lines = f.readlines()
    # Check blank lines before class definition
    if lines[10].strip() != "" or lines[11].strip() != "":
        print("Expected 2 blank lines before class definition")
        issues_found = True
    # Check blank line before first @parameterized.expand
    if lines[16].strip() != "":
        print("Expected blank line before first @parameterized.expand")
        issues_found = True
    # Check blank line before second @parameterized.expand
    if lines[81].strip() != "":
        print("Expected blank line before second @parameterized.expand")
        issues_found = True
    # Check trailing blank lines
    if lines[-1].strip() == "":
        print("test_client.py ends with a blank line")
        issues_found = True

if not issues_found:
    print("All checked issues have been fixed!")
