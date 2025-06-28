# -*- coding: utf-8 -*-
import torch
import numpy as np
from PIL import Image
import io
import base64
import requests
import json
import re
from typing import Tuple

# 从共享文件中导入通用配置和函数
from .common import SERVICE_CONFIG, clean_text, load_preset_configs

class AIPromptRefiner:
    """
    AI提示词优化工具，一个支持多种大模型服务的ComfyUI节点。
    """
    
    NEGATIVE_PROMPTS = {
        "基础模板": "worst quality, low quality, watermark, signature, text, error, blurry",
        "通用高质量": "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, artist name, deformed, distorted, disfigured",
        "完美人像(通用)": "bad hands, bad fingers, missing fingers, extra fingers, ugly, deformed, noisy, blurry, distorted, grainy, extra limbs, missing limbs, disconnected limbs, malformed hands, mutated hands, poorly drawn hands, extra head, malformed, (mutated hands and fingers:1.4)",
        "完美人像(写实)": "deformed, distorted, disfigured, poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, (mutated hands and fingers:1.4), disconnected limbs, mutation, mutated, ugly, disgusting, blurry, amputation, realisticface",
        "动漫优化": "bad hands, bad fingers, missing fingers, extra fingers, ugly, deformed, noisy, blurry, distorted, grainy"
    }

    @classmethod
    def INPUT_TYPES(cls):
        preset_configs = load_preset_configs()
        preset_names = [config["name"] for config in preset_configs]
        if not preset_names:
            preset_names = ["未找到配置,请检查config.json"]

        style_options = [
            "通用", "摄影", "写实", "动漫", "3D模型", "电影感", "概念艺术", 
            "建筑设计", "奇幻", "赛博朋克", "蒸汽朋克", "水墨画", 
            "油画", "水彩画", "素描", "像素艺术", "低多边形", "简约", "复古"
        ]
        
        target_model_options = [
            "通用", 
            "SDXL",
            "Flux"
        ]

        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "a cute cat", "tooltip": "输入基础的文本提示词。"}),
                "config_selection": (preset_names, {"default": preset_names[0] if preset_names else "", "tooltip": "从您的 config.json 文件中选择一个预设配置。"}),
                "target_model": (target_model_options, {"default": "Flux", "tooltip": "选择目标模型的提示词风格，以获得最佳效果。"}),
                "strict_mode": ("BOOLEAN", {"default": True, "label_on": "规范输出", "label_off": "创意模式", "tooltip": "建议开启，以确保AI返回格式正确，便于解析。"}),
                "style": (style_options, {"default": "通用", "tooltip": "选择最终提示词的艺术风格。"}),
                "detail_level": (["基础", "详细", "极其详细"], {"default": "基础", "tooltip": "控制生成提示词的细节程度。"}),
                "negative_mode": (list(cls.NEGATIVE_PROMPTS.keys()) + ["自定义"], {"default": "基础模板", "tooltip": "选择负面提示词模板。"}),
                "custom_negative": ("STRING", {"multiline": True, "default": "", "tooltip": "当选择“自定义”负面模式时，此处内容生效。"}),
            },
            "optional": { "image": ("IMAGE", {"tooltip": "(可选) 连接图片以启用“图生文”模式。"}) }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("优化后的提示词", "负面提示词", "优化笔记")
    FUNCTION = "refine_prompt"
    CATEGORY = "AI提示词工具"

    def _get_config_details(self, selection):
        for preset in load_preset_configs():
            if preset["name"] == selection:
                print(f"✅ 使用配置文件 '{selection}'")
                return preset
        
        raise ValueError(f"找不到名为 '{selection}' 的配置。请重启ComfyUI或检查config.json文件。")

    def _tensor_to_base64(self, tensor: torch.Tensor) -> str:
        image_np = tensor.squeeze(0).cpu().numpy()
        image_np = (image_np * 255).astype(np.uint8)
        pil_image = Image.fromarray(image_np)
        max_dim = 2048
        if pil_image.width > max_dim or pil_image.height > max_dim:
            pil_image.thumbnail((max_dim, max_dim))
            print(f"ℹ️ 图片尺寸已调整为 {pil_image.size} 以符合API限制。")
        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def _get_style_map(self):
        return {
            "通用": "General", "摄影": "Photographic", "写实": "Realistic", "动漫": "Anime", "3D模型": "3D Model", 
            "电影感": "Cinematic", "概念艺术": "Concept Art", "建筑设计": "Architectural", "奇幻": "Fantasy", 
            "赛博朋克": "Cyberpunk", "蒸汽朋克": "Steampunk", "水墨画": "Ink Wash Painting", "油画": "Oil Painting", 
            "水彩画": "Watercolor", "素描": "Sketch", "像素艺术": "Pixel Art", "低多边形": "Low Poly", 
            "简约": "Minimalist", "复古": "Vintage"
        }

    def _build_text_system_prompt(self, style: str, detail_level: str, strict_mode: bool, target_model: str) -> str:
        strict_instruction = " Your entire response must strictly follow the format: [EN] english prompt [ZH] chinese optimization notes." if strict_mode else ""
        
        style_map = self._get_style_map()
        detail_map = {"基础": "Basic", "详细": "Detailed", "极其详细": "Ultra Detailed"}
        
        style_en = style_map.get(style, 'General')
        detail_en = detail_map.get(detail_level, 'Basic')

        # --- 核心修正: 明确告知AI工作环境并禁止外部参数 ---
        ecosystem_context = (
            "You are an expert prompt engineer for the **ComfyUI / Stable Diffusion ecosystem**. "
            "Your output will be used directly in these systems. "
            "**Crucially, do NOT include any platform-specific parameters like `--ar`, `--v`, `--style`, etc.** "
            "Focus only on the descriptive text part of the prompt."
        )

        if target_model == "Flux":
            prompt_style_instructions = (
                "You are generating a prompt for the **Flux model**. "
                "This model excels at understanding natural, descriptive language. "
                "Your task is to enhance the user's idea into a rich, descriptive prompt that works best for Flux."
            )
        elif target_model == "SDXL":
            prompt_style_instructions = (
                "You are generating a prompt for the **SDXL model**. "
                "This model understands detailed descriptions and keyword-based prompts well. "
                "Your task is to enhance the user's idea into a powerful and effective prompt that works best for SDXL."
            )
        else:
             prompt_style_instructions = (
                "You are generating a prompt for **general Stable Diffusion models (v1.5, etc.)**. "
                "These models respond best to structured, keyword-rich prompts with clear tags. "
                "Your task is to enhance the user's idea into a powerful and effective prompt in this style."
            )

        style_instruction = (
            f"It is crucial that the new prompt strongly reflects the '{style_en}' artistic style. "
            f"Infuse specific keywords, artist names, or descriptive phrases characteristic of the '{style_en}' style."
        )
        if style_en == "General":
             style_instruction = "Your goal is to create a universally effective and detailed prompt."

        return (
            f"{ecosystem_context}\n\n"
            "Your primary task is to take a user's basic idea and transform it into a highly effective prompt based on the user's chosen target model style."
            f"{strict_instruction}\n\n"
            "## Core Instructions\n"
            f"{prompt_style_instructions}\n\n"
            "## Task\n"
            "1. Rewrite the user's idea into a prompt following all the Core Instructions for the chosen style.\n"
            f"2. {style_instruction}\n"
            f"3. The level of detail should be '{detail_en}'.\n"
            "4. Provide the final English prompt and Chinese optimization notes in the required format."
        )

    def refine_prompt(self, prompt: str, config_selection: str, target_model: str, strict_mode: bool, style: str, 
                        detail_level: str, negative_mode: str, custom_negative: str, 
                        image: torch.Tensor = None) -> Tuple[str, str, str]:
        try:
            config = self._get_config_details(config_selection)
            service_type = config.get("type")
            final_key = config.get("api_key")
            api_url = config.get("api_base")
            model = config.get("model")
            
            temp_config = SERVICE_CONFIG.get(service_type, SERVICE_CONFIG["ChatGPT"]) 
            temperature = temp_config["temperature_map"].get(detail_level, 0.5)

            headers = {"Content-Type": "application/json"}
            payload = {}

            if image is not None:
                if service_type == "DeepSeek":
                    raise ValueError("DeepSeek 在此节点中当前不支持图片输入。请使用 Gemini 或 ChatGPT 进行视觉分析。")
                print("🖼️ 检测到图片，切换到视觉分析模式。")
                base64_image = self._tensor_to_base64(image)
                
                style_map = self._get_style_map()
                detail_map = {"基础": "Basic", "详细": "Detailed", "极其详细": "Ultra Detailed"}
                style_en = style_map.get(style, 'General')
                detail_en = detail_map.get(detail_level, 'Basic')

                system_prompt_text = (
                    "You are an expert in analyzing images and creating descriptive prompts for AI image generation within the **ComfyUI / Stable Diffusion ecosystem**. "
                    "First, describe the provided image in detail. Then, use that description to generate a new, optimized prompt. "
                    f"The prompt should be suitable for a '{target_model}' model. Follow its best practices. "
                    "**Crucially, do NOT include any platform-specific parameters like `--ar`, `--v`, `--style`, etc.**"
                )
                user_prompt_text = f"Analyze the image, then create a new prompt. The desired art style is '{style_en}' and detail level is '{detail_en}'. User's additional instruction: '{prompt}'"
                
                strict_instruction = " Your entire response must strictly follow the format: [EN] english prompt [ZH] chinese optimization notes." if strict_mode else ""
                user_prompt_text += f"\n\n{strict_instruction}"

                if service_type == "Gemini":
                    if "key=" not in api_url: api_url = f"{api_url}?key={final_key}"
                    final_user_text = f"{system_prompt_text}\n\n{user_prompt_text}"
                    payload = { "contents": [{"parts": [ {"text": final_user_text}, {"inline_data": {"mime_type": "image/jpeg", "data": base64_image}} ]}], "generationConfig": {"temperature": temperature} }
                else:
                    headers["Authorization"] = f"Bearer {final_key}"
                    payload = { "model": model, "messages": [ {"role": "system", "content": system_prompt_text}, {"role": "user", "content": [ {"type": "text", "text": user_prompt_text}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}} ]} ], "temperature": temperature, "max_tokens": 2048 }
            else:
                print("✍️ 未提供图片，在纯文本模式下运行。")
                system_prompt_text = self._build_text_system_prompt(style, detail_level, strict_mode, target_model)
                if service_type == "Gemini":
                    if "key=" not in api_url: api_url = f"{api_url}?key={final_key}"
                    payload = {"contents": [{"parts": [{"text": f"{system_prompt_text}\n\nUser idea: {prompt}"}]}], "generationConfig": {"temperature": temperature}}
                else:
                    headers["Authorization"] = f"Bearer {final_key}"
                    payload = {"model": model, "messages": [{"role": "system", "content": system_prompt_text}, {"role": "user", "content": prompt}], "temperature": temperature}

            print(f"🚀 正在调用 {service_type} API ({api_url}，模型: {model})...")
            response = requests.post(api_url, headers=headers, data=json.dumps(payload), timeout=180)
            response.raise_for_status()

            try:
                data = response.json()
            except requests.exceptions.JSONDecodeError:
                error_text = response.text
                print(f"❌ 解析JSON失败！服务器返回的不是有效的JSON格式。")
                print(f"👇 服务器原始响应内容: \n---\n{error_text}\n---")
                raise ValueError(f"服务器返回内容无法解析，请检查API地址或密钥是否正确。")

            tokens_used_text = ""
            if service_type in ["ChatGPT", "DeepSeek"]:
                if 'usage' in data and 'total_tokens' in data['usage']:
                    tokens_used_text = f"Tokens: {data['usage']['total_tokens']}. "
                    print(f"🪙 Tokens 已使用: {data['usage']['total_tokens']}")
            
            content = data['candidates'][0]['content']['parts'][0]['text'] if service_type == "Gemini" else data['choices'][0]['message']['content']
            
            en_part_match = re.search(r"\[EN\](.*?)\[ZH\]", content, re.DOTALL)
            optimized_prompt = clean_text(en_part_match.group(1)) if en_part_match else "⚠️ 解析优化后的提示词失败。检查AI是否返回了[EN]...[ZH]...格式。"
            
            optimization_notes = content
            
            negative_prompt_text = clean_text(custom_negative) if negative_mode == "自定义" else self.NEGATIVE_PROMPTS.get(negative_mode, "")
            
            print("🎉 提示词优化完成！")
            return (optimized_prompt, negative_prompt_text, optimization_notes)

        except Exception as e:
            error_msg = f"❌ 发生错误: {str(e)}"
            print(error_msg)
            return (prompt, "", error_msg)

NODE_CLASS_MAPPINGS = { "AIPromptRefiner": AIPromptRefiner }
NODE_DISPLAY_NAME_MAPPINGS = { "AIPromptRefiner": "AI提示词优化器" }
