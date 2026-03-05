#!/usr/bin/env python
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from yang_test_system.core.yang_parser import YANGParser

p = YANGParser('ietf-interfaces.yang')
r = p.parse()

print("Keys:", r.keys())
print("Error:", r.get('error'))
print("Errors:", r.get('errors'))
print("Warnings:", r.get('warnings'))
print("Module:", r.get('module', {}).get('name') if r.get('module') else None)
