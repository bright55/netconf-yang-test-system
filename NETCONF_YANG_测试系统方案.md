# NETCONF/YANG 测试系统方案

## 文档信息
- 版本: v1.0
- 日期: 2026-03-03
- 作者: AI Assistant

---

## 1. 概述

### 1.1 背景
随着网络设备自动化配置管理需求的增长，NETCONF和YANG作为下一代网络管理协议标准已成为行业主流。但同时也带来了测试挑战：
- YANG模型复杂性高，手工测试效率低
- 不同厂商YANG模型差异大
- 配置一致性验证困难

### 1.2 目标
1. 自动化测试点生成 - 从YANG文件自动提取可测试的数据节点和操作
2. 静态分析 - YANG文件语法、依赖、一致性验证
3. 功能验证 - NETCONF协议操作的实际执行验证
4. 可执行脚本生成 - 产出可直接运行的Python测试脚本
5. 测试报告生成 - 统一的测试结果输出

---

## 2. NETCONF/YANG协议深入理解

### 2.1 NETCONF核心能力集(RFC 6243)

| 能力标识 | 描述 | 重要性 |
|---------|------|-------|
| :base:1 | 基础NETCONF能力 | 必需 |
| :writable-running | 写入running配置 | 核心 |
| :candidate | 候选配置支持 | 核心 |
| :confirmed-commit | 确认提交 | 可选 |
| :validate | 配置验证 | 重要 |
| :xpath | XPath过滤 | 重要 |

### 2.2 NETCONF核心操作

```xml
<!-- 获取配置 -->
<get-config>
    <filter type="xpath" select="/interfaces/interface[name='eth0']"/>
</get-config>

<!-- 获取运行状态 -->
<get>
    <filter type="xpath"/>
</get>

<!-- 修改配置 -->
<edit-config>
    <target><running/></target>
    <config>
        <interfaces>
            <interface>
                <name>eth0</name>
                <description>Test</description>
            </interface>
        </interfaces>
    </config>
</edit-config>

<!-- 删除配置 -->
<edit-config>
    <target><running/></target>
    <config>
        <interfaces xmlns="http://example.com">
            <operation>delete</operation>
        </interfaces>
    </config>
</edit-config>

<!-- 提交配置 -->
<commit/>
<discard-changes/>
```

### 2.3 YANG数据建模

```yang
module example-interface {
    namespace "http://example.com/interfaces";
    prefix exif;

    revision 2024-01-01 {
        description "Initial revision";
    }

    typedef interface-status {
        type enumeration {
            enum up;
            enum down;
            enum testing;
        }
    }

    container interfaces {
        list interface {
            key "name";
            
            leaf name {
                type string;
                mandatory true;
            }
            
            leaf description {
                type string;
                default "";
            }
            
            leaf enabled {
                type boolean;
                default true;
            }
            
            leaf mtu {
                type uint16 {
                    range "68..9000";
                }
            }
            
            leaf oper-status {
                type interface-status;
                config false;
            }
        }
    }

    rpc reboot {
        input {
            leaf delay {
                type uint32;
                default 0;
            }
        }
        output {
            leaf status {
                type string;
            }
        }
    }
}
```

---

## 3. 测试系统架构

### 3.1 系统总体架构

```
+------------------------------------------------------------+
|                    NETCONF/YANG 测试系统                      |
+------------------------------------------------------------+
|  输入层: CLI/Web UI/REST API                               |
+------------------------------------------------------------+
|  核心引擎:                                                  |
|  +--------+  +--------+  +--------+  +--------+              |
|  | YANG   |  | 测试点 |  | 脚本   |  | 测试   |              |
|  | 解析器 |  | 生成器 |  | 生成器 |  | 执行器 |              |
|  +--------+  +--------+  +--------+  +--------+              |
+------------------------------------------------------------+
|  依赖层: ncclient, pyang, paramiko, pytest                  |
+------------------------------------------------------------+
```

### 3.2 核心模块设计

#### 3.2.1 YANG解析器
```python
class YANGParser:
    def __init__(self, yang_file_path: str):
        self.yang_file_path = yang_file_path
        
    def parse(self) -> Dict[str, Any]:
        # 1. 基础语法检查
        # 2. 提取所有声明
        # 3. 构建数据模型
        pass
    
    def extract_testable_nodes(self) -> List[Dict]:
        nodes = []
        for node in self.data_nodes:
            if self._is_testable(node):
                nodes.append({
                    'path': node.path,
                    'type': node.type,
                    'constraints': self._extract_constraints(node),
                })
        return nodes
    
    def _extract_constraints(self, node) -> Dict:
        constraints = {}
        if hasattr(node, 'range'): constraints['range'] = node.range
        if hasattr(node, 'pattern'): constraints['pattern'] = node.pattern
        if hasattr(node, 'enum'): constraints['enum'] = node.enum
        if hasattr(node, 'default'): constraints['default'] = node.default
        if hasattr(node, 'must'): constraints['must'] = node.must
        return constraints
```

