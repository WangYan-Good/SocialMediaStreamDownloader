# 📝开发日志

本项目开发期间，使用该日志用于记录开发过程中的设计思考和问题解决过程。

## 💡架构设计思考

### 1. 关于数据库

1. 数据库在项目开发中的模型

&emsp;数据库在项目开发中应该属于单例模式，即任何一个项目，对于持久化的存储，应该只有一个全局对象，通常的面向对象开发方法，即通过创建一个新的对象进行操作，在这里可能不适用，因为对整个项目而言，数据库其实只有一个，就整个项目而言，它应当只有一个实例，所有的函数方法调用连接到的应当都是同一个数据库对象。

2. 单例模型会不会有并发执行情况下的性能瓶颈？

&emsp;数据库表的模型以及每个数据

3. 数据库和数据库表的关系以及代码中如何表示？

&emsp;本项目开发中，关系型数据库和数据库表的关系应该是**组合关系**，即数据库表的集合组成了数据库，数据库 = 数据库表的集合，当双方任意一方不存在时，两者都无法独立存在。所以针对代码的设计，不能表示为简单的子类和父类，应该设计为两个类，一个类为数据库类，即`database`，另一个类为数据库表类`db_table`。两者的关系应当为以下 UML 的模型。
```plantUML
@startuml
abstract class database
abstract class db_table_1
abstract class db_table_2
abstract class db_table_x

database *-- db_table_1
database *-- db_table_2
database *-- db_table_x

@enduml
```

### 2. 数据库和数据库表的代码设计

`逻辑结构`
&emsp;本项目开发中，数据库和数据库表之间属于 1:n 的关系，即一对多的关系，通常一个数据库需要对应多个表。而上层服务需要先连接数据库，才可以通过调用数据库对应的接口来更新数据库表，即他们之间构成了`上层服务-数据库-数据库表` 的层级关系，所有服务都需要通过数据库这一层来访问和修改数据库表的内容。因此在架构上，数据库这一层应当离应用层更近，而所有的数据库表的更新应当在数据库的下一层级。

`代码结构`
&emsp;从逻辑层面来看，数据库需要提供所有的表级接口供上层服务来调用，这会引出一个问题，如果在数据库这一级提供表级别的接口，那么意味着所有表级别的代码改动都会影响数据库级别的代码改动，例如数据库 DB 目前有三个表 a，b，c，数据库当前提供了以下三个接口来访问 a，b，c 三个表
- get_table_a()
- get_table_b()
- get_table_c()

此时，如果数据库中需要加一个 d 表，那么必然会影响数据库层的代码，则按照当下的逻辑，需要添加一个额外的接口
- get_table_d()

这种行为似乎看起来是很正常的，但是在实际的开发中，这种结构存在着强耦合，如果在企业项目中，恰好这这个块又由不同的开发者负责维护，无疑会增加沟通成本。因此针对这种问题，建议`透明化`数据库这一层，即弱化数据库操作的存在感，由数据库表级别提供接口，针对数据库的操作，比如连接和关闭连接，可以在所有的数据库表级别完成，比如，上层应用其实之关心需要修改哪个数据库表中的哪个内容，而对数据库的连接以及连接哪个数据库其实不关心，这些细节是可以透明化的操作。因此从代码层面来看，低耦合的实现方式是：
- 数据库表级别显示提供对应的属性和接口
- 针对数据库的操作细节对上层应用隐藏，具体的连接关闭操作由每个表实现，由于数据库是单例模式，因此所有表通过异步来完成数据库的连接和关闭时可行的。
- 上层应用直接 include / import 对应数据库表提供的接口来实现业务数据的更新

## 🐞问题与解决方案

### 1. 项目中单例模型数据库的调用问题

`问题1`：
针对项目中的单例模型，如数据库，在多线程的并发程序执行中，往往同一时刻会有多个线程同时访问该组件，针对这种情况的处理，尤其涉及到连接操作， 增删改查，关闭操作等，多个线程之间容易造成冲突。

例如：当前有线程 A 和线程 B 需要进行访问数据库，正常情况下，一个线程如果需要访问数据库，那么需要进行以下三步:
- 连接数据库
- 操作数据库
- 关闭数据库

此时线程 A B 同时访问数据库，可能出现以下问题:

A 线程先执行，成功进行了数据库的连接，此时 B 线程也开始执行连接数据库操作，由于数据库属于单例模型，对于持久层（数据库）来说，线程 A 和线程 B 都是来自于应用层的访问，对数据库来说，线程 A 和线程 B 的操作只是应用层的两次操作，正常的操作顺序应该是：
- 连接数据库
- A 操作数据库
- B 操作数据库
- 关闭数据库连接

