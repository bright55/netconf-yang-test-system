# NETCONF/YANG 测试系统方案

## 文档信息
- 版本: v2.0
- 日期: 2026-03-04
- 作者: AI Assistant
- 状态: 基于IETF现行标准 (RFC 6241, RFC 7950等)

---

## 1. 概述

### 1.1 背景
随着网络设备自动化配置管理需求的增长，NETCONF和YANG作为下一代网络管理协议标准已成为行业主流。但同时也带来了测试挑战：
- YANG模型复杂性高，手工测试效率低
- 不同厂商YANG模型差异大
- 配置一致性验证困难
- 多厂商设备能力集差异
- YANG版本演进带来的兼容性问题

### 1.2 目标
1. 自动化测试点生成 - 从YANG文件自动提取可测试的数据节点和操作
2. 静态分析 - YANG文件语法、依赖、一致性验证
3. 功能验证 - NETCONF/RESTCONF协议操作的实际执行验证
4. 可执行脚本生成 - 产出可直接运行的Python测试脚本
5. 测试报告生成 - 统一的测试结果输出
6. 能力协商验证 - 设备能力与标准一致性验证

---

## 2. NETCONF/YANG协议深入理解

### 2.1 NETCONF核心标准 (RFC 6241 / RFC 4741演进)

| RFC | 标题 | 状态 | 重要性 |
|-----|------|------|--------|
| RFC 6241 | Network Configuration Protocol (NETCONF) | 现行标准 | 核心协议 |
| RFC 6242 | NETCONF over SSH | 现行标准 | 传输层 |
| RFC 6243 | With-defaults Capability | 现行标准 | 数据处理 |
| RFC 6536 | NETCONF Access Control Model (NACM) | 现行标准 | 安全 |
| RFC 7276 | NETCONF Notifications | 现行标准 | 事件通知 |
| RFC 8040 | RESTCONF Protocol | 现行标准 | HTTP API |
| RFC 8071 | NETCONF Call Home | 现行标准 | 远程管理 |
| RFC 8526 | NETCONF/RESTCONF Data Models for OAM | 现行标准 | OAM数据模型 |
| RFC 8786 | YANG Data Model for NWDA | 现行标准 | 数据存储架构 |
| RFC 8950 | YANG Push | 现行标准 | 订阅推送 |

### 2.2 YANG数据建模语言标准 (RFC 7950 / RFC 6020演进)

| RFC | 标题 | 状态 | 重要性 |
|-----|------|------|--------|
| RFC 7950 | The YANG 1.1 Data Modeling Language | 现行标准 | 核心语言 |
| RFC 7951 | JSON Encoding of YANG Data | 现行标准 | 数据编码 |
| RFC 8341 | Network Configuration Access Control Model | 现行标准 | 访问控制 |
| RFC 8342 | YANG Data Model for Network Management Datastores | 现行标准 | 数据存储 |
| RFC 8525 | YANG Library | 现行标准 | 模块库 |
| RFC 8527 | RESTCONF Extensions to Support YANG Patch | 现行标准 | 补丁操作 |
| RFC 8528 | Schema Mount | 现行标准 | Schema挂载 |
| RFC 8641 | Subscription to YANG Datastore | 现行标准 | 数据订阅 |
| RFC 8819 | YANG Module Tags | 现行标准 | 模块标签 |
| RFC 9195 | YANG Schema Comparison | 现行标准 | Schema比较 |
| RFC 9261 | YANG Schema Versioning | 现行标准 | 版本控制 |

### 2.3 NETCONF核心能力集 (RFC 6241定义)

| 能力标识 | 描述 | 重要性 | 对应RFC |
|---------|------|--------|---------|
| :base:1 | 基础NETCONF能力 | 必需 | RFC 6241 |
| :writable-running | 写入running配置 | 核心 | RFC 6241 |
| :candidate | 候选配置支持 | 核心 | RFC 6241 |
| :confirmed-commit | 确认提交 | 可选 | RFC 6241 |
| :validate | 配置验证 | 重要 | RFC 6241 |
| :xpath | XPath过滤 | 重要 | RFC 6241 |
| :with-defaults | 默认值处理 | 可选 | RFC 6243 |
| :rollback-on-error | 回滚错误 | 可选 | RFC 6241 |
| :notification | 通知能力 | 重要 | RFC 5277 |
| :interleave | 通知交错 | 可选 | RFC 5277 |

