#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import asyncio

import botpy
from botpy import logging as botpy_logging
from botpy.message import GroupMessage, C2CMessage
from botpy.ext.cog_yaml import read

from .reminder import Reminder

# 配置日志
_log = botpy_logging.get_logger()

class CommandError(Exception):
    """命令处理错误"""
    pass

class PermissionError(CommandError):
    """权限错误"""
    pass

class ValidationError(CommandError):
    """参数验证错误"""
    pass

# 定义命令处理函数
async def help_command():
    """显示帮助信息"""
    return True

async def status_command():
    """查看机器人当前状态"""
    return True

async def current_command():
    """显示当前值日人员"""
    return True

async def list_command():
    """列出成员或假期"""
    return True

async def add_member_command():
    """添加成员"""
    return True

async def add_holiday_command():
    """添加假期"""
    return True

async def remove_command():
    """删除成员或假期"""
    return True

async def set_command():
    """设置配置"""
    return True

async def enable_command():
    """启用提醒功能"""
    return True

async def disable_command():
    """禁用提醒功能"""
    return True

async def silent_command():
    """设置静默模式"""
    return True

async def send_command():
    """手动触发提醒"""
    return True

async def next_command():
    """获取下一个成员"""
    return True

async def reset_command():
    """重置轮换顺序"""
    return True
async def restart_command():
    """重启定时任务"""
    return True