然而实际的操作是：
1. A 发起数据库连接
2. B 也发起数据库连接
3. A 操作数据库
4. B 操作数据库
5. A 关闭数据库连接
6. B 关闭数据库连接

以上操作中数据库被连接 2 次和关闭 2 次，不考虑持久层端的异常处理和多连接实例机制和的情况下，就单例模型而言，这可能会带来异常。

`问题2`：
不考虑以上问题的异常情况，假设线程 A 和线程 B 均成功连接到数据库，当 A 和 B 操作如果互斥的情况下，有可能会造成新的问题，如 A 需要读取数据 c，而 B 需要更新数据 c，此时可能会造成读脏数据的问题。

`设计构想与解决方案`：
针对以上问题，针对所有数据库的操作提供代理角色，即提供统一接口提供给上层调用，所有上层针对数据的操作只能通过该接口来进行持久层（数据库）的操作。这样可以在持久层接口层面针对不同操作来做特别处理。

1. 针对同一时刻的读操作的处理
理论上所有的读操作可以同时并行执行，不会存在读脏数据的情况，需要考虑的情况如负载，是否需要限制同一时刻的最大操作数量上限可能需要考虑。

2. 针对同一时刻的写操作
  - 不同表操作
  不同的表操作理论上允许并行，需要考虑不同表之间是否存在耦合和依赖关系，是否存在触发事件导致相互依赖的情况需要考虑。如果存在这些依赖则属于下列的情况，针对本条则不适用。

  - 相同表操作
  如果不同的操作线程 A 和线程 B 涉及到了相同的数据库表 c，此处的操作包括`直接操作`和`间接操作`，其中直接操作可理解为上层操作中指定需要往该数据库表 c 中更新数据，而间接操作可理解为上层操作可能需要更新其他的数据库表 d，然而数据库表 d 的更新会触发数据库表 c 的变化，从而间接操作了数据库表 c，因此造成了线程 A 和 线程 B 的操作冲突。

  针对以上的情况，解决方案是每次只允许 1 个操作，当本次操作完成后，才会允许其他操作进入。

3. 针对同一时刻的读写操作
#2 中的解决方案同样适用于本案例，当操作冲突时，同一时刻只允许一个操作。

`方案评估`：
当持久层的吞吐率过大时，数据库操作可能会成为一个性能瓶颈。

### 2. 关于数据库的连接问题

`问题1`
上层服务每次操作完数据库前后，每次需要创建连接之后才能对数据库执行操作。然而频繁的建立连接和关闭连接会额外产生大量开销。如果使用同一个连接，则会产生另外的问题，如程序异常中断，连接无法关闭；多个可并发执行的数据库操作，无法在同一个连接中同时操作 cursor()，从而引起数据库的访问冲突。如何避免这种情况？

`设计构想与解决方案`：
使用数据库连接池

### 3. 关于数据库的读写互斥加锁问题

`问题1`
在数据库表读操作时，需要知道当前是否有写操作正在执行，如果没有写操作则可以正常读取。所以读操作不应该加锁，而写操作则需要加锁，并且当前如果存在

`设计构想与解决方案`：
读操作并行，写操作互斥，每一个读写操作都被视为原子操作，不可中断
当请求写操作时，需将正在进行的读操作完成方才可开始执行写操作，后续进入的读操作进入就绪状态，等待写操作完成再次被调度

- 读操作 <- non-block -> 读操作
- 读操作   <- block ->   写操作
- 写操作   <- block ->   写操作

数据库层面锁机制
`事务隔离级别设置`

`显式锁语句`
- 行级锁（InnoDB引擎）
- 表级锁

应用层锁机制
`使用线程锁（适用于单机应用）`
`使用分布式锁（适用于多机/集群环境）`

`问题2`
python 中如何通过 `threading.Lock()` 实现表级别的互斥操作，即
- 读操作之间不互斥
- 读写操作互斥
- 写操作之间互斥

### 4. 数据库表插入记录时的索引问题

#### 4.1 插入数据
数据库表在创建时，针对有自动索引的表，在插入时，需要忽略 `index` 这一列，有数据库自身完成自加行为。

