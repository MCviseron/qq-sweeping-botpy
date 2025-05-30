#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

import botpy
from botpy import logging as botpy_logging

# 配置日志
_log = botpy_logging.get_logger()

class Reminder:
    def __init__(self, client):
        self.client = client
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "config.json")
        self.members_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "member.json")
        self.load_config()
        self.load_members()
        self.scheduler_task = None
        self.update_index = None

    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            _log.info("配置文件加载成功")
        except Exception as e:
            _log.error(f"加载配置文件失败: {e}")
            self.config = {
                "reminder_time": "08:00",
                "message_templates": {
                    "normal": "今天 ({year}-{month}-{day}) 星期 {weekday} ,今天该 {name} 你扫地啦",
                    "pause": "今天( {year}-{month}-{day} ) 星期 {weekday} ,本应该是 {name} 扫地,但轮换任务已暂停(不用扫)"
                },
                "email_config": {
                    "smtp_server": "smtp.qq.com",
                    "smtp_port": 465,
                    "sender_email": "your_email@qq.com",
                    "sender_password": "your_email_password",
                    "subject": "扫地提醒",
                    "admin_email": "your_admin_email"
                },
                "index_update_time": {
                    "h": 0,
                    "m": 0,
                    "s": 0,
                    "ms": 0
                },
                "enabled": True,
                "sender?": False,
                "silent_mode": False,
                "holiday_whitelist": []
            }
            self.save_config()

    def load_members(self):
        """加载成员列表"""
        try:
            with open(self.members_path, 'r', encoding='utf-8') as f:
                self.members_data = json.load(f)
            _log.info("成员列表加载成功")
        except Exception as e:
            _log.error(f"加载成员列表失败: {e}")
            self.members_data = {
                "members": [],
                "current_index": 0,
                "last_reminder_date": ""
            }
            self.save_members()

    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            _log.info("配置文件保存成功")
        except Exception as e:
            _log.error(f"保存配置文件失败: {e}")

    def save_members(self):
        """保存成员列表"""
        try:
            with open(self.members_path, 'w', encoding='utf-8') as f:
                json.dump(self.members_data, f, ensure_ascii=False, indent=2)
            _log.info("成员列表保存成功")
        except Exception as e:
            _log.error(f"保存成员列表失败: {e}")

    def get_next_member(self, random_mode=False):
        """获取下一个成员"""
        if not self.members_data["members"]:
            return None
            
        if random_mode:
            # 随机模式
            import random
            return random.choice(self.members_data["members"])
        else:
            # 顺序模式
            current_index = self.members_data["current_index"]
            next_index = (current_index + 1) % len(self.members_data["members"])
            return self.members_data["members"][next_index]

    def is_holiday(self):
        """检查今天是否是假期"""
        today = datetime.now().strftime("%m-%d")
        return today in self.config["holiday_whitelist"]

    async def send_email(self, recipient_email: str, subject: str, content: str) -> bool:
        """发送邮件
        
        Args:
            recipient_email: 收件人邮箱
            subject: 邮件主题
            content: 邮件内容
            
        Returns:
            bool: 是否发送成功
        """
        try:
            # 创建邮件对象
            msg = MIMEMultipart()
            msg['From'] = self.config["email_config"]["sender_email"]
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            # 添加邮件内容
            msg.attach(MIMEText(content, 'plain', 'utf-8'))
            
            # 使用SSL连接SMTP服务器
            _log.info(f"正在连接SMTP服务器: {self.config['email_config']['smtp_server']}:465")
            server = smtplib.SMTP_SSL(self.config["email_config"]["smtp_server"], 465)
            server.set_debuglevel(1)  # 启用调试模式
            
            _log.info("正在登录SMTP服务器...")
            server.login(self.config["email_config"]["sender_email"], self.config["email_config"]["sender_password"])
            _log.info("SMTP登录成功")
            
            _log.info(f"正在发送邮件到: {recipient_email}")
            server.send_message(msg)
            _log.info("邮件发送成功")
            
            server.quit()
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            _log.error(f"SMTP认证失败: {e}")
            return False
        except smtplib.SMTPException as e:
            _log.error(f"SMTP错误: {e}")
            return False
        except Exception as e:
            _log.error(f"发送邮件失败: {e}")
            return False

    async def admin_send_email(self, content: str) -> bool:
        """发送管理员邮件
        
        Args:
            content: 邮件内容
            
        Returns:
            bool: 是否发送成功
        """
        try:
            # 创建邮件对象
            msg = MIMEMultipart()
            msg['From'] = self.config["email_config"]["sender_email"]
            msg['To'] = self.config["email_config"]["admin_email"]
            msg['Subject'] = "Admin-bot-log-condition-email"
            
            # 添加邮件内容
            msg.attach(MIMEText(content, 'plain', 'utf-8'))
            
            # 使用SSL连接SMTP服务器
            _log.info(f"正在连接SMTP服务器: {self.config['email_config']['smtp_server']}:{self.config['email_config']['smtp_port']}")
            server = smtplib.SMTP_SSL(self.config["email_config"]["smtp_server"], self.config['email_config']['smtp_port'])
            server.set_debuglevel(0)  # 关闭调试模式
            
            _log.info("正在登录SMTP服务器...")
            server.login(self.config["email_config"]["sender_email"], self.config["email_config"]["sender_password"])
            _log.info("SMTP登录成功")
            
            _log.info(f"正在发送邮件到admin: {msg['To']}")
            server.send_message(msg)
            _log.info("邮件发送成功")
            
            server.quit()
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            _log.error(f"SMTP认证失败: {e}")
            return False
        except smtplib.SMTPException as e:
            _log.error(f"SMTP错误: {e}")
            return False
        except Exception as e:
            _log.error(f"发送邮件失败: {e}")
            return False

    async def send_reminder(self, client: botpy.Client, force_send=False):
        """发送提醒消息
        
        Args:
            client: botpy客户端实例
            force_send: 是否强制发送,忽略日期检查
        """
        if not self.config["enabled"]:
            _log.info("提醒功能已禁用,不发送提醒")
            return
            
        if self.config["silent_mode"]:
            _log.info("静默模式已启用,不发送提醒")
            return
            
        if self.is_holiday():
            _log.info("今天是假期,不发送提醒")
            return
            
        today = datetime.now()
        today_str = today.strftime("%Y-%m-%d")
        
        # 检查今天是否已经发送过提醒（除非强制发送）
        if not force_send and self.members_data["last_reminder_date"] == today_str:
            _log.info(f"今天 {today_str} 已经发送过提醒了")
            return
            
        # 获取当前成员
        if not self.members_data["members"]:
            _log.error("没有可用的成员")
            return
            
        current_member = self.members_data["members"][self.members_data["current_index"]]
        
        # 准备消息内容
        weekday_names = ["一", "二", "三", "四", "五", "六", "日"]
        weekday = weekday_names[today.weekday()]
        
        max_retries = 3
        retry_delay = 5  # 初始重试延迟（秒）
        
        if self.config["enabled"]:
            template = self.config["message_templates"]["normal"]
            message = template.format(
                year=today.year,
                month=today.month,
                day=today.day,
                weekday=weekday,
                name=current_member["name"]
            )
            
            # 发送邮件提醒
            for attempt in range(max_retries):
                try:
                    _log.info(f"尝试发送提醒给 {current_member['name']} (尝试 {attempt+1}/{max_retries})")
                    
                    # 构建收件人邮箱（QQ邮箱格式）
                    recipient_email = f"{current_member['qq_id']}@qq.com"
                    
                    # 发送邮件
                    success = await self.send_email(
                        recipient_email=recipient_email,
                        subject=self.config["email_config"]["subject"],
                        content=message
                    )
                    
                    if success:
                        _log.info(f"成功发送提醒邮件给 {current_member['name']}({current_member['id']})")
                        # 更新最后提醒日期
                        self.members_data["last_reminder_date"] = today_str
                        self.save_members()
                        #更新发送状态
                        self.config["sender?"] = True
                        self.save_config()
                        #管理员提醒邮件
                        #创建今天的索引更新时间 
                        now = datetime.now()
                        update_h , update_m , update_s = map(int, self.config["index_update_time"].split(":"))
                        next_update = now.replace(hour=update_h,minute=update_m,second=update_s,microsecond=0)
                        #如果已经过了今天的时间,则下一天
                        if now >= next_update:
                            next_update += timedelta(days=1)
                        
                        current_member = self.members_data["members"][self.members_data["current_index"]]
                        wait_seconds = (next_update - now).total_seconds()
                        #管理员提醒邮件
                        await self.admin_send_email(f"机器人成功发送提醒邮件给 {current_member['name']}({current_member['id']}),等待 {wait_seconds} 秒后更新索引到下一个成员\n{self.get_status()}\n")
                        return
                    else:
                        raise Exception("发送邮件失败")
                        
                except Exception as e:
                    if attempt < max_retries - 1:
                        _log.warning(f"发送提醒失败 (尝试 {attempt+1}/{max_retries}): {e}, {retry_delay}秒后重试")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                    else:
                        _log.error(f"发送提醒最终失败: {e}")
                        await self.admin_send_email(f"发送提醒最终失败: {e}")
                        raise e  # 重新抛出异常,让调用者知道发送失败
        else:
            template = self.config["message_templates"]["pause"]
            message = template.format(name=current_member["name"])
            
            for attempt in range(max_retries):
                try:
                    # 构建收件人邮箱（QQ邮箱格式）
                    recipient_email = f"{current_member['qq_id']}@qq.com"
                    
                    # 发送邮件
                    success = await self.send_email(
                        recipient_email=recipient_email,
                        subject=self.config["email_config"]["subject"],
                        content=message
                    )
                    
                    if success:
                        _log.info("已发送暂停提醒邮件")
                        return
                    else:
                        raise Exception("发送邮件失败")
                        
                except Exception as e:
                    if attempt < max_retries - 1:
                        _log.warning(f"发送暂停提醒失败 (尝试 {attempt+1}/{max_retries}): {e}, {retry_delay}秒后重试")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                    else:
                        _log.error(f"发送暂停提醒最终失败: {e}")
                        await self.admin_send_email(f"发送暂停提醒最终失败: {e}")
                        raise e  # 重新抛出异常,让调用者知道发送失败
    async def update_indexer(self, client):
        while True:
            try:
                retry_count1 = 0
                max_retry = 3
                # 更新当前索引到下一个成员


                update_time = self.config["index_update_time"]
                update_h , update_m , update_s = map(int, update_time.split(":"))

                #创建今天的索引更新时间 
                now = datetime.now()
                next_update = now.replace(hour=update_h,minute=update_m,second=update_s,microsecond=0)
                #如果已经过了今天的时间,则下一天
                if now >= next_update:
                    next_update += timedelta(days=1)
                
                # current_member = self.members_data["members"][self.members_data["current_index"]]
                wait_seconds = (next_update - now).total_seconds()
                _log.info(f"等待 {wait_seconds} 秒后更新索引到下一个成员")
                #管理员提醒邮件
                # await self.admin_send_email(f"机器人成功发送提醒邮件给 {current_member['name']}({current_member['id']}),等待 {wait_seconds} 秒后更新索引到下一个成员\n{self.get_status()}\n")
                # 等待索引更新时间
                await asyncio.sleep(wait_seconds)
                #定时器触发
                _log.info("索引更新器触发,准备更新索引")
                #更新索引
                current_index = self.members_data["current_index"]
                next_index = (current_index + 1) % len(self.members_data["members"])
                self.members_data["current_index"] = next_index
                _log.info(f"索引已更新:{current_index + 1} -> {next_index + 1}")
                await self.admin_send_email(f"值日索引已更新:{current_index + 1} -> {next_index + 1}")
                #更新发送状态
                self.config["sender?"] = False
                self.save_members()
                self.save_config()
                #短时间等待,防止重复发送
                await asyncio.sleep(120)
            except asyncio.CancelledError:
                _log.info("更新索引被取消")
                break
            except Exception as e:
                retry_count1 += 1
                _log.error(f"定时器出错 (尝试 {retry_count1}/{max_retry}): {e}")
                
                if retry_count1 >= max_retry:
                    _log.critical(f"定时器在 {max_retry} 次尝试后仍然失败,等待较长时间后重试")
                    retry_count1 = 0
                    await asyncio.sleep(3600)  # 出错多次后等待一小时再继续
                else:
                    await asyncio.sleep(60 * retry_count1)

    async def reminder_scheduler(self, client):
        """定时提醒调度器"""
        retry_count = 0
        max_retries = 3
        
        while True:
            try:
                now = datetime.now()
                reminder_time_str = self.config["reminder_time"]
                reminder_hour, reminder_minute = map(int, reminder_time_str.split(":"))
                
                # 创建今天的提醒时间
                next_reminder = now.replace(hour=reminder_hour, minute=reminder_minute, second=0, microsecond=0)
                
                # 如果已经过了今天的提醒时间,设置为明天
                if now >= next_reminder:
                    next_reminder = next_reminder + timedelta(days=1)
                
                # 计算等待时间
                wait_seconds = (next_reminder - now).total_seconds()
                _log.info(f"下一次提醒将在 {next_reminder.strftime('%Y-%m-%d %H:%M:%S')} 发送,等待 {wait_seconds:.2f} 秒")
                
                # 等待到提醒时间
                await asyncio.sleep(wait_seconds)
                
                # 重置重试计数
                retry_count = 0
                
                # 发送提醒
                _log.info("定时器触发,准备发送提醒")
                await self.send_reminder(self.client)
                
                # 记录成功发送的日志
                _log.info("提醒已成功发送")
                # await self.admin_send_email("今日提醒已成功发送")
                
                # 短暂等待,避免在同一分钟内重复发送
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                _log.info("定时器被取消")
                break
            except Exception as e:
                retry_count += 1
                _log.error(f"定时器出错 (尝试 {retry_count}/{max_retries}): {e}")
                
                if retry_count >= max_retries:
                    _log.critical(f"定时器在 {max_retries} 次尝试后仍然失败,等待较长时间后重试")
                    retry_count = 0
                    await asyncio.sleep(3600)  # 出错多次后等待一小时再继续
                else:
                    await asyncio.sleep(60 * retry_count)  # 重试前等待时间逐渐增加

    async def start_reminder(self, client):
        """启动定时调度器"""
        if self.scheduler_task is not None:
            self.scheduler_task.cancel()  

        self.scheduler_task = asyncio.create_task(self.reminder_scheduler(self.client))
        _log.info("定时提醒调度器已启动")
        
    async def start_update_index(self, client):
        if self.update_index is not None:
            self.update_index.cancel()
        
        self.update_index = asyncio.create_task(self.update_indexer(self.client))
        _log.info("定时索引更新已启动")

    def add_member(self, name, qq_id):
        """添加成员"""
        # 检查成员是否已存在
        for member in self.members_data["members"]:
            if member["qq_id"] == qq_id:
                return False, "该成员已存在"
                
        # 生成新ID
        new_id = 1
        if self.members_data["members"]:
            new_id = max(member["id"] for member in self.members_data["members"]) + 1
            
        # 添加新成员
        self.members_data["members"].append({
            "id": new_id,
            "name": name,
            "qq_id": qq_id
        })
        self.save_members()
        return True, f"成功添加成员 {name}(ID:{new_id})"

    def remove_member(self, qq_id):
        """删除成员"""
        original_count = len(self.members_data["members"])
        self.members_data["members"] = [
            member for member in self.members_data["members"] 
            if member["qq_id"] != qq_id
        ]
        
        if len(self.members_data["members"]) < original_count:
            # 确保current_index不会越界
            if self.members_data["members"]:
                self.members_data["current_index"] = min(
                    self.members_data["current_index"],
                    len(self.members_data["members"]) - 1
                )
            else:
                self.members_data["current_index"] = 0
                
            self.save_members()
            return True, "成员删除成功"
        else:
            return False, "未找到该成员"

    def add_holiday(self, date_str):
        """添加假期"""
        try:
            # 验证日期格式 MM-DD
            datetime.strptime(date_str, "%m-%d")
            
            if date_str in self.config["holiday_whitelist"]:
                return False, "该日期已在假期列表中"
                
            self.config["holiday_whitelist"].append(date_str)
            self.save_config()
            return True, f"成功添加假期 {date_str}"
        except ValueError:
            return False, "日期格式错误,请使用MM-DD格式"
        
    def remove_holiday(self, date_str):
        """删除假期"""
        if date_str in self.config["holiday_whitelist"]:
            self.config["holiday_whitelist"].remove(date_str)
            self.save_config()
            return True, f"成功删除假期 {date_str}"
        else:
            return False, "该日期不在假期列表中"

    def set_reminder_time(self, time_str):
        """设置提醒时间"""
        try:
            # 验证时间格式 HH:MM
            datetime.strptime(time_str, "%H:%M")
            
            self.config["reminder_time"] = time_str
            self.save_config()
            #重启定时器
            #定时提醒任务
            asyncio.create_task(self.start_reminder(self))
            return True, f"提醒时间已设置为 {time_str}"
        except ValueError:
            return False, "时间格式错误,请使用HH:MM格式"
    def set_index_update_time(self, time_str):
        try:
            datetime.strptime(time_str, "%H:%M:%S")

            self.config["index_update_time"] = time_str
            self.save_config()
            #重启定时器
            #定时更新索引任务
            asyncio.create_task(self.start_update_index(self))
            return True, f"索引更新时间已设置为 {time_str}"
        except ValueError:
            return False, "时间格式错误,请使用HH:MM:SS格式"
    def toggle_enabled(self, enabled=None):
        """切换启用状态"""
        if enabled is None:
            self.config["enabled"] = not self.config["enabled"]
        else:
            self.config["enabled"] = enabled
            
        self.save_config()
        status = "启用" if self.config["enabled"] else "禁用"
        return True, f"提醒功能已{status}"

    def toggle_silent_mode(self, silent=None):
        """切换静默模式"""
        if silent is None:
            self.config["silent_mode"] = not self.config["silent_mode"]
        else:
            self.config["silent_mode"] = silent
            
        self.save_config()
        status = "开启" if self.config["silent_mode"] else "关闭"
        return True, f"静默模式已{status}"

    def reset_rotation(self):
        """重置轮换"""
        self.members_data["current_index"] = 0
        self.members_data["last_reminder_date"] = ""  # 重置最后提醒日期
        self.save_members()
        _log.info("轮换已重置")
    def restart_task(self):
        """重启任务"""
        asyncio.create_task(self.start_reminder(self))
        asyncio.create_task(self.start_update_index(self))
        _log.info("任务已重启")
        return True, "所有任务已成功重启"

    def get_current_member(self):
        """获取当前值日人员信息"""
        if not self.members_data["members"]:
            return "当前没有设置值日人员"
            
        # 确保 current_index 在有效范围内
        if self.members_data["current_index"] >= len(self.members_data["members"]):
            self.members_data["current_index"] = 0
            self.save_members()
            
        current_member = self.members_data["members"][self.members_data["current_index"]]
        return f"今日值日人员: {current_member['name']} (ID: {current_member['id']})"

    def get_status(self):
        """获取当前状态"""
        enabled = "启用" if self.config["enabled"] else "禁用"
        silent = "开启" if self.config["silent_mode"] else "关闭"
        
        # 获取当前值日人员
        current_member = self.get_current_member()
        if current_member == "当前没有设置值日人员":
            current_member = "无"
        
        # 获取下一个值日人员
        next_member = self.get_next_member()
        next_member_name = "无" if not isinstance(next_member, dict) else next_member["name"]
        next_member_index = next_member["id"]
        #发送状态
        sendered = self.config["sender?"]
        if sendered == True:
            senderedtext = "已发送"
        else:
            senderedtext = "未发送"

        text = (
            f"状态:\n"
            f"今天: {datetime.now().year}-{datetime.now().month}-{datetime.now().day}\n"
            f"提醒功能: {enabled} (今日{senderedtext}提醒)\n"
            f"静默模式: {silent}\n"
            f"提醒时间: {self.config['reminder_time']}\n"
            f"索引更新时间: {self.config['index_update_time']}\n"
            f"今日值日: {current_member}\n"
            f"下一位值日: {next_member_name}(ID:{next_member_index})\n"
            f"成员数量: {len(self.members_data['members'])}\n"
            f"假期数量: {len(self.config['holiday_whitelist'])}"
        )
        return (text)

    def list_members(self):
        """列出所有成员"""
        if not self.members_data["members"]:
            return "当前没有成员"
        
        member_list = "\n".join([
            f"{member['id']}. {member['name']} (QQ: {member['qq_id']})"
            for member in self.members_data["members"]
        ])
        return f"成员列表:\n{member_list}"

    def list_holidays(self):
        """列出所有假期"""
        if not self.config["holiday_whitelist"]:
            return "目前没有设置假期白名单"
        
        holidays = ", ".join(self.config["holiday_whitelist"])
        return f"假期白名单: {holidays}"

    def set_email_config(self, smtp_server: str, smtp_port: int, sender_email: str, sender_password: str, subject: str = "扫地提醒"):
        """设置邮件配置
        
        Args:
            smtp_server: SMTP服务器地址
            smtp_port: SMTP服务器端口
            sender_email: 发件人邮箱
            sender_password: 发件人密码
            subject: 邮件主题
        """
        self.config["email_config"] = {
            "smtp_server": smtp_server,
            "smtp_port": smtp_port,
            "sender_email": sender_email,
            "sender_password": sender_password,
            "subject": subject
        }
        self.save_config()
        return True, "邮件配置已更新"

    def remove_member_by_id(self, member_id):
        """通过ID删除成员"""
        try:
            member_id = int(member_id)
            original_count = len(self.members_data["members"])
            self.members_data["members"] = [
                member for member in self.members_data["members"] 
                if member["id"] != member_id
            ]
            
            if len(self.members_data["members"]) < original_count:
                # 确保current_index不会越界
                if self.members_data["members"]:
                    self.members_data["current_index"] = min(
                        self.members_data["current_index"],
                        len(self.members_data["members"]) - 1
                    )
                else:
                    self.members_data["current_index"] = 0
                    
                self.save_members()
                return True, "成员删除成功"
            else:
                return False, "未找到该成员"
        except ValueError:
            return False, "ID格式错误,请输入数字"

    def set_current_member(self, member_id):
        """设置当前值日人员"""
        try:
            member_id = int(member_id)
            # 查找成员
            for i, member in enumerate(self.members_data["members"]):
                if member["id"] == member_id:
                    self.members_data["current_index"] = i
                    self.save_members()
                    return True, f"已设置当前值日人员为: {member['name']}"
            return False, "未找到该成员"
        except ValueError:
            return False, "ID格式错误,请输入数字" 