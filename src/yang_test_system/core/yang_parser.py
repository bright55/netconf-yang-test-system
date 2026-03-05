"""YANG Parser - Parse YANG 1.1 files and extract testable nodes

Based on RFC 7950 - The YANG 1.1 Data Modeling Language
"""

import os
import re
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field

try:
    import pyang
    from pyang import statements as stmt
    from pyang.context import Context
    PYANG_AVAILABLE = True
except ImportError:
    PYANG_AVAILABLE = False


@dataclass
class YANGNode:
    """Represents a YANG data node"""
    name: str
    path: str
    node_type: str
    yang_type: Optional[str] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    default_value: Optional[Any] = None
    is_mandatory: bool = False
    is_config: bool = True
    if_feature: List[str] = field(default_factory=list)
    when_condition: Optional[str] = None
    description: Optional[str] = None
    children: List['YANGNode'] = field(default_factory=list)
    parent: Optional['YANGNode'] = None


@dataclass
class YANGModule:
    """Represents a YANG module"""
    name: str
    namespace: str
    prefix: str
    revision: Optional[str] = None
    yang_version: str = "1.1"
    imports: List[Dict[str, str]] = field(default_factory=list)
    includes: List[str] = field(default_factory=list)
    features: List[Dict[str, str]] = field(default_factory=list)
    identities: List[Dict[str, str]] = field(default_factory=list)
    groupings: List[Dict[str, str]] = field(default_factory=list)
    data_nodes: List[YANGNode] = field(default_factory=list)
    rpcs: List[Dict[str, Any]] = field(default_factory=list)
    notifications: List[Dict[str, Any]] = field(default_factory=list)


