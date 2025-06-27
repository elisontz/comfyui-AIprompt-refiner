# -*- coding: utf-8 -*-
import requests
import json
from typing import Tuple
import urllib.parse

# 从共享文件中导入通用配置和函数
from .common import SERVICE_CONFIG, clean_text, load_preset_configs

class AITranslator:
    """
    一个使用外部AI服务和传统服务进行中英文互译的节点。
    """
    
    TRADITIONAL_SERVICES = ["Google Translate", "MyMemory Translate"]
    
    @classmethod
    def INPUT_TYPES(cls):
        # 在需要时才加载配置文件
        preset_configs = load_preset_configs()
        preset_names = [config["name"] for config in preset_configs]

        # 如果没有AI配置，下拉菜单只显示传统服务
        all_services = cls.TRADITIONAL_SERVICES + preset_names
        if not preset_names:
             all_services = cls.TRADITIONAL_SERVICES
             print("⚠️ 未找到AI配置，翻译器将只提供传统服务。")

        return {
            "required": {
                "text_to_translate": ("STRING", {"multiline": True, "default": "", "tooltip": "输入您想要翻译的文本。"}),
                "translation_direction": (["中文 -> 英文", "英文 -> 中文"], {"default": "中文 -> 英文", "tooltip": "选择翻译方向。"}),
                "service_selection": (all_services, {"default": "Google Translate", "tooltip": "选择翻译服务或您在config.json中定义的AI配置。"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("翻译后的文本",)
    FUNCTION = "translate"
    CATEGORY = "AI提示词工具" 

    def _get_config_details(self, selection):
        # 每次都重新加载配置，以反映用户可能在运行时对文件的修改
        for preset in load_preset_configs():
            if preset["name"] == selection:
                print(f"✅ 使用配置文件 '{selection}'")
                return preset
        
        raise ValueError(f"找不到名为 '{selection}' 的配置。请重启ComfyUI或检查config.json文件。")

    def _google_translate(self, text: str, direction: str) -> str:
        source_lang, target_lang = ("zh-CN", "en") if direction == "中文 -> 英文" else ("en", "zh-CN")
        url = "https://translate.googleapis.com/translate_a/single"
        params = {"client": "gtx", "sl": source_lang, "tl": target_lang, "dt": "t", "q": text}
        print("🚀 正在调用 Google Translate API...")
        response = requests.get(url, params=params, timeout=20, verify=False)
        response.raise_for_status()
        try:
            return "".join([item[0] for item in response.json()[0] if item[0]])
        except (IndexError, TypeError):
            raise ValueError(f"无法解析来自 Google Translate 的响应: {response.text}")

    def _mymemory_translate(self, text: str, direction: str) -> str:
        source_lang, target_lang = ("zh-CN", "en") if direction == "中文 -> 英文" else ("en", "zh-CN")
        email = "user@example.com"
        url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair={source_lang}|{target_lang}&de={email}"
        print("🚀 正在调用 MyMemory Translate API...")
        response = requests.get(url, timeout=20, verify=False)
        response.raise_for_status()
        data = response.json()
        if data.get("responseStatus") == 200:
            return data["responseData"]["translatedText"]
        else:
            raise ValueError(f"MyMemory API 返回错误: {data.get('responseDetails')}")

    def translate(self, text_to_translate: str, translation_direction: str, service_selection: str) -> Tuple[str]:
        if not text_to_translate.strip():
            return ("",)
        try:
            translated_text = ""
            if service_selection in self.TRADITIONAL_SERVICES:
                if service_selection == "Google Translate": 
                    translated_text = self._google_translate(text_to_translate, translation_direction)
                elif service_selection == "MyMemory Translate":
                    translated_text = self._mymemory_translate(text_to_translate, translation_direction)
            
            else: # Is an AI Service
                config = self._get_config_details(service_selection)
                service_type = config.get("type")
                final_key = config.get("api_key")
                api_url = config.get("api_base")
                model = config.get("model")
                
                headers = {"Content-Type": "application/json"}
                system_prompt = "You are a professional translator. Translate the following Chinese text to English. Only return the translated English text, without any explanations or extra content." if translation_direction == "中文 -> 英文" else "You are a professional translator. Translate the following English text to Chinese. Only return the translated Chinese text, without any explanations or extra content."

                if service_type == "Gemini":
                    if "key=" not in api_url: api_url = f"{api_url}?key={final_key}"
                    payload = {"contents": [{"parts": [{"text": f"{system_prompt}\n\n{text_to_translate}"}]}]}
                else:
                    headers["Authorization"] = f"Bearer {final_key}"
                    payload = {"model": model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": text_to_translate}]}

                print(f"🚀 正在调用 {service_type} API ({api_url}, 模型: {model}) 进行翻译...")
                response = requests.post(api_url, headers=headers, data=json.dumps(payload), timeout=180)
                response.raise_for_status()
                
                try:
                    data = response.json()
                except requests.exceptions.JSONDecodeError:
                    error_text = response.text
                    print(f"❌ 解析JSON失败！服务器返回的不是有效的JSON格式。")
                    print(f"👇 服务器原始响应内容: \n---\n{error_text}\n---")
                    raise ValueError(f"服务器返回内容无法解析，请检查API地址或密钥是否正确。")

                translated_text = data['candidates'][0]['content']['parts'][0]['text'] if service_type == "Gemini" else data['choices'][0]['message']['content']

            final_text = clean_text(translated_text)
            print("✅ 翻译成功。")
            return (final_text,)

        except Exception as e:
            error_msg = f"❌ 翻译失败: {str(e)}"
            print(error_msg)
            return (f"错误: {error_msg}\n\n原文: {text_to_translate}",)

NODE_CLASS_MAPPINGS = { "AITranslator": AITranslator }
NODE_DISPLAY_NAME_MAPPINGS = { "AITranslator": "AI翻译器" }