#### 3.2.2 测试点生成器
```python
class TestType(Enum):
    SYNTAX_VALIDATION = "syntax_validation"
    MANDATORY_FIELD = "mandatory_field"
    DEFAULT_VALUE = "default_value"
    TYPE_VALIDATION = "type_validation"
    RANGE_CONSTRAINT = "range_constraint"
    PATTERN_CONSTRAINT = "pattern_constraint"
    ENUM_VALIDATION = "enum_validation"
    MUST_EXPRESSION = "must_expression"
    OPERATION_TEST = "operation_test"
    RPC_VALIDATION = "rpc_validation"
    NOTIFICATION_VALIDATION = "notification_validation"

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

class TestPointGenerator:
    def __init__(self, yang_module_info: Dict):
        self.yang_module = yang_module_info
        
    def generate_all_test_points(self) -> List[TestPoint]:
        test_points = []
        test_points.extend(self._generate_syntax_test_points())
        test_points.extend(self._generate_data_node_test_points())
        test_points.extend(self._generate_rpc_test_points())
        test_points.extend(self._generate_notification_test_points())
        return test_points
    
    def _generate_data_node_test_points(self) -> List[TestPoint]:
        test_points = []
        for node in self.yang_module.get('data_nodes', []):
            node_path = node['path']
            is_mandatory = node.get('mandatory', False)
            is_config = node.get('config', True)
            constraints = node.get('constraints', {})
            
            # 必填字段测试
            if is_mandatory:
                test_points.append(TestPoint(
                    test_id=f"MANDATORY_{self._path_to_id(node_path)}",
                    test_name=f"必填字段验证 - {node_path}",
                    test_type=TestType.MANDATORY_FIELD,
                    yang_path=node_path,
                    test_description=f"验证{node_path}必填字段处理",
                    test_steps=[
                        f"1. 尝试创建不包含{node_path}的配置",
                        "2. 发送edit-config RPC",
                        "3. 验证返回错误响应"
                    ],
                    expected_result="设备返回mandatory-field-missing错误",
                    severity="critical",
                    auto_executable=True
                ))
            
            # 默认值测试
            if 'default' in node and is_config:
                test_points.append(TestPoint(
                    test_id=f"DEFAULT_{self._path_to_id(node_path)}",
                    test_name=f"默认值验证 - {node_path}",
                    test_type=TestType.DEFAULT_VALUE,
                    yang_path=node_path,
                    test_description=f"验证默认值{node['default']}正确应用",
                    test_steps=[
                        "1. 创建不包含该字段的配置",
                        "2. 获取配置验证默认值",
                        "3. 验证默认值与YANG定义一致"
                    ],
                    expected_result="默认值正确设置",
                    severity="major",
                    auto_executable=True
                ))
            
            # 类型验证测试
            test_points.append(TestPoint(
                test_id=f"TYPE_{self._path_to_id(node_path)}",
                test_name=f"类型验证 - {node_path}",
                test_type=TestType.TYPE_VALIDATION,
                yang_path=node_path,
                test_description=f"验证类型{node.get('type')}正确处理",
                test_steps=[
                    "1. 构造有效类型值",
                    "2. 构造无效类型值",
                    "3. 验证正确行为"
                ],
                expected_result="正确类型接受，错误类型拒绝",
                severity="critical",
                auto_executable=True
            ))
            
            # 范围约束测试
            if 'range' in constraints:
                test_points.append(TestPoint(
                    test_id=f"RANGE_{self._path_to_id(node_path)}",
                    test_name=f"范围约束测试 - {node_path}",
                    test_type=TestType.RANGE_CONSTRAINT,
                    yang_path=node_path,
                    test_description=f"验证范围约束{constraints['range']}",
                    test_steps=[
                        "1. 测试边界值",
                        "2. 测试边界外值",
                        "3. 验证正确行为"
                    ],
                    expected_result="范围内接受，范围外拒绝",
                    severity="critical",
                    auto_executable=True
                ))
            
            # 枚举值测试
            if 'enum' in constraints:
                test_points.append(TestPoint(
                    test_id=f"ENUM_{self._path_to_id(node_path)}",
                    test_name=f"枚举值测试 - {node_path}",
                    test_type=TestType.ENUM_VALIDATION,
                    yang_path=node_path,
                    test_description=f"验证枚举值{constraints['enum']}",
                    test_steps=[
                        "1. 逐个测试枚举值",
                        "2. 测试无效枚举值",
                        "3. 验证正确行为"
                    ],
                    expected_result="有效枚举接受，无效枚举拒绝",
                    severity="critical",
                    auto_executable=True
                ))
            
            # Must表达式测试
            if 'must' in constraints:
                test_points.append(TestPoint(
                    test_id=f"MUST_{self._path_to_id(node_path)}",
                    test_name=f"Must表达式测试 - {node_path}",
                    test_type=TestType.MUST_EXPRESSION,
                    yang_path=node_path,
                    test_description=f"验证must约束{constraints['must']}",
                    test_steps=[
                        "1. 配置满足must条件",
                        "2. 配置不满足must条件",
                        "3. 验证正确行为"
                    ],
                    expected_result="满足接受，不满足拒绝",
                    severity="critical",
                    auto_executable=True
                ))
            
            # 配置vs状态测试
            if is_config:
                test_points.append(TestPoint(
                    test_id=f"CONFIG_{self._path_to_id(node_path)}",
                    test_name=f"配置读写测试 - {node_path}",
                    test_type=TestType.OPERATION_TEST,
                    yang_path=node_path,
                    test_description=f"验证get-config和edit-config操作",
                    test_steps=[
                        "1. 使用edit-config设置值",
                        "2. 使用get-config验证值",
                        "3. 验证配置持久化"
                    ],
                    expected_result="配置操作成功",
                    severity="critical",
                    auto_executable=True
                ))
            else:
                test_points.append(TestPoint(
                    test_id=f"STATUS_{self._path_to_id(node_path)}",
                    test_name=f"状态只读测试 - {node_path}",
                    test_type=TestType.OPERATION_TEST,
                    yang_path=node_path,
                    test_description=f"验证只读状态节点",
                    test_steps=[
                        "1. 尝试edit-config修改",
                        "2. 验证返回错误",
                        "3. 使用get获取状态"
                    ],
                    expected_result="edit拒绝，get返回状态",
                    severity="major",
                    auto_executable=True
                ))
        
        return test_points
    
    def _generate_rpc_test_points(self) -> List[TestPoint]:
        test_points = []
        for rpc in self.yang_module.get('rpc_methods', []):
            rpc_name = rpc['name']
            
            # RPC输入验证
            for input_param in rpc.get('input', []):
                test_points.append(TestPoint(
                    test_id=f"RPC_INPUT_{self._path_to_id(rpc_name)}_{self._path_to_id(input_param['name'])}",
                    test_name=f"RPC输入验证 - {rpc_name}/{input_param['name']}",
                    test_type=TestType.RPC_VALIDATION,
                    yang_path=f"{rpc_name}/input/{input_param['name']}",
                    test_description=f"验证RPC输入参数{input_param['name']}",
                    test_steps=[
                        f"1. 调用{rpc_name}不包含参数",
                        "2. 验证必填参数检查",
                        "3. 测试参数类型验证"
                    ],
                    expected_result="必填参数缺失返回错误",
                    severity="critical",
                    auto_executable=True
                ))
            
            # RPC输出验证
            test_points.append(TestPoint(
                test_id=f"RPC_OUTPUT_{self._path_to_id(rpc_name)}",
                test_name=f"RPC输出验证 - {rpc_name}",
                test_type=TestType.RPC_VALIDATION,
                yang_path=f"{rpc_name}/output",
                test_description=f"验证RPC输出结构",
                test_steps=[
                    f"1. 调用{rpc_name}",
                    "2. 验证输出字段",
                    "3. 验证字段类型"
                ],
                expected_result="输出符合YANG定义",
                severity="major",
                auto_executable=True
            ))
            
            # RPC成功执行
            test_points.append(TestPoint(
                test_id=f"RPC_SUCCESS_{self._path_to_id(rpc_name)}",
                test_name=f"RPC成功执行 - {rpc_name}",
                test_type=TestType.RPC_VALIDATION,
                yang_path=rpc_name,
                test_description=f"验证RPC正常执行",
                test_steps=[
                    f"1. 调用{rpc_name}",
                    "2. 验证ok响应",
                    "3. 验证预期效果"
                ],
                expected_result="RPC执行成功",
                severity="critical",
                auto_executable=True
            ))
        
        return test_points
    
    def _path_to_id(self, path: str) -> str:
        return path.replace('/', '_').replace('-', '_')
```

