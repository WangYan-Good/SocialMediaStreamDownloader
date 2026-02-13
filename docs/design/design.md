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

- **用户表**

|sec_user_id|nickname|post_share_url|live_share_url|
|:-|:-|:-|:-|
|MS4wLjABAAAAiTYeahaMCuDgWzy8uqWELnZSq3MQYsJTe_d_MUOvq2zzbu72TeVvxDXOR5TOo_fO|萝呀萝|https://v.douyin.com/iP1G4Mhs/|https://v.douyin.com/iP1G4Mhs/|

- **主页链接分享表**

|share url|temp location|target location|
|:-|:-|:-|
|url|||

- **直播链接分享表**

- **作品链接分享表**