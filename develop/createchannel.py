#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import requests
from typing import Dict, List, Optional, Any
import traceback
import argparse
import logging as py_logging
from botpy.ext.cog_yaml import read
from botpy import logging

# 配置日志以显示更多信息
py_logging.basicConfig(level=py_logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.get_logger()

class ChannelCreator:
    """QQ频道子频道创建器"""
    
    def __init__(self, appid: str = None, secret: str = None):
        if not appid or not secret:
            config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
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
        
        # 使用正式环境API地址
        self.base_url = "https://api.sgroup.qq.com"
        self.access_token = self.get_access_token()
        print(f"使用API地址: {self.base_url}")

    def get_access_token(self) -> str:
        """获取访问令牌"""
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
            resp.raise_for_status()
            result = resp.json()
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

    def get_guild_list(self) -> List[Dict[str, Any]]:
        """获取机器人加入的服务器列表"""
        url = f"{self.base_url}/users/@me/guilds"
        headers = {
            "Authorization": f"QQBot {self.access_token}"
        }
        print(f"正在请求服务器列表，URL: {url}")
        try:
            response = requests.get(url, headers=headers)
            print(f"服务器列表请求状态码: {response.status_code}")
            response.raise_for_status()
            result = response.json()
            if isinstance(result, list):
                print(f"获取到 {len(result)} 个服务器")
                return result
            else:
                print(f"获取服务器列表失败，响应格式不正确: {result}")
                return []
        except Exception as e:
            print(f"获取服务器列表异常: {str(e)}")
            return []

    def create_channel(self, guild_id: str, name: str, channel_type: int = 0, 
                      parent_id: str = "0", private_type: int = 0, 
                      speak_permission: int = 0) -> Optional[Dict[str, Any]]:
        """创建子频道
        
        Args:
            guild_id: 服务器ID
            name: 子频道名称
            channel_type: 子频道类型，0:文字频道，1:语音频道
            parent_id: 父频道ID，如果是顶级频道则为0
            private_type: 子频道类型，0:公开频道，1:私密频道
            speak_permission: 发言权限，0:所有人可发言，1:仅管理员可发言
            
        Returns:
            Dict[str, Any]: 创建的子频道信息，失败返回None
        """
        url = f"{self.base_url}/guilds/{guild_id}/channels"
        headers = {
            "Authorization": f"QQBot {self.access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "name": name,
            "type": channel_type,
            "position": 0,
            "parent_id": parent_id,
            "private_type": private_type,
            "speak_permission": speak_permission
        }
        
        print(f"正在创建子频道，URL: {url}")
        print(f"创建参数: {json.dumps(data, ensure_ascii=False)}")
        
        try:
            response = requests.post(url, headers=headers, json=data)
            print(f"创建子频道请求状态码: {response.status_code}")
            response.raise_for_status()
            result = response.json()
            print(f"创建子频道响应: {json.dumps(result, ensure_ascii=False)}")
            return result
        except Exception as e:
            print(f"创建子频道异常: {str(e)}")
            logger.error(f"创建子频道异常: {str(e)}")
            logger.error(traceback.format_exc())
            return None

def main():
    # 读取创建配置
    create_config_path = os.path.join(os.path.dirname(__file__), "createconfig.yaml")
    if not os.path.exists(create_config_path):
        print(f"创建配置文件不存在: {create_config_path}")
        return
        
    create_config = read(create_config_path)
    channels = create_config.get("channels", [])
    if not channels:
        print("配置文件中没有找到子频道配置")
        return
        
    creator = ChannelCreator()
    
    # 获取服务器ID
    guild_id = create_config.get("guild_id", "")
    if not guild_id:
        guilds = creator.get_guild_list()
        if not guilds:
            print("未获取到任何服务器信息")
            return
            
        print("\n可用的服务器列表：")
        for i, guild in enumerate(guilds, 1):
            print(f"{i}. {guild.get('name', '未命名服务器')} (ID: {guild.get('id')})")
            
        choice = input("\n请选择服务器编号（输入数字）: ")
        try:
            guild_index = int(choice) - 1
            if 0 <= guild_index < len(guilds):
                guild_id = guilds[guild_index].get('id')
            else:
                print("无效的选择")
                return
        except ValueError:
            print("请输入有效的数字")
            return
    
    # 创建所有配置的子频道
    print(f"\n开始创建子频道，服务器ID: {guild_id}")
    for channel in channels:
        name = channel.get("name")
        if not name:
            print("跳过未命名的子频道配置")
            continue
            
        print(f"\n正在创建子频道: {name}")
        result = creator.create_channel(
            guild_id=guild_id,
            name=name,
            channel_type=channel.get("type", 0),
            parent_id=channel.get("parent_id", "0"),
            private_type=channel.get("private", 0),
            speak_permission=channel.get("speak", 0)
        )
        
        if result:
            print(f"成功创建子频道：{name}")
            print(f"子频道ID: {result.get('id')}")
        else:
            print(f"创建子频道失败：{name}")

if __name__ == "__main__":
    main() 