#### 4.2 关于 auto_increment 自增指定数值问题
摘选自 [MySQL里AUTO_INCREMENT表里插入0值的问题 - 简书](https://www.jianshu.com/p/7fa6330e9ebc)
在mysql中对于设置了自增属性auto_increment的字段自增值是从1开始的，写入0会被当做null值处理从而写入当前最大值的下一个值（即表示定义中auto_increment的值）。
如果需要修改自增值的起始位置可以通过 " alter table table_name(表名) auto_increment=xxxx; "进行修改，但是这个值必须比当前表内数据的最大值要大，否则修改不会生效。
如果需要修改自增值从0开始而不是从1开始，可以设置线程级别的参数" set sql_mode='NO_AUTO_VALUE_ON_ZERO' ; "来实现 ( 可小写 )
```sql
set sql_mode='no_auto_value_on_zero';
CREATE TABLE auth_function (
  id BIGINT(20) AUTO_INCREMENT NOT NULL,
  name varchar(64) NOT NULL,
  parent_id BIGINT(20) NOT NULL,
  url varchar(128) NOT NULL,
  serial_num int NOT NULL,
  accordion int NOT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
```

---

## 🚀 v0.8.0 开发记录（2026.04.14）

### 1. 数据库连接池实现

`背景`
在 v0.7.2 及之前版本中，数据库连接采用每次请求创建新连接的模式：
```python
def get_db_connector(self):
    self.__connector = pymysql.connect(host=..., user=..., passwd=..., db=...)
    return self.__connector
```
这种模式存在以下问题：
1. **连接泄露**：异常时未执行 `close()`，连接未归还
2. **性能瓶颈**：频繁创建/销毁连接产生大量开销
3. **并发限制**：高并发时可能耗尽 MySQL 最大连接数

`解决方案`
引入 `DBUtils PooledDB` 连接池管理数据库连接。

`核心设计`
```python
__pool_config = {
    'mincached': 2,       # 初始化2个空闲连接
    'maxcached': 10,      # 最多保持10个空闲连接
    'maxshared': 20,      # 最多20个共享连接
    'maxconnections': 30, # 最大30个连接
    'blocking': True,     # 超限时阻塞等待
    'maxusage': 1000,     # 单连接最多使用1000次
    'ping': 1,            # 失效时自动重连
}
```

`使用模式`
```python
# 新方式：自动管理连接生命周期
with db.get_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute(sql, params)
# 连接自动归还，异常时也会归还
```

`关键技术点`
1. **线程安全单例**：使用双检锁（Double-Check Locking）避免多线程创建多个连接池
2. **上下文管理器**：`@contextmanager` 装饰器实现 `get_connection()`，自动处理连接的获取和归还
3. **异常处理**：异常时自动 `rollback()` 并归还连接，避免连接泄露
4. **向后兼容**：保留原有 `get_db_connector()` 方法（标记为废弃），避免影响现有代码

### 2. API 错误处理改进

`背景`
v0.7.2 之前，Flask POST 端点错误处理存在以下问题：
```python
@app.route('/', methods=['POST'])
def process_request():
    try:
        platform_dispatcher.dispatch(request.json)
    except Exception as e:
        print(f"ERROR: {e}")  # 仅打印到控制台
        return jsonify({"message": "request 处理失败"}), 500
```

问题：
1. 未校验请求格式（可能不是 JSON）
2. 未校验必需字段（`urls` 可能为空）
3. 异常信息仅打印，未记录到日志
4. 返回信息过于笼统，无法区分客户端错误和服务器错误

`解决方案`
```python
@app.route('/', methods=['POST'])
def process_request():
    # 1. 校验请求格式
    if not request.is_json:
        return jsonify({"status": "error", "message": "...", "code": 400}), 400

    # 2. 校验必需字段
    urls = json_data.get('urls')
    if not urls or not isinstance(urls, list):
        return jsonify({"status": "error", "message": "...", "code": 400}), 400

    # 3. 处理请求
    platform_dispatcher.dispatch(json_data)

    # 4. 分类异常处理
    except BadRequest:  # 客户端错误 400
    except ValueError:  # 业务校验错误 400
    except Exception:   # 服务器错误 500
```

`关键技术点`
1. **输入校验**：校验 JSON 格式、必需字段、URL 格式
2. **异常分类**：`BadRequest`（400）、`ValueError`（400）、`Exception`（500）
3. **日志记录**：使用 `logger.error()` 替代 `print()`
4. **环境区分**：生产环境返回通用错误，开发环境返回详细错误
5. **结构化响应**：统一返回 `status`、`message`、`code` 字段

### 3. Docker 优化

`背景`
原有 Dockerfile 存在以下问题：
1. 基于 AlmaLinux 手动编译 Python 和 OpenSSL，镜像 ~800MB
2. 使用绝对路径 `COPY`，构建上下文不清晰
3. 未使用多阶段构建，编译工具残留

`解决方案`
采用多阶段构建，基于 `python:3.12-slim`：
- **阶段1**（builder）：安装编译依赖，安装 Python 包
- **阶段2**（runtime）：仅复制虚拟环境和运行时依赖

优化后镜像 ~300-400MB，减少约 50%。

`Docker Compose`
新增 `docker-compose.yml` 一键部署：
- MySQL 8.0 服务（配置最大连接数、超时参数）
- 应用服务（依赖 MySQL 健康检查）
- 独立网络 `smd-network`
- 数据卷持久化

---

### 4. run-server.sh 启动脚本重构

`背景`
原有 `run-server.sh` 存在以下问题：
1. **输出丢弃**：`nohup python3 ./server.py > /dev/null 2>&1 &` 导致所有日志丢失
2. **pip 更新脆弱**：依赖清华源和 `pip index versions` 命令，可能失败
3. **依赖安装复杂**：MD5 校验 + 逐个检查逻辑复杂，但 pip 本身已优化
4. **无配置检查**：未检查 `.env` 是否存在，可能使用默认配置启动
5. **无端口检查**：未检查 5000 端口是否占用，导致启动冲突
6. **可重复启动**：多次执行脚本启动多个实例
7. **重复激活**：两次 `source venv/bin/activate`

`解决方案`
重写启动脚本，添加以下功能：

**1. Python 版本检查**
```bash
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [[ "$PYTHON_VERSION" < "3.12" ]]; then
    log_warn "Python 版本低于要求"
fi
```

**2. 虚拟环境管理**
```bash
if [[ -n "$VIRTUAL_ENV" ]]; then
    log_info "已处于虚拟环境中"
else
    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
fi
```

**3. 依赖安装简化**
```bash
# 原：复杂的 MD5 校验 + 逐个检查
# 新：pip 自动跳过已安装的包
pip install -q -r "$REQUIREMENTS_FILE" --disable-pip-version-check
```

**4. 配置文件检查**
```bash
if [[ ! -f ".env" ]]; then
    log_warn "未找到 .env 配置文件"
    cp .env.example .env
    sleep 10  # 给用户时间编辑配置
fi
```

**5. 端口占用检查**
```bash
if command -v lsof &> /dev/null; then
    if lsof -i ":$SERVER_PORT" &> /dev/null; then
        log_error "端口 $SERVER_PORT 已被占用"
        exit 1
    fi
fi
```

**6. PID 防重复启动**
```bash
PID_FILE="./.server.pid"
if [[ -f "$PID_FILE" ]]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        log_error "服务已在运行 (PID: $OLD_PID)"
        exit 1
    fi
fi
```

**7. 日志输出到文件**
```bash
# 原：> /dev/null 2>&1
# 新：输出到日志文件
nohup python3 ./server.py > "$LOG_FILE" 2>&1 &
```

**8. 彩色输出**
```bash
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
```

`优化效果`
| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| 日志可追溯性 | 无（丢弃到 /dev/null） | 有（logs/ 文件） |
| 配置检查 | 无 | 自动创建模板 |
| 端口冲突 | 可能冲突 | 启动前检查 |
| 重复进程 | 可启动多个 | PID 文件阻止 |
| pip 更新 | 依赖外部镜像源 | 不强制更新 |
| 依赖安装 | 复杂 MD5 校验 | pip 自动处理 |
| 错误提示 | 简单 | 彩色分类 |

### 5. PyPI 镜像源自动检测

`背景`
国内服务器直接 `pip install` 官方源经常超时或失败，原脚本依赖单一清华源，若该源不可用则安装失败。

`解决方案`
添加镜像源自动检测功能：

**1. 多源列表**
```bash
PIP_MIRRORS=(
    "https://pypi.tuna.tsinghua.edu.cn/simple/"
    "https://mirrors.aliyun.com/pypi/simple/"
    "https://pypi.mirrors.ustc.edu.cn/simple/"
    "https://mirrors.cloud.tencent.com/pypi/simple/"
    "https://pypi.org/simple/"
)
```

**2. 自动检测**
```bash
detect_pypi_mirror() {
    local timeout=3
    for mirror in "${PIP_MIRRORS[@]}"; do
        if curl -s -o /dev/null -w "%{http_code}" --connect-timeout "$timeout" "$mirror" | grep -q "200"; then
            echo "$mirror"
            return 0
        fi
    done
    return 1
}
```

**3. 使用检测到的源**
```bash
MIRROR_URL=$(detect_pypi_mirror)
if [[ -n "$MIRROR_URL" ]]; then
    TRUSTED_HOST=$(echo "$MIRROR_URL" | sed -e 's|https\?://||' -e 's|/.*||')
    pip install -q -r requirements.txt -i "$MIRROR_URL" --trusted-host "$TRUSTED_HOST"
else
    # 回退到默认源
    pip install -q -r requirements.txt
fi
```

`优势`
1. **自动容灾**：一个源不可用自动尝试下一个
2. **超时控制**：每个源最多等待 3 秒
3. **智能回退**：所有源不可用时使用官方源
4. **无需配置**：用户无需手动指定源

---