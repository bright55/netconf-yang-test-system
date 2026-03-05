# NETCONF/YANG Test System

Python实现基于RFC 6241/RFC 7950标准的NETCONF/YANG测试系统

## 功能特性

- YANG 1.1文件解析与静态分析
- 自动测试点生成
- NETCONF协议操作测试
- RESTCONF协议测试
- YANG Push订阅测试
- 能力协商验证
- 测试报告生成

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 命令行使用

```bash
# 基本测试
netconf-yang-test -y ietf-interfaces.yang -h 192.168.1.1 -u admin -p password

# 生成脚本不执行
netconf-yang-test -y ietf-interfaces.yang --generate-only

# 指定测试类型
netconf-yang-test -y ietf-interfaces.yang -t mandatory,type,enum

# 生成HTML报告
netconf-yang-test -y ietf-interfaces.yang --report-format html
```

### Python API使用

```python
from yang_test_system import YANGTestSystem

test_system = YANGTestSystem(
    yang_file='ietf-interfaces.yang',
    device_host='192.168.1.1',
    device_port=830,
    username='admin',
    password='password'
)

results = test_system.run_tests()
test_system.generate_report(format='html')
```

## 项目结构

```
netconf-yang-test-system/
├── src/yang_test_system/    # 核心源代码
├── tests/                   # 测试用例
├── yang_modules/           # YANG模块文件
├── examples/               # 示例配置
└── docs/                   # 文档
```

## 依赖

- ncclient >= 0.6.14
- pyang >= 2.5.0
- pytest >= 7.0.0
- jinja2 >= 3.0.0
- paramiko >= 2.10.0
- requests >= 2.28.0

## 参考标准

- RFC 6241 - NETCONF
- RFC 7950 - YANG 1.1
- RFC 8040 - RESTCONF
- RFC 8641 - YANG Push
