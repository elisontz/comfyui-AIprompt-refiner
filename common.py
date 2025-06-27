# -*- coding: utf-8 -*-
import os
import requests
import json
import inspect

# 服务配置字典，仅用于温度映射
SERVICE_CONFIG = {
    "DeepSeek": {"temperature_map": {"基础": 0.3, "详细": 0.5, "极其详细": 0.7}},
    "Gemini": {"temperature_map": {"基础": 0.2, "详细": 0.4, "极其详细": 0.6}},
    "ChatGPT": {"temperature_map": {"基础": 0.3, "详细": 0.5, "极其详细": 0.7}}
}

def get_plugin_root():
    """获取插件的根目录"""
    try:
        current_file_path = inspect.getfile(inspect.currentframe())
        return os.path.dirname(current_file_path)
    except Exception:
        return os.path.dirname(os.path.realpath(__file__))

PLUGIN_ROOT = get_plugin_root()
CONFIG_PATH = os.path.join(PLUGIN_ROOT, "config.json")

# --- 优化点: 移除缓存，实现热重载 ---
def load_preset_configs():
    """
    从插件根目录加载 config.json 文件。
    移除缓存机制，使得每次调用都会重新读取文件，
    这样用户在ComfyUI界面点击刷新即可加载新配置。
    """
    if not os.path.exists(CONFIG_PATH):
        # 即使文件不存在也不报错，而是在UI中显示提示
        return []
    
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            if "configurations" in config_data and isinstance(config_data["configurations"], list):
                print(f"✅ 成功加载 {len(config_data['configurations'])} 个预设配置。")
                return config_data["configurations"]
            else:
                print("❌ config.json 文件格式错误：缺少 'configurations' 列表。")
                return []
    except Exception as e:
        print(f"❌ 加载 config.json 文件时发生未知错误: {e}")
        return []

def clean_text(text: str) -> str:
    """清理AI返回的文本，移除不必要的字符"""
    return text.strip().replace("\n", " ").replace("\"", "")
