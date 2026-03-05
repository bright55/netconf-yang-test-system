#!/usr/bin/env python
import subprocess
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Test static validator
from yang_test_system.core.yang_static_validator import YANGStaticValidator

validator = YANGStaticValidator()
result = validator.validate_syntax('ietf-interfaces.yang')

print("=== YANG Static Validation ===")
print("Valid:", result.is_valid)
print("Errors:", result.errors)
print("Warnings:", result.warnings)

# Try to get tree output
result2 = validator.generate_module_tree('ietf-interfaces.yang')
print("\n=== Tree Output ===")
if 'tree' in result2:
    print(result2['tree'][:500])
