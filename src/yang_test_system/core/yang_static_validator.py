"""YANG Static Validator - Syntax and semantics validation

Based on RFC 7950 - The YANG 1.1 Data Modeling Language
RFC 9195 - YANG Schema Comparison
RFC 9261 - YANG Schema Versioning
"""

import subprocess
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .types import YANGValidationResult


class YANGStaticValidator:
    """YANG static validation using pyang"""
    
    def __init__(self):
        """Initialize static validator"""
        self.pyang_available = self._check_pyang()
        self._errors: List[str] = []
        self._warnings: List[str] = []
    
    def _check_pyang(self) -> bool:
        """Check if pyang is available"""
        try:
            result = subprocess.run(
                ['pyang', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def validate_syntax(self, yang_file: str) -> YANGValidationResult:
        """
        Validate YANG file syntax using pyang
        
        Args:
            yang_file: Path to YANG file
            
        Returns:
            YANGValidationResult with validation status
        """
        if not self.pyang_available:
            return YANGValidationResult(
                is_valid=False,
                errors=[{"error": "pyang not available", "rfc_reference": "RFC 7950"}],
                warnings=[]
            )
        
        if not os.path.exists(yang_file):
            return YANGValidationResult(
                is_valid=False,
                errors=[{"error": f"File not found: {yang_file}", "rfc_reference": "RFC 7950"}],
                warnings=[]
            )
        
        try:
            result = subprocess.run(
                ['pyang', '-Werror', yang_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            errors = []
            warnings = []
            
            for line in result.stderr.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                if 'error:' in line.lower():
                    errors.append({
                        "error": line,
                        "rfc_reference": "RFC 7950"
                    })
                elif 'warning:' in line.lower():
                    warnings.append({
                        "warning": line,
                        "rfc_reference": "RFC 7950"
                    })
            
            return YANGValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings
            )
            
        except subprocess.TimeoutExpired:
            return YANGValidationResult(
                is_valid=False,
                errors=[{"error": "Validation timeout", "rfc_reference": "RFC 7950"}],
                warnings=[]
            )
        except Exception as e:
            return YANGValidationResult(
                is_valid=False,
                errors=[{"error": f"Validation error: {str(e)}", "rfc_reference": "RFC 7950"}],
                warnings=[]
            )
    
    def validate_imports(self, yang_file: str, search_path: Optional[List[str]] = None) -> YANGValidationResult:
        """
        Validate YANG module imports
        
        Args:
            yang_file: Path to YANG file
            search_path: Additional search paths for imported modules
            
        Returns:
            YANGValidationResult with validation status
        """
        if not self.pyang_available:
            return YANGValidationResult(
                is_valid=False,
                errors=[{"error": "pyang not available", "rfc_reference": "RFC 7950 Section 7"}],
                warnings=[]
            )
        
        cmd = ['pyang']
        
        if search_path:
            # Add search paths
            for path in search_path:
                cmd.extend(['-p', path])
        
        cmd.append(yang_file)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            errors = []
            
            for line in result.stderr.split('\n'):
                line = line.strip().lower()
                if 'import' in line and 'error' in line:
                    errors.append({
                        "error": line,
                        "rfc_reference": "RFC 7950 Section 7"
                    })
            
            return YANGValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=[]
            )
            
        except Exception as e:
            return YANGValidationResult(
                is_valid=False,
                errors=[{"error": f"Import validation error: {str(e)}", "rfc_reference": "RFC 7950 Section 7"}],
                warnings=[]
            )
    
    def compare_schemas(self, yang_file1: str, yang_file2: str) -> Dict[str, Any]:
        """
        Compare two YANG schemas (RFC 9195)
        
        Args:
            yang_file1: Path to first YANG file
            yang_file2: Path to second YANG file
            
        Returns:
            Dictionary with comparison results
        """
        if not self.pyang_available:
            return {
                "error": "pyang not available",
                "compatible": False
            }
        
        try:
            # Generate tree for both files
            result1 = subprocess.run(
                ['pyang', '-f', 'tree', yang_file1],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            result2 = subprocess.run(
                ['pyang', '-f', 'tree', yang_file2],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            tree1 = result1.stdout
            tree2 = result2.stdout
            
            # Compare trees
            compatible = tree1 != tree2
            
            return {
                "schema1_tree": tree1,
                "schema2_tree": tree2,
                "compatible": compatible,
                "rfc_reference": "RFC 9195"
            }
            
        except Exception as e:
            return {
                "error": f"Schema comparison error: {str(e)}",
                "compatible": False,
                "rfc_reference": "RFC 9195"
            }
    
    def generate_module_tree(self, yang_file: str, verbose: bool = False) -> Dict[str, Any]:
        """
        Generate tree structure from YANG module
        
        Args:
            yang_file: Path to YANG file
            verbose: Include verbose information
            
        Returns:
            Dictionary with tree structure
        """
        if not self.pyang_available:
            return {"error": "pyang not available"}
        
        cmd = ['pyang', '-f', 'tree']
        if verbose:
            cmd.append('--verbose')
        cmd.append(yang_file)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "tree": result.stdout,
                "errors": result.stderr if result.stderr else None
            }
            
        except Exception as e:
            return {"error": f"Tree generation error: {str(e)}"}
    
    def generate_tree_line(self, yang_file: str) -> Dict[str, Any]:
        """
        Generate tree structure with line definitions
        
        Args:
            yang_file: Path to YANG file
            
        Returns:
            Dictionary with tree structure
        """
        if not self.pyang_available:
            return {"error": "pyang not available"}
        
        try:
            result = subprocess.run(
                ['pyang', '-f', 'tree', '--tree-line-length', '120', yang_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "tree": result.stdout
            }
            
        except Exception as e:
            return {"error": f"Tree line generation error: {str(e)}"}
    
    def extract_module_info(self, yang_file: str) -> Dict[str, Any]:
        """
        Extract module information
        
        Args:
            yang_file: Path to YANG file
            
        Returns:
            Dictionary with module information
        """
        if not self.pyang_available:
            return {"error": "pyang not available"}
        
        try:
            result = subprocess.run(
                ['pyang', '-f', 'module-tags', yang_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "info": result.stdout
            }
            
        except Exception as e:
            return {"error": f"Module info extraction error: {str(e)}"}
    
    def validate_yang_version(self, yang_file: str) -> Dict[str, Any]:
        """
        Validate YANG version
        
        Args:
            yang_file: Path to YANG file
            
        Returns:
            Dictionary with version info
        """
        if not self.pyang_available:
            return {"error": "pyang not available"}
        
        try:
            result = subprocess.run(
                ['pyang', '-v', yang_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Check if it's YANG 1.0 or 1.1
            is_1_1 = '1.1' in result.stdout or 'yang-version 1.1' in open(yang_file).read()
            
            return {
                "version": "1.1" if is_1_1 else "1.0",
                "is_valid": True,
                "rfc_reference": "RFC 7950"
            }
            
        except Exception as e:
            return {"error": f"Version validation error: {str(e)}"}


def create_validator() -> YANGStaticValidator:
    """Factory function to create validator"""
    return YANGStaticValidator()