### 2.4 RESTCONF能力集 (RFC 8040定义)

| 能力标识 | 描述 | 重要性 |
|---------|------|--------|
| :resource | RESTCONF资源 | 必需 |
| :datastore | 数据存储访问 | 核心 |
| :yang-push | 数据订阅推送 | 重要 |
| :defaults | 默认值处理 | 可选 |

### 2.5 NETCONF核心操作

```xml
<!-- 获取配置 - get-config -->
<get-config>
    <source><running/></source>
    <filter type="xpath" select="/interfaces/interface[name='eth0']"/>
</get-config>

<!-- 获取运行状态 - get -->
<get>
    <filter type="xpath" select="/interfaces/interface"/>
</get>

<!-- 修改配置 - edit-config -->
<edit-config>
    <target><running/></target>
    <default-operation>merge</default-operation>
    <config>
        <interfaces>
            <interface>
                <name>eth0</name>
                <description>Test</description>
            </interface>
        </interfaces>
    </config>
</edit-config>

<!-- 删除配置 - edit-config with delete -->
<edit-config>
    <target><running/></target>
    <config>
        <interfaces xmlns="http://example.com">
            <interface>
                <name>eth0</name>
                <operation>delete</operation>
            </interface>
        </interfaces>
    </config>
</edit-config>

<!-- 替换配置 - edit-config with replace -->
<edit-config>
    <target><candidate/></target>
    <default-operation>replace</default-operation>
    <config>
        <interfaces>...</interfaces>
    </config>
</edit-config>

<!-- 提交配置 - commit -->
<commit>
    <confirmed/>
    <confirm-timeout>60</confirm-timeout>
</commit>

<!-- 丢弃修改 - discard-changes -->
<discard-changes/>

<!-- 验证配置 - validate -->
<validate>
    <source><candidate/></source>
</validate>

<!-- 锁配置 - lock -->
<lock>
    <target><candidate/></target>
</lock>

<!-- 解锁 - unlock -->
<unlock>
    <target><candidate/></target>
</unlock>

<!-- 复制配置 - copy-config -->
<copy-config>
    <source><url>file:///backup.xml</url></source>
    <target><running/></target>
</copy-config>

<!-- 删除配置 - delete-config -->
<delete-config>
    <target><startup/></target>
</delete-config>

<!-- 关闭会话 - close-session -->
<close-session/>

<!-- 杀掉会话 - kill-session -->
<kill-session>
    <session-id>4</session-id>
</kill-session>
```

### 2.6 YANG 1.1 数据建模示例 (RFC 7950)

```yang
module example-interface {
    namespace "http://example.com/interfaces";
    prefix exif;

    yang-version "1.1";

    revision 2024-01-01 {
        description "Initial revision";
    }

    typedef interface-status {
        type enumeration {
            enum up { value 1; }
            enum down { value 2; }
            enum testing { value 3; }
        }
    }

    container interfaces {
        description "Interface configuration";

        list interface {
            key "name";
            max-elements "unbounded";
            
            leaf name {
                type string;
                description "Interface name";
            }
            
            leaf description {
                type string;
                default "";
                description "Human-readable description";
            }
            
            leaf enabled {
                type boolean;
                default true;
                description "Enable/disable interface";
            }
            
            leaf mtu {
                type uint16 {
                    range "68..9000";
                }
                description "Maximum Transmission Unit";
            }
            
            leaf oper-status {
                type interface-status;
                config false;
                description "Operational status";
            }
            
            uses interface-common;

            choice address-family {
                case ipv4 {
                    leaf ipv4-address { type string; }
                }
                case ipv6 {
                    leaf ipv6-address { type string; }
                }
            }
        }
    }

    grouping interface-common {
        leaf type {
            type identityref {
                base interface-type;
            }
        }
        
        leaf speed {
            type uint32;
            units "bps";
        }
    }

    identity interface-type {
        description "Base identity for interface types";
    }

    rpc reboot {
        description "Reboot the device";
        
        input {
            leaf delay {
                type uint32;
                default 0;
                units "seconds";
            }
            leaf message {
                type string;
                description "Reboot message";
            }
        }
        
        output {
            leaf status {
                type string;
            }
        }
    }

    notification interface-link-failure {
        description "Link failure detected";
        
        leaf name {
            type leafref {
                path "/interfaces/interface/name";
            }
        }
        leaf cause {
            type enumeration {
                enum link-down;
                enum carrier-lost;
                enum not-present;
            }
        }
    }

    feature loopback {
        description "Device supports loopback";
    }

    leaf loopback-enabled {
        if-feature loopback;
        type boolean;
    }
}
```

