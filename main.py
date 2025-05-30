#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import traceback
import botpy
from botpy.ext.cog_yaml import read
from botpy import logging as botpy_logging
from modules.commands import SweepingBot

def main():
    try:
        # 获取botpy日志
        logger = botpy_logging.get_logger()
        logger.info("正在启动扫地机器人...")
        
        # 读取配置文件
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
            
        config = read(config_path)
        if not config.get("appid") or not config.get("secret"):
            raise ValueError("配置文件缺少必要的appid或secret")
        
        # 设置机器人需要监听的事件通道
        # 设置intents
        intents = botpy.Intents(public_messages=True)
        
        # 创建机器人实例
        client = SweepingBot(intents=intents)
        
        # 启动机器人
        logger.info("机器人启动成功,开始运行...")
        client.run(appid=config["appid"], secret=config["secret"])
        
    except FileNotFoundError as e:
        logger.error(f"配置文件错误: {str(e)}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"配置错误: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"启动失败: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 