class SweepingBot(botpy.Client):
    def __init__(self, intents):
        super().__init__(intents=intents)
        self.reminder = Reminder(self)
        self.config = read(os.path.join(os.path.dirname(__file__), "..", "config.yaml"))
        self.command_prefix = "/"  # 使用标准的斜杠作为前缀
        self.admin_ids = self.config.get("admin_ids", [])
        self.silent_mode = False
        
        # 初始化命令处理器和帮助信息
        self.command_handlers = {}
        self.command_aliases = {}
        self.command_help = {}
        
        # 注册命令处理函数
        self._register_commands()

    def _register_commands(self):
        """注册所有命令处理函数"""
        # 普通命令
        self._add_command("help", help_command, ["帮助"], "显示帮助信息")
        self._add_command("status", status_command, ["状态"], "查看机器人当前状态")
        self._add_command("current", current_command, ["当前"], "显示当前值日人员")
        self._add_command("list", list_command, [], "列出成员或假期")
        
        # 管理员命令
        self._add_command("addm", add_member_command, [], "添加成员", admin=True)
        self._add_command("addh", add_holiday_command, [], "添加假期", admin=True)
        self._add_command("rm", remove_command, [], "删除成员或假期", admin=True)
        self._add_command("set", set_command, [], "设置配置", admin=True)
        self._add_command("on", enable_command, [], "启用提醒功能", admin=True)
        self._add_command("off", disable_command, [], "禁用提醒功能", admin=True)
        self._add_command("silent", silent_command, [], "设置静默模式", admin=True)
        self._add_command("send", send_command, [], "手动触发提醒", admin=True)
        self._add_command("next", next_command, [], "获取下一个成员", admin=True)
        self._add_command("reset", reset_command, [], "重置轮换顺序", admin=True)
        self._add_command("restart", restart_command, [], "重启所有定时任务", admin=True)

    def _add_command(self, name, handler, aliases=None, help_text="", admin=False):
        """添加命令处理函数"""
        # 设置标记
        handler.is_admin = admin
        
        # 注册主命令
        self.command_handlers[name] = handler
        self.command_help[name] = help_text
        
        # 注册别名
        if aliases:
            for alias in aliases:
                self.command_aliases[alias] = name

    async def on_ready(self):
        """机器人启动时触发"""
        _log.info(f"扫地机器人「{self.robot.name}」已启动!")
        #启动任务
        #定时提醒任务
        asyncio.create_task(self.reminder.start_reminder(self))
        #定时更新索引任务
        asyncio.create_task(self.reminder.start_update_index(self))

    async def generate_help_text(self) -> str:
        """生成帮助文本"""
        help_text = ["扫地机器人命令帮助:"]
        
        # 普通命令
        help_text.append("\n普通命令:")
        help_text.append(f"{self.command_prefix}help - 显示帮助信息")
        help_text.append(f"{self.command_prefix}status - 查看机器人当前状态")
        help_text.append(f"{self.command_prefix}current - 显示当前值日人员")
        help_text.append(f"{self.command_prefix}list [m/h] - 列出成员(m)或假期(h)")
        
        # 管理员命令
        help_text.append("\n管理员命令:")
        help_text.append(f"{self.command_prefix}addm [name] [qq] - 添加成员")
        help_text.append(f"{self.command_prefix}addh [MM-DD] - 添加假期")
        help_text.append(f"{self.command_prefix}rm [m/h] [id/MM-DD] - 删除成员或假期")
        help_text.append(f"{self.command_prefix}set [time/index-time/id] [HH:MM/HH:MM:SS/1、2、3...] - 设置提醒时间、索引更新时间和当前值日生")
        help_text.append(f"{self.command_prefix}on - 启用提醒功能")
        help_text.append(f"{self.command_prefix}off - 禁用提醒功能")
        help_text.append(f"{self.command_prefix}silent [on/off] - 设置静默模式")
        help_text.append(f"{self.command_prefix}send - 手动触发提醒")
        help_text.append(f"{self.command_prefix}next - 切换到下一值日人员")
        help_text.append(f"{self.command_prefix}reset - 重置轮换顺序")
        help_text.append(f"{self.command_prefix}restart - 重启所有定时任务")
        
        return "\n".join(help_text)

    async def on_group_at_message_create(self, message: GroupMessage):
        """处理群聊消息"""
        _log.info(f"收到群聊消息: {message.content}")
            
        # 处理命令
        content = message.content.strip()
        
        # 检查命令完整性
        if content.startswith("/addm") and len(content.split()) < 3:
            await message.reply(content="格式错误,请使用: /addm [name] [qq]")
            return
        elif content.startswith("/list") and len(content.split()) < 2:
            await message.reply(content="格式错误,请使用: /list [m/h] (m:成员列表, h:假期列表)")
            return
        elif content.startswith("/addh") and len(content.split()) < 2:
            await message.reply(content="格式错误,请使用: /addh [MM-DD]")
            return
        elif content.startswith("/rm") and len(content.split()) < 3:
            await message.reply(content="格式错误,请使用: /rm [m/h] [id/MM-DD]")
            return
        elif content.startswith("/set") and len(content.split()) < 3:
            await message.reply(content="格式错误,请使用: /set [time/id] [HH:MM/1、2、3...]")
            return
        elif content.startswith("/silent") and len(content.split()) < 2:
            await message.reply(content="格式错误,请使用: /silent [on/off]")
            return
            
        # 添加成员
        if content.startswith("/addm "):
            try:
                #权限检查
                if not self.is_admin(message):
                    cmd = content.split( )
                    await message.reply(content=f"你没有权限执行' {cmd[0]} '命令")
                    return
                parts = content.split()
                _, name, qq_id = parts
                success, msg = self.reminder.add_member(name, qq_id)
                await message.reply(content=msg)
            except ValueError:
                await message.reply(content="格式错误,请使用: /addm [name] [qq]")
                
        # 强制发送提醒
        elif content == "/send":
            try:
                #权限检查
                if not self.is_admin(message):
                    cmd = content.split( )
                    await message.reply(content=f"你没有权限执行' {cmd[0]} '命令")
                    return
                current_member = self.reminder.members_data["members"][self.reminder.members_data["current_index"]]
                if not self.reminder.config["enabled"]:
                    await message.reply(content="提醒功能已禁用,无法发送提醒")
                elif self.reminder.config["silent_mode"]:
                    await message.reply(content="静默模式已启用,不发送提醒")
                elif self.reminder.is_holiday():
                    await message.reply(content="今天是假期,不发送提醒")
                else:
                    await self.reminder.send_reminder(self, force_send=True)
                    await message.reply(content=f"已发送提醒给：{current_member['name']}(ID:{current_member['id']})")
            except Exception as e:
                await message.reply(content=f"提醒发送失败：{str(e)}")
                
        # 获取状态
        elif content == "/status":
            status = self.reminder.get_status()
            await message.reply(content=status)
            
        # 列出成员或假期
        elif content.startswith("/list "):
            try:
                parts = content.split()
                _, list_type = parts
                if list_type == "m":
                    member_list = self.reminder.list_members()
                    await message.reply(content=member_list)
                elif list_type == "h":
                    holidays = self.reminder.list_holidays()
                    await message.reply(content=holidays)
                else:
                    await message.reply(content="格式错误,请使用: /list [m/h] (m:成员列表, h:假期列表)")
            except ValueError:
                await message.reply(content="格式错误,请使用: /list [m/h] (m:成员列表, h:假期列表)")
            
        # 添加假期
        elif content.startswith("/addh "):
            try:
                #权限检查
                if not self.is_admin(message):
                    cmd = content.split( )
                    await message.reply(content=f"你没有权限执行' {cmd[0]} '命令")
                    return
                parts = content.split()
                _, date = parts
                success, msg = self.reminder.add_holiday(date)
                await message.reply(content=msg)
            except ValueError:
                await message.reply(content="格式错误,请使用: /addh [MM-DD]")
                
        # 删除成员或假期
        elif content.startswith("/rm "):
            try:
                #权限检查
                if not self.is_admin(message):
                    cmd = content.split( )
                    await message.reply(content=f"你没有权限执行' {cmd[0]} '命令")
                    return
                parts = content.split()
                _, rm_type, value = parts
                if rm_type == "m":
                    success, msg = self.reminder.remove_member_by_id(value)
                elif rm_type == "h":
                    success, msg = self.reminder.remove_holiday(value)
                else:
                    await message.reply(content="格式错误,请使用: /rm [m/h] [id/MM-DD]")
                    return
                await message.reply(content=msg)
            except ValueError:
                await message.reply(content="格式错误,请使用: /rm [m/h] [id/MM-DD]")
                
        # 设置提醒时间或当前值日生
        elif content.startswith("/set "):
            try:
                #权限检查
                if not self.is_admin(message):
                    cmd = content.split( )
                    await message.reply(content=f"你没有权限执行' {cmd[0]} '命令")
                    return
                parts = content.split()
                _, set_type, value = parts
                if set_type == "time":
                    success, msg = self.reminder.set_reminder_time(value)
                elif set_type == "index-time":
                    success, msg = self.reminder.set_index_update_time(value)
                elif set_type == "id":
                    success, msg = self.reminder.set_current_member(value)
                else:
                    await message.reply(content="格式错误,请使用: /set [time/id] [HH:MM/1、2、3...]")
                    return
                await message.reply(content=msg)
            except ValueError:
                await message.reply(content="格式错误,请使用: /set [time/id] [HH:MM/1、2、3...]")
                
        # 切换启用状态
        elif content == "/on":
            #权限检查
            if not self.is_admin(message):
                cmd = content.split( )
                await message.reply(content=f"你没有权限执行' {cmd[0]} '命令")
                return
            current_status = self.reminder.config["enabled"]
            if current_status:
                await message.reply(content="提醒功能已经是启用状态")
            else:
                success, msg = self.reminder.toggle_enabled(True)
                await message.reply(content=msg)
                
        elif content == "/off":
            #权限检查
            if not self.is_admin(message):
                cmd = content.split( )
                await message.reply(content=f"你没有权限执行' {cmd[0]} '命令")
                return
            current_status = self.reminder.config["enabled"]
            if not current_status:
                await message.reply(content="提醒功能已经是关闭状态")
            else:
                success, msg = self.reminder.toggle_enabled(False)
                await message.reply(content=msg)
                
        # 切换静默模式
        elif content.startswith("/silent "):
            try:
                #权限检查
                if not self.is_admin(message):
                    cmd = content.split( )
                    await message.reply(content=f"你没有权限执行' {cmd[0]} '命令")
                    return
                parts = content.split()
                _, mode = parts
                if mode == "on":
                    current_status = self.reminder.config["silent_mode"]
                    if current_status:
                        await message.reply(content="静默模式已经是开启状态")
                    else:
                        success, msg = self.reminder.toggle_silent_mode(True)
                        await message.reply(content=msg)
                elif mode == "off":
                    current_status = self.reminder.config["silent_mode"]
                    if not current_status:
                        await message.reply(content="静默模式已经是关闭状态")
                    else:
                        success, msg = self.reminder.toggle_silent_mode(False)
                        await message.reply(content=msg)
                else:
                    await message.reply(content="格式错误,请使用: /silent [on/off]")
            except ValueError:
                await message.reply(content="格式错误,请使用: /silent [on/off]")
                
        # 重置轮换
        elif content == "/reset":
            #权限检查
            if not self.is_admin(message):
                cmd = content.split( )
                await message.reply(content=f"你没有权限执行' {cmd[0]} '命令")
                return
            self.reminder.reset_rotation()
            await message.reply(content="轮换已重置")
            
        # 获取当前值日人员
        elif content == "/current":
            current = self.reminder.get_current_member()
            await message.reply(content=current)
            
        # 切换到下一值日人员
        elif content == "/next":
            #权限检查
            if not self.is_admin(message):
                cmd = content.split( )
                await message.reply(content=f"你没有权限执行' {cmd[0]} '命令")
                return
            next_member = self.reminder.get_next_member()
            if isinstance(next_member, dict):
                await message.reply(content=f"已切换到下一值日人员: {next_member['name']}")
            else:
                await message.reply(content="没有可用的成员")
        
        elif content == "/restart":
            if not self.is_admin(message):
                cmd = content.split( )
                await message.reply(content=f"你没有权限执行' {cmd[0]} '命令")
                return
            success, content = self.reminder.restart_task()
            await message.reply(content)

        # 显示帮助信息
        elif content == "/help":
            help_text = await self.generate_help_text()
            await message.reply(content=help_text)

    async def on_c2c_message_create(self, message: C2CMessage):
        """处理私聊消息"""
        try:
            _log.info(f"收到私聊消息: {message.content}")
            
            # 解析命令
            content = message.content.strip()
            if not content.startswith(self.command_prefix):
                # 非命令消息,返回默认提示
                await message._api.post_c2c_message(
                    openid=message.author.user_openid,
                    msg_type=0,
                    msg_id=message.id,
                    content=f"您好,请使用{self.command_prefix}help查看可用命令"
                )
                return

            # 分割命令和参数
            parts = content[len(self.command_prefix):].strip().split()
            if not parts:
                return

            command = parts[0].lower()
            params = parts[1:] if len(parts) > 1 else None

            # 处理命令并生成响应文本
            result = await self._process_c2c_command(message, command, params)
            
            # 使用私聊API回复消息
            await message._api.post_c2c_message(
                openid=message.author.user_openid,
                msg_type=0,
                msg_id=message.id,
                content=result
            )

        except Exception as e:
            _log.error(f"处理私聊消息时发生错误: {str(e)}")
            try:
                await message._api.post_c2c_message(
                    openid=message.author.user_openid,
                    msg_type=0,
                    msg_id=message.id,
                    content=f"处理消息时发生错误: {str(e)}"
                )
            except:
                _log.error(f"回复私聊错误消息失败: {str(e)}")

    async def _process_c2c_command(self, message, command, params):
        """处理私聊命令,返回结果字符串"""
        # 查找命令处理函数
        if command in self.command_handlers:
            handler = self.command_handlers[command]
        elif command in self.command_aliases:
            main_cmd = self.command_aliases[command]
            handler = self.command_handlers[main_cmd]
        else:
            return f"未找到命令: {command},请使用{self.command_prefix}help查看可用命令"
            
        # 检查权限
        # if handler.is_admin and not self.is_admin(message):
        #     return "您没有权限执行此命令"
            
        # 根据命令类型获取结果
        if command == "help":
            if params and params:
                cmd = params[0].lower()
                if cmd in self.command_help:
                    return f"命令 {cmd} 的帮助信息:\n{self.command_help[cmd]}"
                else:
                    return f"未找到命令 {cmd} 的帮助信息"
            else:
                return await self.generate_help_text()
        elif command == "status":
            return self.reminder.get_status()
        elif command == "current":
            return self.reminder.get_current_member()
        elif command == "list":
            if not params or not params:
                return "格式错误,请使用: /list [m/h] (m:成员列表, h:假期列表)"
            if params[0] == "m":
                return self.reminder.list_members()
            elif params[0] == "h":
                return self.reminder.list_holidays()
            else:
                return "格式错误,请使用: /list [m/h] (m:成员列表, h:假期列表)"
        elif command == "addm":
            if not params or len(params) < 2:
                return "格式错误,请使用: /addm [name] [qq]"
            success, msg = self.reminder.add_member(params[0], params[1])
            return msg
        elif command == "addh":
            if not params or not params:
                return "格式错误,请使用: /addh [MM-DD]"
            success, msg = self.reminder.add_holiday(params[0])
            return msg
        elif command == "rm":
            if not params or len(params) < 2:
                return "格式错误,请使用: /rm [m/h] [id/MM-DD]"
            if params[0] == "m":
                success, msg = self.reminder.remove_member_by_id(params[1])
                return msg
            elif params[0] == "h":
                success, msg = self.reminder.remove_holiday(params[1])
                return msg
            else:
                return "格式错误,请使用: /rm [m/h] [id/MM-DD]"
        elif command == "set":
            if not params or len(params) < 2:
                return "格式错误,请使用: /set [time/index-time/id] [HH:MM/HH:MM:SS/1、2、3...]"
            if params[0] == "time":
                success, msg = self.reminder.set_reminder_time(params[1])
                return msg
            elif params[0] == "index-time":
                success, msg = self.reminder.set_index_update_time(params[1])
                return msg
            elif params[0] == "id":
                success, msg = self.reminder.set_current_member(params[1])
                return msg
            else:
                return "格式错误,请使用: /set [time/index-time/id] [HH:MM/HH:MM:SS/1、2、3...]"
        elif command == "on":
            current_status = self.reminder.config["enabled"]
            if current_status:
                return "提醒功能已经是启用状态"
            success, msg = self.reminder.toggle_enabled(True)
            return msg
        elif command == "off":
            current_status = self.reminder.config["enabled"]
            if not current_status:
                return "提醒功能已经是关闭状态"
            success, msg = self.reminder.toggle_enabled(False)
            return msg
        elif command == "silent":
            if not params or not params:
                return "格式错误,请使用: /silent [on/off]"
            if params[0] == "on":
                current_status = self.reminder.config["silent_mode"]
                if current_status:
                    return "静默模式已经是开启状态"
                success, msg = self.reminder.toggle_silent_mode(True)
                return msg
            elif params[0] == "off":
                current_status = self.reminder.config["silent_mode"]
                if not current_status:
                    return "静默模式已经是关闭状态"
                success, msg = self.reminder.toggle_silent_mode(False)
                return msg
            else:
                return "格式错误,请使用: /silent [on/off]"
        elif command == "send":
            await self.reminder.send_reminder(self, force_send=True)
            current_member = self.reminder.members_data["members"][self.reminder.members_data["current_index"]]
            if not self.reminder.config["enabled"]:
                return "提醒功能已禁用,无法发送提醒"
            elif self.reminder.config["silent_mode"]:
                return "静默模式已启用,不发送提醒"
            elif self.reminder.is_holiday():
                return "今天是假期,不发送提醒"
            else:
                return f"已发送提醒给：{current_member['name']}(ID:{current_member['id']})"
        elif command == "next":
            next_member = self.reminder.get_next_member()
            if isinstance(next_member, dict):
                # 更新当前索引
                current_index = self.reminder.members_data["current_index"]
                next_index = (current_index + 1) % len(self.reminder.members_data["members"])
                self.reminder.members_data["current_index"] = next_index
                self.reminder.save_members()
                return f"已切换到下一值日人员: {next_member['name']}"
            else:
                return "没有可用的成员"
        elif command == "reset":
            self.reminder.reset_rotation()
            return "轮换已重置"
        elif command == "restart":
            success, content = self.reminder.restart_task()
            return f"{content}"
        # 未知命令或格式错误
        return f"命令格式错误,请使用{self.command_prefix}help查看帮助"

    def is_admin(self, message):
        """检查用户是否为管理员"""
        
        # 特殊情况: 如果没有设置管理员ID,则默认允许所有人访问管理员命令
        if not self.admin_ids:
            _log.info("未配置管理员ID,默认允许访问管理员命令")
            return True
            
        # 打印消息对象信息用于调试
        _log.info(f"消息对象类型: {type(message).__name__}")
        
        try:
            # 对于群聊消息
            if hasattr(message, 'author'):
                # 尝试获取用户ID
                if hasattr(message.author, 'member_openid'):
                    user_id = message.author.member_openid
                    _log.info(f"检查管理员权限:{(user_id in self.admin_ids)}")
                    _log.info(f"从群聊消息获取用户ID(member_openid): {user_id}")
                    return user_id in self.admin_ids
                    
                # 打印所有可用属性
                _log.info(f"用户对象属性: {dir(message.author)}")
                
                # 紧急情况: 群聊消息暂时全部允许
                _log.info("无法确定用户ID,暂时允许群聊中的管理员命令")
                return True
                
            # 紧急情况: 如果找不到用户ID,暂时允许访问
            _log.info("无法确定消息类型,暂时允许管理员命令")
            return True
            
        except Exception as e:
            _log.error(f"检查管理员权限时出错: {str(e)}")
            # 安全起见,权限检查失败时拒绝访问
            return False