### 2.7 YANG数据节点类型

| 类型 | 描述 | 示例 |
|-----|------|------|
| leaf | 单值叶节点 | leaf name { type string; } |
| leaf-list | 列表叶节点 | leaf-list addresses { type ip-address; } |
| container | 容器 | container config { ... } |
| list | 列表 | list interface { key "name"; ... } |
| choice | 选择 | choice address-family { ... } |
| case | 分支 | case ipv4 { ... } |
| augment | 扩展 | augment "/if:interfaces/if:interface" { ... } |
| uses | 使用组 | uses interface-common; |

---

## 3. 测试系统架构

### 3.1 系统总体架构

```
+------------------------------------------------------------+
|                    NETCONF/YANG 测试系统 v2.0                |
+------------------------------------------------------------+
|  输入层: CLI / Web UI / REST API / Python SDK             |
+------------------------------------------------------------+
|  核心引擎:                                                  |
|  +----------+  +----------+  +----------+  +----------+      |
|  | YANG     |  | 测试点   |  | 脚本     |  | 测试     |      |
|  | 解析器   |  | 生成器   |  | 生成器   |  | 执行器   |      |
|  +----------+  +----------+  +----------+  +----------+      |
|  +----------+  +----------+  +----------+  +----------+      |
|  | 能力     |  | RESTCONF|  | YANG Push|  | Schema   |      |
|  | 协商器   |  | 测试器   |  | 测试器   |  | 版本比较器|      |
|  +----------+  +----------+  +----------+  +----------+      |
+------------------------------------------------------------+
|  依赖层: ncclient, pyang, pytest, jinja2, requests         |
+------------------------------------------------------------+
```

### 3.2 核心模块设计

#### 3.2.1 YANG解析器
```python
class YANGParser:
    def __init__(self, yang_file_path: str):
        self.yang_file_path = yang_file_path
        
    def parse(self) -> Dict[str, Any]:
        # 1. 基础语法检查 (RFC 7950)
        # 2. 提取所有声明
        # 3. 构建数据模型
        # 4. 解析uses/augment关系
        pass
    
    def extract_testable_nodes(self) -> List[Dict]:
        nodes = []
        for node in self.data_nodes:
            if self._is_testable(node):
                nodes.append({
                    'path': node.path,
                    'type': node.type,
                    'constraints': self._extract_constraints(node),
                    'yang_version': node.yang_version,
                    'if_feature': node.if_feature,
                    'when': node.when,
                })
        return nodes
    
    def _extract_constraints(self, node) -> Dict:
        constraints = {}
        if hasattr(node, 'range'): constraints['range'] = node.range
        if hasattr(node, 'pattern'): constraints['pattern'] = node.pattern
        if hasattr(node, 'enum'): constraints['enum'] = node.enum
        if hasattr(node, 'default'): constraints['default'] = node.default
        if hasattr(node, 'must'): constraints['must'] = node.must
        if hasattr(node, 'min_elements'): constraints['min_elements'] = node.min_elements
        if hasattr(node, 'max_elements'): constraints['max_elements'] = node.max_elements
        return constraints
    
    def extract_schema_versions(self) -> List[Dict]:
        """提取YANG模块版本信息 (RFC 9261)"""
        versions = []
        for module in self.modules:
            versions.append({
                'name': module.name,
                'revision': module.revision,
                'namespace': module.namespace,
                'yang_version': module.yang_version,
            })
        return versions
```