class YANGParser:
    """YANG 1.1 Parser for extracting testable nodes and schema information"""
    
    def __init__(self, yang_file_path: str):
        """
        Initialize YANG parser
        
        Args:
            yang_file_path: Path to YANG file
        """
        self.yang_file_path = yang_file_path
        self.module: Optional[YANGModule] = None
        self.modules: List[YANGModule] = []
        self.data_nodes: List[YANGNode] = []
        self._errors: List[str] = []
        self._warnings: List[str] = []
        
        if not PYANG_AVAILABLE:
            self._errors.append("pyang library is not installed")
    
    def parse(self) -> Dict[str, Any]:
        """
        Parse YANG file and build data model
        
        Returns:
            Dictionary containing parsed YANG module information
        """
        if not PYANG_AVAILABLE:
            return {"error": "pyang not available", "modules": []}
        
        try:
            # Create pyang context
            ctx = Context()
            ctx.search_ctx = [os.path.dirname(self.yang_file_path)]
            
            # Parse the module
            with open(self.yang_file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Use pyang to parse
            from pyang import parse
            module = parse.parse(ctx, self.yang_file_path)
            
            if module is None:
                self._errors.append("Failed to parse YANG file")
                return {"error": "Parse failed", "modules": []}
            
            # Extract module information
            self.module = self._extract_module_info(module)
            self.modules = [self.module]
            
            # Extract data nodes
            self.data_nodes = self._extract_data_nodes(module)
            self.module.data_nodes = self.data_nodes
            
            return {
                "module": self._module_to_dict(self.module),
                "modules": [self._module_to_dict(m) for m in self.modules],
                "data_nodes": [self._node_to_dict(n) for n in self.data_nodes],
                "errors": self._errors,
                "warnings": self._warnings,
            }
            
        except Exception as e:
            self._errors.append(f"Parse error: {str(e)}")
            return {"error": str(e), "modules": []}
    
    def _extract_module_info(self, module) -> YANGModule:
        """Extract module information from pyang module"""
        name = module.arg
        namespace = ""
        prefix = ""
        revision = None
        yang_version = "1.1"
        imports = []
        includes = []
        features = []
        identities = []
        groupings = []
        rpcs = []
        notifications = []
        
        # Get namespace and prefix
        for child in module.substmts:
            if child.keyword == "namespace":
                namespace = child.arg
            elif child.keyword == "prefix":
                prefix = child.arg
            elif child.keyword == "revision":
                revision = child.arg
            elif child.keyword == "yang-version":
                yang_version = child.arg
            elif child.keyword == "import":
                imports.append({
                    "name": child.arg,
                    "prefix": self._get_child_arg(child, "prefix"),
                })
            elif child.keyword == "include":
                includes.append(child.arg)
            elif child.keyword == "feature":
                features.append({
                    "name": child.arg,
                    "description": self._get_child_arg(child, "description"),
                })
            elif child.keyword == "identity":
                identities.append({
                    "name": child.arg,
                    "base": self._get_child_arg(child, "base"),
                })
            elif child.keyword == "grouping":
                groupings.append({
                    "name": child.arg,
                    "description": self._get_child_arg(child, "description"),
                })
        
        # Get RPCs
        for child in module.substmts:
            if child.keyword == "rpc":
                rpcs.append(self._extract_rpc_info(child))
            elif child.keyword == "notification":
                notifications.append(self._extract_notification_info(child))
        
        return YANGModule(
            name=name,
            namespace=namespace,
            prefix=prefix,
            revision=revision,
            yang_version=yang_version,
            imports=imports,
            includes=includes,
            features=features,
            identities=identities,
            groupings=groupings,
            data_nodes=[],
            rpcs=rpcs,
            notifications=notifications,
        )
    
    def _extract_rpc_info(self, rpc_node) -> Dict[str, Any]:
        """Extract RPC information"""
        rpc_info = {
            "name": rpc_node.arg,
            "description": "",
            "input": [],
            "output": [],
        }
        
        for child in rpc_node.substmts:
            if child.keyword == "description":
                rpc_info["description"] = child.arg
            elif child.keyword == "input":
                rpc_info["input"] = self._extract_rpc_params(child)
            elif child.keyword == "output":
                rpc_info["output"] = self._extract_rpc_params(child)
        
        return rpc_info
    
    def _extract_rpc_params(self, params_node) -> List[Dict[str, Any]]:
        """Extract RPC input/output parameters"""
        params = []
        for child in params_node.substmts:
            if child.keyword in ["leaf", "leaf-list", "container", "list"]:
                params.append({
                    "name": child.arg,
                    "type": self._get_child_arg(child, "type"),
                    "description": self._get_child_arg(child, "description"),
                    "mandatory": self._is_mandatory(child),
                })
        return params
    
    def _extract_notification_info(self, notif_node) -> Dict[str, Any]:
        """Extract notification information"""
        notif_info = {
            "name": notif_node.arg,
            "description": "",
            "data": [],
        }
        
        for child in notif_node.substmts:
            if child.keyword == "description":
                notif_info["description"] = child.arg
            elif child.keyword in ["leaf", "leaf-list", "container", "list"]:
                notif_info["data"].append({
                    "name": child.arg,
                    "type": self._get_child_arg(child, "type"),
                })
        
        return notif_info
    
    def _extract_data_nodes(self, module, parent_path: str = "", parent_node: Optional[YANGNode] = None) -> List[YANGNode]:
        """Extract all data nodes from YANG module"""
        nodes = []
        
        for child in module.substmts:
            if child.keyword in ["container", "list", "leaf", "leaf-list", "choice", "anydata", "anyxml"]:
                node = self._create_yang_node(child, parent_path, parent_node)
                if node:
                    nodes.append(node)
                    
                    # Recursively get children for containers and lists
                    if child.keyword in ["container", "list"]:
                        child_nodes = self._extract_data_nodes(child, node.path, node)
                        nodes.extend(child_nodes)
        
        return nodes
    
    def _create_yang_node(self, stmt_obj, parent_path: str, parent_node: Optional[YANGNode]) -> Optional[YANGNode]:
        """Create YANGNode from pyang statement"""
        name = stmt_obj.arg
        path = f"{parent_path}/{name}" if parent_path else f"/{name}"
        
        node_type = stmt_obj.keyword
        yang_type = self._get_child_arg(stmt_obj, "type")
        constraints = self._extract_constraints(stmt_obj)
        default_value = self._get_child_arg(stmt_obj, "default")
        is_mandatory = self._is_mandatory(stmt_obj)
        is_config = self._is_config(stmt_obj)
        if_feature = self._get_features(stmt_obj)
        when_condition = self._get_child_arg(stmt_obj, "when")
        description = self._get_child_arg(stmt_obj, "description")
        
        return YANGNode(
            name=name,
            path=path,
            node_type=node_type,
            yang_type=yang_type,
            constraints=constraints,
            default_value=default_value,
            is_mandatory=is_mandatory,
            is_config=is_config,
            if_feature=if_feature,
            when_condition=when_condition,
            description=description,
            parent=parent_node,
        )
    
    def _extract_constraints(self, stmt_obj) -> Dict[str, Any]:
        """Extract constraints from YANG statement"""
        constraints = {}
        
        for child in stmt_obj.substmts:
            if child.keyword == "type":
                # Get type constraints
                type_name = child.arg
                constraints["type"] = type_name
                
                for type_child in child.substmts:
                    if type_child.keyword == "range":
                        constraints["range"] = type_child.arg
                    elif type_child.keyword == "length":
                        constraints["length"] = type_child.arg
                    elif type_child.keyword == "pattern":
                        constraints["pattern"] = type_child.arg
                    elif type_child.keyword == "enum":
                        constraints.setdefault("enum", []).append(type_child.arg)
                    elif type_child.keyword == "path":
                        constraints["path"] = type_child.arg
                    elif type_child.keyword == "fraction-digits":
                        constraints["fraction-digits"] = type_child.arg
                    elif type_child.keyword == "base":
                        constraints["base"] = type_child.arg
                    elif type_child.keyword == "require-instance":
                        constraints["require-instance"] = type_child.arg
            
            elif child.keyword == "must":
                constraints.setdefault("must", []).append(child.arg)
            elif child.keyword == "when":
                constraints["when"] = child.arg
        
        return constraints
    
    def _get_child_arg(self, stmt_obj, keyword: str) -> Optional[str]:
        """Get argument from child statement"""
        for child in stmt_obj.substmts:
            if child.keyword == keyword:
                return child.arg
        return None
    
    def _is_mandatory(self, stmt_obj) -> bool:
        """Check if statement is mandatory"""
        for child in stmt_obj.substmts:
            if child.keyword == "mandatory":
                return child.arg.lower() == "true"
        return False
    
    def _is_config(self, stmt_obj) -> bool:
        """Check if statement is config"""
        for child in stmt_obj.substmts:
            if child.keyword == "config":
                return child.arg.lower() == "true"
        return True  # Default is config true
    
    def _get_features(self, stmt_obj) -> List[str]:
        """Get if-feature statements"""
        features = []
        for child in stmt_obj.substmts:
            if child.keyword == "if-feature":
                features.append(child.arg)
        return features
    
    def extract_testable_nodes(self) -> List[Dict]:
        """
        Extract all testable nodes from YANG model
        
        Returns:
            List of testable node dictionaries
        """
        nodes = []
        
        for node in self.data_nodes:
            if self._is_testable(node):
                nodes.append({
                    "path": node.path,
                    "name": node.name,
                    "type": node.node_type,
                    "yang_type": node.yang_type,
                    "constraints": node.constraints,
                    "default_value": node.default_value,
                    "is_mandatory": node.is_mandatory,
                    "is_config": node.is_config,
                    "if_feature": node.if_feature,
                    "when": node.when_condition,
                    "description": node.description,
                })
        
        return nodes
    
    def _is_testable(self, node: YANGNode) -> bool:
        """Check if node is testable"""
        # Only config data nodes are testable for configuration
        if not node.is_config and node.node_type not in ["leaf", "leaf-list"]:
            return False
        return True
    
    def extract_schema_versions(self) -> List[Dict]:
        """
        Extract YANG module version information (RFC 9261)
        
        Returns:
            List of module version dictionaries
        """
        versions = []
        
        for module in self.modules:
            versions.append({
                "name": module.name,
                "revision": module.revision,
                "namespace": module.namespace,
                "yang_version": module.yang_version,
            })
        
        return versions
    
    def extract_rpcs(self) -> List[Dict[str, Any]]:
        """
        Extract RPC definitions from YANG module
        
        Returns:
            List of RPC definitions
        """
        if not self.module:
            return []
        
        return self.module.rpcs
    
    def extract_notifications(self) -> List[Dict[str, Any]]:
        """
        Extract notification definitions from YANG module
        
        Returns:
            List of notification definitions
        """
        if not self.module:
            return []
        
        return self.module.notifications
    
    def extract_features(self) -> List[Dict[str, str]]:
        """
        Extract feature definitions from YANG module
        
        Returns:
            List of feature definitions
        """
        if not self.module:
            return []
        
        return self.module.features
    
    def _module_to_dict(self, module: YANGModule) -> Dict[str, Any]:
        """Convert YANGModule to dictionary"""
        return {
            "name": module.name,
            "namespace": module.namespace,
            "prefix": module.prefix,
            "revision": module.revision,
            "yang_version": module.yang_version,
            "imports": module.imports,
            "includes": module.includes,
            "features": module.features,
            "identities": module.identities,
            "groupings": module.groupings,
            "data_nodes": [self._node_to_dict(n) for n in module.data_nodes],
            "rpcs": module.rpcs,
            "notifications": module.notifications,
        }
    
    def _node_to_dict(self, node: YANGNode) -> Dict[str, Any]:
        """Convert YANGNode to dictionary"""
        return {
            "name": node.name,
            "path": node.path,
            "type": node.node_type,
            "yang_type": node.yang_type,
            "constraints": node.constraints,
            "default_value": node.default_value,
            "is_mandatory": node.is_mandatory,
            "is_config": node.is_config,
            "if_feature": node.if_feature,
            "when": node.when_condition,
            "description": node.description,
        }
