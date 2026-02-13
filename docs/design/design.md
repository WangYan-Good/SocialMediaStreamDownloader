## 系统架构设计

### 平台配置设计

为了提高系统的可扩展性，我们引入了动态平台配置机制：

- **配置文件**：使用YAML格式存储平台配置信息
- **动态加载**：系统启动时动态加载配置文件中的平台信息
- **插件化支持**：通过配置文件可以轻松添加新平台支持

|配置项|说明|
|:-|:-|
|handler|平台处理器的模块路径|
|domains|该平台相关的域名列表|
|enabled|是否启用该平台|

### 支持的平台功能

系统当前支持以下社交媒体平台的下载功能：

- **抖音 (Douyin)**：支持直播下载、视频下载等功能
- **小红书**：计划支持
- **快手**：计划支持
- **哔哩哔哩**：计划支持

未来可通过配置文件轻松扩展更多平台。

### 数据库设计

系统遵循以下数据类型存储原则：
- 状态：unsigned tinyint, 占 1 个字节 0~255
- ID: varchar(200)
- 姓名昵称: varchar(50)
- 城市: varchar(100)
- 位置：varchar(100)
- 类型: unsigned tinyint, 占 1 个字节 0~255
- 模式: unsigned tinyint, 占 1 个字节 0~255
- 时间：timestamp
- URL: text，最大 64KB
- 星座: varchar(20)
- 等级: unsigned smallint, 占 2 个字节 0-65535
- 性别：unsigned tinyint, 占 1 个字节 0-255
- 签名：text, 最大 64KB
- 号码：varchar(20)
- 配置：text, 最大 64KB
- 参数：text, 最大 64KB
- 标题：tinytext, 最大 256 字节
- 版本：varchar(20)
- 标签：tinytext, 最大 256 字节
- 关注数量：unsigned int 占 4 个字节 0 - 4 294,967,295
- 粉丝数量：unsigned bigint 占 8 个字节 0 - 18,446,744,073,709,551,615
- 设置: tinytext, 最大 256 字节
- uri 的 url 索引: unsigned tinyint, 占 1 个字节
- 拓扑路径: tinyint, 最大 256 字节
- 颜色: varchar(7)
- 时长: unsinged int
- 选项: varchar(100)

#### 抖音直播信息表结构

直播间 room 表包含以下关键字段：
- `cover` - 封面图片信息
- `owner` - 主播信息
- `title` - 直播标题
- `start_time` - 开播时间
- `popularity` - 人气值
- `user_count` - 观众数量
- `share_url` - 分享链接
- `status` - 直播状态

用户表 user 包含以下关键字段：
- `sec_user_id` - 用户唯一标识
- `nickname` - 用户昵称
- `signature` - 用户签名
- `avatar` - 头像链接
- `follow_status` - 关注状态
- `fans_count` - 粉丝数量
- `works_count` - 作品数量