#### 3.2.2 NETCONF能力协商器
```python
class CapabilityNegotiator:
    """NETCONF/RESTCONF能力协商验证 (RFC 6241, RFC 8040)"""
    
    NETCONF_CAPABILITIES = {
        'base:1': '基础NETCONF能力',
        'writable-running': '写入running配置',
        'candidate': '候选配置支持',
        'confirmed-commit': '确认提交',
        'validate': '配置验证',
        'xpath': 'XPath过滤',
        'with-defaults': '默认值处理 (RFC 6243)',
        'rollback-on-error': '错误回滚',
        'notification': '通知能力',
        'interleave': '通知交错',
    }
    
    RESTCONF_CAPABILITIES = {
        'resource': 'RESTCONF资源',
        'datastore': '数据存储访问',
        'yang-push': 'YANG Push订阅 (RFC 8641)',
        'defaults': '默认值处理',
    }
    
    def get_device_capabilities(self, device_info: Dict) -> Dict:
        """获取设备能力集"""
        client = NETCONFClient(**device_info)
        capabilities = client.get_capabilities()
        return {
            'netconf': capabilities.get('server_capabilities', []),
            'restconf': capabilities.get('restconf_operations', []),
        }
    
    def verify_capability_consistency(self, expected: List[str], 
                                     actual: List[str]) -> TestResult:
        """验证能力一致性"""
        missing = set(expected) - set(actual)
        extra = set(actual) - set(expected)
        
        return TestResult(
            passed=len(missing) == 0,
            details={
                'missing': list(missing),
                'extra': list(extra),
            }
        )
```

#### 3.2.3 测试点生成器
```python
class TestType(Enum):
    SYNTAX_VALIDATION = "syntax_validation"
    MODULE_IMPORT = "module_import"
    FEATURE_CONDITION = "feature_condition"
    VERSION_COMPATIBILITY = "version_compatibility"
    MANDATORY_FIELD = "mandatory_field"
    DEFAULT_VALUE = "default_value"
    TYPE_VALIDATION = "type_validation"
    RANGE_CONSTRAINT = "range_constraint"
    PATTERN_CONSTRAINT = "pattern_constraint"
    ENUM_VALIDATION = "enum_validation"
    MUST_EXPRESSION = "must_expression"
    WHEN_CONDITION = "when_condition"
    CHOICE_CASE = "choice_case"
    GET_CONFIG = "get_config"
    EDIT_CONFIG = "edit_config"
    COPY_CONFIG = "copy_config"
    DELETE_CONFIG = "delete_config"
    LOCK_UNLOCK = "lock_unlock"
    COMMIT_DISCARD = "commit_discard"
    VALIDATE = "validate"
    RPC_VALIDATION = "rpc_validation"
    NOTIFICATION_VALIDATION = "notification_validation"
    RESTCONF_GET = "restconf_get"
    RESTCONF_POST = "restconf_post"
    RESTCONF_PUT = "restconf_put"
    RESTCONF_PATCH = "restconf_patch"
    RESTCONF_DELETE = "restconf_delete"
    YANG_PUSH_SUBSCRIPTION = "yang_push_subscription"
    CAPABILITY_NEGOTIATION = "capability_negotiation"
    NACM_AUTHORIZATION = "nacm_authorization"

@dataclass
class TestPoint:
    test_id: str
    test_name: str
    test_type: TestType
    yang_path: str
    test_description: str
    test_steps: List[str]
    expected_result: str
    severity: str
    auto_executable: bool
    rfc_reference: str = ""
```

