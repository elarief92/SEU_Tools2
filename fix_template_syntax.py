#!/usr/bin/env python3
"""
Fix Django template variables that are broken across multiple lines.
This script ensures all Django template variables are on single lines.
"""

import re
import sys

def fix_template_variables(content):
    """Fix Django template variables that are split across multiple lines."""
    
    # Pattern to match template variables split across lines
    # Matches {{ followed by whitespace/newlines followed by variable followed by }}
    pattern = r'{{\s*\n\s*([^}]+?)\s*\n\s*}}'
    
    def replace_multiline_var(match):
        # Extract the variable content and put it on one line
        var_content = match.group(1).strip()
        # Remove any extra whitespace/newlines within the variable
        var_content = re.sub(r'\s+', ' ', var_content)
        return '{{ ' + var_content + ' }}'
    
    # Fix multiline template variables
    fixed_content = re.sub(pattern, replace_multiline_var, content, flags=re.MULTILINE | re.DOTALL)
    
    return fixed_content

def main():
    if len(sys.argv) != 2:
        print("Usage: python fix_template_syntax.py <template_file>")
        sys.exit(1)
    
    template_file = sys.argv[1]
    
    try:
        # Read the template file
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix the template variables
        fixed_content = fix_template_variables(content)
        
        # Write back the fixed content
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"Fixed template variables in {template_file}")
        
    except Exception as e:
        print(f"Error fixing template: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 