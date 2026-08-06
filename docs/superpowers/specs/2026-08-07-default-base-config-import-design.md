# 默认基础配置路径导入修复设计

## 目标

统一 `DEFAULT_BASE_CONFIG_PATH` 的导入来源，使所有使用旧下载基础配置的模块都直接依赖其权威定义 `backend.src.base.default`，消除 `backend.src.base.config` 删除该常量后产生的导入错误。

## 范围

本次只修改以下模块中的常量导入：

- `backend/src/base/downloader.py`
- `backend/src/platform/douyin/douyin_config.py`
- `backend/src/platform/douyin/douyin_live_config.py`
- `backend/src/platform/douyin/douyin_live_downloader.py`
- `backend/src/platform/douyin/douyin_post_config.py`
- `backend/src/platform/douyin/douyin_post_downloader.py`

每个模块继续从原模块导入类或函数，但改为直接使用：

```python
from backend.src.base.default import DEFAULT_BASE_CONFIG_PATH
```

不修改：

- 常量值 `config/base_config.yml`。
- `backend/src/base/login.py` 中指向登录配置的同名局部常量。
- 下载、平台分发或 Flask 的运行行为。
- YAML 系统配置的加载和消费逻辑。

## 依赖关系

```text
backend.src.base.default.DEFAULT_BASE_CONFIG_PATH
  ├── base.downloader
  ├── douyin.douyin_config
  ├── douyin.douyin_live_config
  ├── douyin.douyin_live_downloader
  ├── douyin.douyin_post_config
  └── douyin.douyin_post_downloader
```

模块不再通过 `base.config`、`base.downloader` 或其他斗音配置模块间接转发该常量。

## 错误处理

本次不新增运行时错误处理。修复目标是让相关模块导入时不再产生 `cannot import name 'DEFAULT_BASE_CONFIG_PATH'`。

## 测试

聚焦测试使用 Python AST 解析上述六个模块，验证每个模块都直接从 `backend.src.base.default` 导入 `DEFAULT_BASE_CONFIG_PATH`。该测试在当前代码上会因错误导入来源而失败，修复后应通过；随后使用 `compileall` 验证语法。

本步骤不执行六个模块的运行时导入，因为其中存在与本目标无关的既有导入副作用和旧式顶层依赖。这些问题不在本次修复范围内。

完成本步骤后停止，不处理 Flask 初始化顺序问题。