#### 3.2.4 RESTCONF测试器
```python
class RESTCONFTester:
    """RESTCONF协议测试 (RFC 8040)"""
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.auth = (username, password)
        self.headers = {
            'Accept': 'application/yang-data+json',
            'Content-Type': 'application/yang-data+json',
        }
    
    def get(self, path: str) -> Dict:
        url = f"{self.base_url}/restconf/data/{path}"
        response = requests.get(url, auth=self.auth, headers=self.headers)
        return response.json()
    
    def post(self, path: str, data: Dict) -> Dict:
        url = f"{self.base_url}/restconf/data/{path}"
        response = requests.post(url, json=data, auth=self.auth, headers=self.headers)
        return response.json()
    
    def put(self, path: str, data: Dict) -> Dict:
        url = f"{self.base_url}/restconf/data/{path}"
        response = requests.put(url, json=data, auth=self.auth, headers=self.headers)
        return response.json()
    
    def patch(self, path: str, data: Dict) -> Dict:
        url = f"{self.base_url}/restconf/data/{path}"
        response = requests.patch(url, json=data, auth=self.auth, headers=self.headers)
        return response.json()
    
    def delete(self, path: str) -> Dict:
        url = f"{self.base_url}/restconf/data/{path}"
        response = requests.delete(url, auth=self.auth, headers=self.headers)
        return response.json()
    
    def yang_patch(self, path: str, patches: List[Dict]) -> Dict:
        url = f"{self.base_url}/restconf/data/{path}"
        data = {
            "ietf-yang-patch:yang-patch": {
                "patch-id": "patch-1",
                "comment": "Test patch",
                "patch": patches
            }
        }
        response = requests.patch(url, json=data, auth=self.auth, headers=self.headers)
        return response.json()
```

#### 3.2.5 YANG Push测试器
```python
class YANGPushTester:
    """YANG Push订阅测试 (RFC 8641)"""
    
    def create_subscription(self, client, stream: str, filter_path: str,
                           periodicity: int = None) -> str:
        subscription_rpc = f'''
        <establish-subscription xmlns="urn:ietf:params:xml:ns:yang:ietf-yang-push">
            <stream>{stream}</stream>
            <xpath-filter>{filter_path}</xpath-filter>
            <periodicity>{periodicity}</periodicity>
        </establish-subscription>
        '''
        response = client.rpc(subscription_rpc)
        return response.find('.//subscription-id').text
    
    def modify_subscription(self, client, subscription_id: str,
                          new_filter: str = None) -> bool:
        modify_rpc = f'''
        <modify-subscription xmlns="urn:ietf:params:xml:ns:yang:ietf-yang-push">
            <subscription-id>{subscription_id}</subscription-id>
            <xpath-filter>{new_filter}</xpath-filter>
        </modify-subscription>
        '''
        response = client.rpc(modify_rpc)
        return response.ok
    
    def terminate_subscription(self, client, subscription_id: str) -> bool:
        terminate_rpc = f'''
        <terminate-subscription xmlns="urn:ietf:params:xml:ns:yang:ietf-yang-push">
            <subscription-id>{subscription_id}</subscription-id>
        </terminate-subscription>
        '''
        response = client.rpc(terminate_rpc)
        return response.ok
```