#### 3.2.3 脚本生成器
```python
class ScriptGenerator:
    def __init__(self, template_dir: str = None):
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir or './templates')
        )
        
    def generate_test_script(self, test_points: List[Dict], device_info: Dict) -> str:
        template = self.env.get_template('netconf_test.j2')
        return template.render(
            test_points=test_points,
            device_info=device_info,
            generation_time=datetime.now().isoformat()
        )
    
    def _generate_operation_test(self, test_point: Dict) -> str:
        yang_path = test_point['yang_path']
        return f'''
    def test_{test_point["test_id"].lower()}(self):
        """{test_point["test_name"]}"""
        
        config_data = {self._build_config_data(yang_path)}
        
        try:
            # 1. edit-config设置配置
            result = self.netconf_client.edit_config(
                target='running',
                config=config_data,
                default_operation='merge'
            )
            self.assertEqual(result.ok, True)
            
            # 2. get-config验证
            response = self.netconf_client.get_config(
                source='running',
                filter=('{yang_path}')
            )
            self._verify_value(response, '{yang_path}', config_data)
            
        except NCError as e:
            self.fail(f"NETCONF failed: {{e}}")
'''
    
    def _generate_rpc_test(self, test_point: Dict) -> str:
        yang_path = test_point['yang_path']
        rpc_name = yang_path.split('/')[0]
        return f'''
    def test_{test_point["test_id"].lower()}(self):
        """{test_point["test_name"]}"""
        
        try:
            result = self.netconf_client.rpc(
                '''{rpc_name}'''
            )
            self.assertEqual(result.ok, True)
            
        except NCError as e:
            self.fail(f"RPC failed: {{e}}")
'''
```

