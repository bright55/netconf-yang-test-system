#!/usr/bin/env python
"""Test script for NETCONF/YANG Test System"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from yang_test_system.cli.main import main

if __name__ == "__main__":
    sys.exit(main())