#### 3.2.6 NETCONF客户端
```python
class NETCONFClient:
    def __init__(self, host: str, port: int = 830, 
                 username: str = None, password: str = None,
                 hostkey_verify: bool = False,
                 transport: str = 'ssh'):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.transport = transport
        self.hostkey_verify = hostkey_verify
        self.mgr = None
        
    def connect(self) -> bool:
        try:
            self.mgr = manager.connect(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                hostkey_verify=self.hostkey_verify,
                device_params={'name': 'default'},
            )
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def get_capabilities(self) -> Dict:
        if not self.mgr:
            raise RuntimeError("Not connected")
        capabilities = list(self.mgr.server_capabilities)
        parsed = {}
        for cap in capabilities:
            if ':' in cap:
                prefix, uri = cap.split(':', 1)
                parsed[uri] = {'prefix': prefix, 'full': cap}
        return {
            'server_capabilities': capabilities,
            'parsed': parsed,
            'session_id': self.mgr.session_id,
        }
    
    def get_config(self, source: str = 'running', filter=None) -> Any:
        if not self.mgr:
            raise RuntimeError("Not connected")
        return self.mgr.get_config(source=source, filter=filter)
    
    def get(self, filter=None) -> Any:
        if not self.mgr:
            raise RuntimeError("Not connected")
        return self.mgr.get(filter=filter)
    
    def edit_config(self, target: str, config: Any,
                   default_operation: str = 'merge',
                   operation: str = None) -> Any:
        if not self.mgr:
            raise RuntimeError("Not connected")
        return self.mgr.edit_config(
            target=target,
            config=config,
            default_operation=default_operation,
            operation=operation
        )
    
    def copy_config(self, source: str, target: str) -> Any:
        if not self.mgr:
            raise RuntimeError("Not connected")
        return self.mgr.copy_config(source=source, target=target)
    
    def delete_config(self, target: str) -> Any:
        if not self.mgr:
            raise RuntimeError("Not connected")
        return self.mgr.delete_config(target=target)
    
    def lock(self, target: str) -> Any:
        if not self.mgr:
            raise RuntimeError("Not connected")
        return self.mgr.lock(target=target)
    
    def unlock(self, target: str) -> Any:
        if not self.mgr:
            raise RuntimeError("Not connected")
        return self.mgr.unlock(target=target)
    
    def commit(self, confirmed: bool = False, timeout: int = None) -> Any:
        if not self.mgr:
            raise RuntimeError("Not connected")
        return self.mgr.commit(confirmed=confirmed, timeout=timeout)
    
    def discard_changes(self) -> Any:
        if not self.mgr:
            raise RuntimeError("Not connected")
        return self.mgr.discard_changes()
    
    def validate(self, source: str = 'candidate') -> Any:
        if not self.mgr:
            raise RuntimeError("Not connected")
        return self.mgr.validate(source=source)
    
    def rpc(self, rpc_xml: str) -> Any:
        if not self.mgr:
            raise RuntimeError("Not connected")
        return self.mgr.rpc(rpc_xml)
    
    def close_session(self) -> Any:
        if self.mgr:
            return self.mgr.close_session()
    
    def kill_session(self, session_id: int) -> Any:
        if not self.mgr:
            raise RuntimeError("Not connected")
        return self.mgr.kill_session(session_id=session_id)
```

### 3.3 YANG静态测试
```python
class YANGStaticValidator:
    def __init__(self):
        self.pyang_available = self._check_pyang()
        
    def _check_pyang(self) -> bool:
        try:
            subprocess.run(['pyang', '--version'], capture_output=True, check=True)
            return True
        except:
            return False
    
    def validate_syntax(self, yang_file: str) -> YANGValidationResult:
        if not self.pyang_available:
            return YANGValidationResult(
                is_valid=False,
                errors=[{"error": "pyang not available"}],
                warnings=[]
            )
        result = subprocess.run(
            ['pyang', '-Werror', yang_file],
            capture_output=True, text=True
        )
        errors = []
        warnings = []
        for line in result.stderr.split('\n'):
            if 'error:' in line.lower():
                errors.append({"error": line, "rfc_reference": "RFC 7950"})
            elif 'warning:' in line.lower():
                warnings.append({"warning": line})
        return YANGValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_imports(self, yang_file: str, search_path: List[str]) -> YANGValidationResult:
        result = subprocess.run(
            ['pyang', '-p', ':'.join(search_path), yang_file],
            capture_output=True, text=True
        )
        errors = []
        for line in result.stderr.split('\n'):
            if 'import' in line.lower() and 'error' in line.lower():
                errors.append({"error": line})
        return YANGValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=[]
        )
    
    def compare_schemas(self, yang_file1: str, yang_file2: str) -> Dict:
        result = subprocess.run(
            ['pyang', '-f', 'tree', yang_file1],
            capture_output=True, text=True
        )
        tree1 = result.stdout
        result = subprocess.run(
            ['pyang', '-f', 'tree', yang_file2],
            capture_output=True, text=True
        )
        tree2 = result.stdout
        return {
            'schema1_tree': tree1,
            'schema2_tree': tree2,
            'compatible': tree1 != tree2,
        }
    
    def generate_module_tree(self, yang_file: str) -> Dict:
        result = subprocess.run(
            ['pyang', '-f', 'tree', yang_file],
            capture_output=True, text=True
        )
        return {"tree": result.stdout}
```

---

## 4. 测试执行流程