#### 3.2.4 NETCONF客户端
```python
class NETCONFClient:
    def __init__(self, host: str, port: int = 830, 
                 username: str = None, password: str = None,
                 hostkey_verify: bool = False):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
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
        return {
            'server_capabilities': list(self.mgr.server_capabilities),
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
                   default_operation: str = 'merge') -> Any:
        if not self.mgr:
            raise RuntimeError("Not connected")
        return self.mgr.edit_config(
            target=target,
            config=config,
            default_operation=default_operation
        )
    
    def commit(self, confirmed: bool = False, timeout: int = None) -> Any:
        if not self.mgr:
            raise RuntimeError("Not connected")
        return self.mgr.commit(confirmed=confirmed, timeout=timeout)
    
    def discard_changes(self) -> Any:
        if not self.mgr:
            raise RuntimeError("Not connected")
        return self.mgr.discard_changes()
    
    def lock(self, target: str) -> Any:
        if not self.mgr:
            raise RuntimeError("Not connected")
        return self.mgr.lock(target=target)
    
    def unlock(self, target: str) -> Any:
        if not self.mgr:
            raise RuntimeError("Not connected")
        return self.mgr.unlock(target=target)
    
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
                errors.append({"error": line})
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
输入YANG文件 → 静态分析 → 测试点生成 → 脚本生成 → 设备执行 → 报告生成
```

### 4.2 测试阶段
1. **输入验证**: 接收YANG文件，验证格式
2. **静态分析**: 语法检查、依赖分析
3. **测试点生成**: 遍历节点、提取约束
4. **脚本生成**: 框架搭建、用例代码生成
5. **设备执行**: 建立会话、能力协商、执行测试
6. **报告生成**: 统计结果、分析失败、输出报告

---

## 5. 测试用例覆盖矩阵

| 测试类别 | 测试项 | 测试方法 |
|---------|-------|---------|
| 语法验证 | YANG语法正确性 | pyang验证 |
| 语法验证 | 模块导入完整性 | 依赖检查 |
| 语义验证 | 数据类型正确性 | 类型测试 |
| 语义验证 | 约束条件验证 | 边界测试 |
| 功能验证 | get-config操作 | 读取测试 |
| 功能验证 | edit-config操作 | 写入测试 |
| 功能验证 | commit/discard | 事务测试 |
| 功能验证 | lock/unlock | 锁测试 |
| 功能验证 | validate | 验证测试 |
| RPC测试 | RPC输入验证 | 参数测试 |
| RPC测试 | RPC输出验证 | 响应测试 |
| 通知测试 | 通知订阅 | 事件测试 |

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

本方案提供了一个完整的NETCONF/YANG测试系统，能够：
1. 自动解析YANG文件并提取测试点
2. 支持静态分析和动态执行测试
3. 生成可执行的Python测试脚本
4. 提供详细的测试报告

系统设计遵循模块化原则，便于扩展和维护。
