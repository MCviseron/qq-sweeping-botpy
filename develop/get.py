#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import requests
from typing import Dict, List, Optional, Any, Tuple
import traceback
import logging as py_logging
from botpy.ext.cog_yaml import read
from botpy import logging

# 配置日志以显示更多信息
py_logging.basicConfig(level=py_logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.get_logger()

class ChannelGetter:
    def __init__(self, appid: str = None, secret: str = None):
        if not appid or not secret:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
            print(f"正在尝试读取配置文件: {config_path}")
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"配置文件不存在: {config_path}")
            config = read(config_path)
            self.appid = config.get("appid")
            self.secret = config.get("secret")
            print(f"从配置文件读取的APPID: {self.appid}")
            if not self.appid or not self.secret:
                raise ValueError("配置文件缺少必要的appid或secret")
        else:
            self.appid = appid
            self.secret = secret
        # 使用沙箱环境API地址
        self.base_url = "https://sandbox.api.sgroup.qq.com"
        self.access_token = self.get_access_token()
        print(f"使用API地址: {self.base_url}")

    def get_access_token(self) -> str:
        url = "https://bots.qq.com/app/getAppAccessToken"
        data = {
            "appId": self.appid,
            "clientSecret": self.secret
        }
        headers = {"Content-Type": "application/json"}
        print(f"正在请求access_token，URL: {url}")
        try:
            resp = requests.post(url, json=data, headers=headers)
            print(f"access_token请求状态码: {resp.status_code}")
            print(f"请求数据: {data}")
            resp.raise_for_status()
            result = resp.json()
            print(f"access_token响应: {result}")
            if "access_token" in result:
                print("成功获取access_token")
                return result["access_token"]
            else:
                raise Exception(f"获取access_token失败: {result}")
        except Exception as e:
            print(f"获取access_token异常: {str(e)}")
            logger.error(f"获取access_token异常: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def get_guild_list(self) -> list:
        """获取机器人加入的频道列表"""
        url = f"{self.base_url}/users/@me/guilds"
        headers = {
            "Authorization": f"QQBot {self.access_token}"
        }
        print(f"正在请求服务器列表，URL: {url}")
        try:
            response = requests.get(url, headers=headers)
            print(f"服务器列表请求状态码: {response.status_code}")
            print(f"请求头: {headers}")
            print(f"服务器列表原始响应: {response.text}")
            response.raise_for_status()
            result = response.json()
            if isinstance(result, list):
                print(f"获取到 {len(result)} 个服务器")
                return result
            else:
                print(f"获取服务器列表失败，响应格式不正确: {result}")
                logger.error(f"获取服务器列表失败: {result}")
                return []
        except Exception as e:
            print(f"获取服务器列表异常: {str(e)}")
            logger.error(f"获取服务器列表异常: {str(e)}")
            logger.error(traceback.format_exc())
            return []

    def get_channel_list(self, guild_id: str) -> list:
        """获取频道下的子频道列表"""
        url = f"{self.base_url}/guilds/{guild_id}/channels"
        headers = {
            "Authorization": f"QQBot {self.access_token}"
        }
        print(f"正在请求频道列表，URL: {url}, 服务器ID: {guild_id}")
        try:
            response = requests.get(url, headers=headers)
            print(f"频道列表请求状态码: {response.status_code}")
            print(f"请求头: {headers}")
            response.raise_for_status()
            result = response.json()
            print(f"频道列表响应: {result}")
            if isinstance(result, list):
                print(f"获取到 {len(result)} 个频道")
                return result
            else:
                print(f"获取频道列表失败，响应格式不正确: {result}")
                logger.error(f"获取频道列表失败: {result}")
                return []
        except Exception as e:
            print(f"获取频道列表异常: {str(e)}")
            logger.error(f"获取频道列表异常: {str(e)}")
            logger.error(traceback.format_exc())
            return []

    def get_guild_info(self, guild_id: str) -> dict:
        """获取频道详细信息"""
        url = f"{self.base_url}/guilds/{guild_id}"
        headers = {
            "Authorization": f"QQBot {self.access_token}"
        }
        print(f"正在请求频道信息，URL: {url}")
        try:
            response = requests.get(url, headers=headers)
            print(f"频道信息请求状态码: {response.status_code}")
            print(f"请求头: {headers}")
            response.raise_for_status()
            result = response.json()
            print(f"频道信息响应: {result}")
            return result
        except Exception as e:
            print(f"获取频道信息异常: {str(e)}")
            logger.error(f"获取频道信息异常: {str(e)}")
            logger.error(traceback.format_exc())
            return {}

def main():
    try:
        # 创建获取器实例
        getter = ChannelGetter()
        
        # 获取频道列表
        guilds = getter.get_guild_list()
        if not guilds:
            print("未找到任何频道")
            sys.exit(1)
            
        # 显示频道列表
        print("\n可用的频道:")
        print("=" * 50)
        print("注意：频道ID就是主频道ID，用于发帖功能")
        print("=" * 50)
        for i, guild in enumerate(guilds, 1):
            print(f"{i}. {guild['name']}")
            print(f"   └─ 主频道ID: {guild['id']} (用于发帖)")
            
        # 选择频道
        while True:
            try:
                choice = int(input("\n请选择要查看的频道编号: "))
                if 1 <= choice <= len(guilds):
                    selected_guild = guilds[choice - 1]
                    break
                else:
                    print("无效的选择，请重试")
            except ValueError:
                print("请输入有效的数字")
                
        # 获取频道详细信息
        guild_info = getter.get_guild_info(selected_guild["id"])
        if guild_info:
            print(f"\n频道详细信息:")
            print("=" * 50)
            print(f"名称: {guild_info.get('name')}")
            print(f"主频道ID: {guild_info.get('id')} (用于发帖)")
            print(f"描述: {guild_info.get('description', '无')}")
            print(f"成员数: {guild_info.get('member_count', '未知')}")
            print(f"最大成员数: {guild_info.get('max_members', '未知')}")
            print(f"创建时间: {guild_info.get('joined_at', '未知')}")
            print("=" * 50)
            print("提示：将此主频道ID配置到config.json的channel_id字段中")
            print("=" * 50)
            
        # 获取子频道列表
        channels = getter.get_channel_list(selected_guild["id"])
        if channels:
            print(f"\n{selected_guild['name']} 的子频道:")
            print("=" * 50)
            print("注意：子频道ID用于其他功能，发帖请使用主频道ID")
            print("=" * 50)
            for i, channel in enumerate(channels, 1):
                channel_type = {
                    0: "文字频道",
                    1: "语音频道",
                    2: "直播频道",
                    3: "应用频道",
                    4: "论坛频道",
                    5: "帖子频道"
                }.get(channel.get('type', 0), "未知类型")
                print(f"{i}. {channel['name']}")
                print(f"   └─ 子频道ID: {channel['id']} (类型: {channel_type})")
            
    except Exception as e:
        print(f"程序执行出错: {str(e)}")
        logger.error(f"程序执行出错: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 