### 4.1 完整测试流程
```
输入YANG文件 → 静态分析 → 能力协商 → 测试点生成 → 脚本生成 → 设备执行 → 报告生成
     ↓              ↓           ↓           ↓           ↓           ↓
  RFC 7950    RFC 8407    RFC 6241    RFC 6241    RFC 7950    RFC 8040
```

### 4.2 测试阶段
1. 输入验证: 接收YANG文件，验证格式 (RFC 7950)
2. 静态分析: 语法检查、依赖分析、版本比较 (RFC 8407, RFC 9195)
3. 能力协商: 获取设备能力，验证标准一致性 (RFC 6241)
4. 测试点生成: 遍历节点、提取约束、生成测试用例
5. 脚本生成: 框架搭建，用例代码生成
6. 设备执行: 建立会话、能力协商、执行测试
7. 报告生成: 统计结果，分析失败、输出报告

---

## 5. 测试用例覆盖矩阵

### 5.1 YANG语法/语义测试

| 测试类别 | 测试项 | 测试方法 | RFC参考 |
|---------|-------|---------|---------|
| 语法验证 | YANG 1.1语法正确性 | pyang验证 | RFC 7950 |
| 语法验证 | 模块导入完整性 | 依赖检查 | RFC 7950 Section 7 |
| 语义验证 | 数据类型正确性 | 类型测试 | RFC 7950 Section 9 |
| 语义验证 | 约束条件验证 | 边界测试 | RFC 7950 Section 9 |
| 版本兼容性 | YANG版本兼容性 | 版本比较 | RFC 9195, RFC 9261 |
| Feature测试 | 条件特性支持 | 特性检测 | RFC 7950 Section 7.20.1 |
| Uses/Augment | 组引用/扩展 | 结构验证 | RFC 7950 Section 7.17/7.18 |

### 5.2 NETCONF操作测试

| 测试类别 | 测试项 | 测试方法 | RFC参考 |
|---------|-------|---------|---------|
| 配置读取 | get-config (running) | 读取测试 | RFC 6241 Section 7.1 |
| 配置读取 | get-config (candidate) | 读取测试 | RFC 6241 Section 7.1 |
| 配置读取 | get (含状态数据) | 读取测试 | RFC 6241 Section 7.7 |
| 配置写入 | edit-config (merge) | 写入测试 | RFC 6241 Section 7.2 |
| 配置写入 | edit-config (replace) | 替换测试 | RFC 6241 Section 7.2 |
| 配置写入 | edit-config (create) | 创建测试 | RFC 6241 Section 7.2 |
| 配置写入 | edit-config (delete) | 删除测试 | RFC 6241 Section 7.2 |
| 配置复制 | copy-config | 复制测试 | RFC 6241 Section 7.3 |
| 配置删除 | delete-config | 删除测试 | RFC 6241 Section 7.4 |
| 事务管理 | commit | 提交测试 | RFC 6241 Section 7.4 |
| 事务管理 | commit (confirmed) | 确认提交 | RFC 6241 Section 7.4 |
| 事务管理 | discard-changes | 丢弃测试 | RFC 6241 Section 7.4 |
| 配置验证 | validate | 验证测试 | RFC 6241 Section 8.6 |
| 锁管理 | lock/unlock | 锁测试 | RFC 6241 Section 7.5/7.6 |
| 会话管理 | close-session | 关闭测试 | RFC 6241 Section 7.8 |
| 会话管理 | kill-session | 杀掉测试 | RFC 6241 Section 7.9 |

### 5.3 RESTCONF操作测试

| 测试类别 | 测试项 | 测试方法 | RFC参考 |
|---------|-------|---------|---------|
| 数据读取 | GET /data/{path} | HTTP GET | RFC 8040 Section 3.3 |
| 数据创建 | POST /data/{path} | HTTP POST | RFC 8040 Section 3.4 |
| 数据替换 | PUT /data/{path} | HTTP PUT | RFC 8040 Section 3.5 |
| 数据修改 | PATCH /data/{path} | HTTP PATCH | RFC 8040 Section 4.5 |
| 数据删除 | DELETE /data/{path} | HTTP DELETE | RFC 8040 Section 3.6 |
| YANG Patch | PATCH with yang-patch | 补丁测试 | RFC 8040 Section 4.6, RFC 8527 |
| 数据验证 | OPTIONS | 能力探测 | RFC 8040 |

