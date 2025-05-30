# QQ 群自动化扫地提醒机器人

基于 QQ 官方机器人框架（qq-botpy）的自动化群管理工具，实现群内成员轮流扫地的提醒功能。

## 功能特点

1. **每日定时提醒**：在指定时间自动发送提醒邮件，发送如："今天是 xxxx 年 xx 月 xx 日 星期 x，今天该你扫地啦"的消息
2. **成员轮换**：支持顺序循环或自定义选择群成员
3. **灵活控制**：提供暂停/恢复、静默模式、节假日白名单等管理功能
4. **易配置性**：通过 QQ 群/私聊内指令动态调整设置，无需修改代码
5. **高可靠性**：内置错误重试机制，确保消息能够可靠送达
6. **状态查询**：随时查看当前值日人员和提醒状态

## 安装和部署

### 前提条件

- Python 3.7+
- QQ 机器人开发者账号

### 安装步骤

1. 克隆本仓库

   ```bash
   git clone https://github.com/yourusername/qq-sweep-bot.git
   cd qq-sweep-bot
   ```

2. 安装依赖

   ```bash
   pip install -r requirements.txt
   ```

3. 配置机器人信息
   在 `config.yaml`中填写你的机器人信息：

   ```yaml
   appid: "你机器人的appid"
   token: "你机器人的token"
   secret: "你机器人的secret"
   intent:
     - at_messages
     - public_messages
     - guild_messages
     - c2c_messages
   admin_role_id: "管理员角色ID"
   ```

4. 运行机器人

   ```bash
   # Linux/MacOS
   ./start.sh

   # Windows
   start.bat
   ```

## 项目结构

```
qq-botpy-v2/
├── config.yaml           # 机器人主配置文件
├── data/                 # 数据目录
│   ├── config.json       # 机器人功能配置
│   └── member.json       # 成员列表
├── main.py               # 主程序入口
├── modules/              # 模块目录
│   ├── __init__.py       # 包初始化文件
│   ├── commands.py       # 命令处理模块
│   └── reminder.py       # 提醒管理模块
├── README.md             # 项目说明文档
├── requirements.txt      # 项目依赖
├── start.bat             # Windows启动脚本
├── start.sh              # Linux/MacOS启动脚本
└── qqbot.service.example # Systemd服务文件示例
```

## 配置文件

### config.yaml

机器人的基本配置，包含 appid、token、secret 权限等信息。

其中 appid、token、secret 都可以在 QQ 开放平台创建的机器人找到

secret 为高保密，QQ 开放平台只会显示第一次，而后只能重置不能查看，请牢记。

### data/config.json

机器人的功能配置：

- `reminder_time`: 每日提醒时间
- `message_templates`: 消息模板
  - `normal`: 正常提醒格式
  - `pause`: 暂停时提醒格式
- `email_config`: 邮件配置

  - `smtp_server`: SMTP 服务器地址
  - `smtp_port`: SMTP 服务器端口
  - `sender`: 发件人（机器人）邮箱
  - `password`: 发件人邮箱密码（授权码）
  - `subject`: 邮件主题
  - `admin_email`: 管理员提醒邮箱

- `index_update_time`: 索引（轮换顺序）更新时间
- `enabled`: 是否启用提醒
- `sender?`: 是否已经发送过提醒
- `silent_mode`: 是否启用静默模式
- `holiday_whitelist`: 假期白名单

### data/member.json

成员名单配置：

- `members`: 成员列表，每个成员包含 id、name 和 qq_id
- `current_index`: 当前轮换到的成员索引（不是 id 是从 0 开始的索引）
- `last_reminder_date`: 上次提醒日期

## 命令相关

### 指令前缀说明

- **QQ 平台官方指令**：使用"/"作为前缀（例如"/help"）
- 此前缀不可更改，由 QQ 平台固定设置

### 普通命令

- `/help` - 显示帮助信息
- `/status` - 查看机器人当前状态
- `/current` - 显示当前值日人员
- `/list [m/h]` - 列出成员或假期

### 管理员命令

格式 功能

- `/addm [名字] [QQ号]` - 添加成员
- `/addh [MM-DD]` - 添加假期
- `/rm [m/h] [QQ号/MM-DD]` - 删除成员或假期
- `/set [time/index-time/id] [HH:MM/HH:MM-SS/1,2,3···]` - 设置提醒时间、索引更新时间、当前值日人员
- `/on` - 启用提醒功能
- `/off` - 禁用提醒功能
- `/silent [on/off]` - 开启/关闭静默模式
- `/send` - 手动触发提醒
- `/next` - 获取下一个成员(可选随机模式)
- `/reset` - 重置轮换顺序，从第一个成员开始
- `/restart` - 重启所有定时任务

### 使用示例

1. 查看帮助信息：

```
/help
```

2. 添加新成员：

```
/addm 张三 123456789
```

3. 设置提醒时间：

```
/set time 08:00
```

4. 查看当前值日人员：

```
/current
```

5. 切换到下一值日人员：

```
/next
```

### 注意事项

1. 管理员指令需要相应的权限才能使用
2. 时间格式必须严格遵循 HH:MM 格式
3. 日期格式必须严格遵循 MM-DD 格式
4. 成员 ID 必须是数字

### 错误处理

当指令格式错误或执行失败时，机器人会返回相应的错误提示信息，帮助用户理解问题所在。常见错误包括：

5. 格式错误：指令参数格式不正确
6. 权限错误：用户没有执行该指令的权限
7. 参数错误：提供的参数无效或不存在
8. 系统错误：机器人内部处理出错

## 部署为服务

在 Linux 系统上，你可以使用 Systemd 将机器人部署为服务，以便在系统启动时自动运行：

1. 复制服务文件示例并修改

   ```bash
   sudo cp qqbot.service.example /etc/systemd/system/qqbot.service
   sudo nano /etc/systemd/system/qqbot.service
   ```

2. 修改文件中的用户名和路径
3. 启用并启动服务

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable qqbot.service
   sudo systemctl start qqbot.service
   ```

4. 检查服务状态

   ```bash
   sudo systemctl status qqbot.service
   ```

---

文档最后更新日期：2025 年 5 月 30 日 0:18