### 5.4 YANG Push测试

| 测试类别 | 测试项 | 测试方法 | RFC参考 |
|---------|-------|---------|---------|
| 订阅管理 | establish-subscription | 创建订阅 | RFC 8641 Section 3.1 |
| 订阅管理 | modify-subscription | 修改订阅 | RFC 8641 Section 3.2 |
| 订阅管理 | terminate-subscription | 终止订阅 | RFC 8641 Section 3.3 |
| 订阅类型 | 定期推送 | period | RFC 8641 |
| 订阅类型 | 变更推送 | on-change | RFC 8641 |
| 通知接收 | push-update | 接收更新 | RFC 8641 Section 3.4 |

### 5.5 能力协商测试

| 测试类别 | 测试项 | 测试方法 | RFC参考 |
|---------|-------|---------|---------|
| 能力发现 | capability交换 | 能力获取 | RFC 6241 Section 8.1 |
| 能力验证 | :base:1 | 基础能力 | RFC 6241 |
| 能力验证 | :candidate | 候选配置 | RFC 6241 Section 8.3 |
| 能力验证 | :writable-running | running写入 | RFC 6241 Section 8.2 |
| 能力验证 | :validate | 配置验证 | RFC 6241 Section 8.6 |
| 能力验证 | :xpath | XPath过滤 | RFC 6241 Section 8.9 |
| 能力验证 | :with-defaults | 默认值处理 | RFC 6243 |

### 5.6 NACM访问控制测试

| 测试类别 | 测试项 | 测试方法 | RFC参考 |
|---------|-------|---------|---------|
| 认证测试 | 用户认证 | 身份验证 | RFC 6536 |
| 授权测试 | 读操作授权 | 权限验证 | RFC 6536 |
| 授权测试 | 写操作授权 | 权限验证 | RFC 6536 |
| 授权测试 | 执行操作授权 | 权限验证 | RFC 6536 |

---

## 6. 使用示例

### 6.1 命令行使用
```bash
# 基本用法
netconf-yang-test -y ietf-interfaces.yang -h 192.168.1.1 -u admin -p password

# 指定端口
netconf-yang-test -y ietf-interfaces.yang -h 192.168.1.1 --port 830

# 生成脚本不执行
netconf-yang-test -y ietf-interfaces.yang --generate-only

# 执行特定测试
netconf-yang-test -y ietf-interfaces.yang -t mandatory,type,enum

# 生成报告
netconf-yang-test -y ietf-interfaces.yang --report-format html
```

### 6.2 Python API使用
```python
from yang_test_system import YANGTestSystem

# 初始化测试系统
test_system = YANGTestSystem(
    yang_file='ietf-interfaces.yang',
    device_host='192.168.1.1',
    device_port=830,
    username='admin',
    password='password'
)

# 执行测试
results = test_system.run_tests()

# 生成报告
test_system.generate_report(format='html')
```

---

## 7. 依赖环境

### 7.1 Python依赖
- ncclient >= 0.6.14
- pyang >= 2.5.0
- pytest >= 7.0.0
- jinja2 >= 3.0.0
- paramiko >= 2.10.0

### 7.2 系统依赖
- Python 3.8+
- OpenSSH (for NETCONF over SSH)

---

## 8. 总结

本方案提供了一个完整的NETCONF/YANG测试系统v2.0，能够：
1. 自动解析YANG 1.1文件并提取测试点
2. 支持静态分析和动态执行测试
3. 生成可执行的Python测试脚本
4. 提供详细的测试报告
5. 支持RESTCONF协议测试
6. 支持YANG Push订阅测试
7. 支持能力协商验证
8. 提供NACM访问控制测试

系统设计遵循模块化原则，便于扩展和维护。

主要更新v2.0:
- 全面支持RFC 6241/RFC 7950等现行标准
- 新增RESTCONF测试模块
- 新增YANG Push测试模块
- 新增能力协商验证
- 扩展测试覆盖范围
