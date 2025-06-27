# ComfyUI AI Prompt Tools

因为太懒，懒得仔细写提示词而做的一个小插件，简单易用。本插件代码基本由AI完成，其实本人并不怎么会编程😊

一个为 ComfyUI 设计的、由大型语言模型驱动的智能小工具，旨在将繁琐的提示词工程和翻译工作自动化，让您的创作流程更顺畅、更高效。
![image](https://github.com/user-attachments/assets/4a291a4b-b8a6-42b3-ba68-37f7c1b486b4)



## ✨ 功能特性 (Features)

- **🤖 AI提示词优化器**: 将您简单的想法，通过AI一键优化成结构化、高质量、且适配不同模型的专业级提示词。
    
- **🌐 AI翻译器**: 集成了多种免费和专业的AI翻译服务，轻松实现中英文提示词的互译。
    
- **🚀 高度可配置**: 无需修改代码！通过一个简单的 `config.json` 文件，即可轻松添加和管理您自己的API服务（包括官方、第三方代理和本地模型）。
    
- **🧠 多模型适配**: "AI提示词优化器"内置了针对不同模型的优化策略，无论是为 **SDXL** 生成关键词风格的提示词，还是为 **Flux** 生成更自然的语言描述，都能轻松切换。
    
- **⚡️ 热重载**: 修改 `config.json` 文件后，无需重启ComfyUI，只需在浏览器界面点击刷新，即可加载最新的配置。
    

## 📦 安装 (Installation)

1. 打开您的终端或命令行工具。
    
2. 进入 ComfyUI 的自定义节点目录：
    
    ```
    cd path/to/your/ComfyUI/custom_nodes/
    ```
    
3. 克隆本仓库：
    
    ```
    git clone https://github.com/elisontz/comfyui-AIprompt-refiner.git
    ```
    
4. 重启 ComfyUI。
    

## 🔧 配置 (Configuration)

本插件的核心优势在于其灵活的配置系统。所有API服务都通过插件根目录下的 `config.json` 文件进行管理。

**初次使用步骤:**

1. 在插件的根目录 (`ComfyUI/custom_nodes/comfyui-AIprompt-refiner/`)下，找到 `config.json.example` 文件。
    
2. **复制**该文件并将其**重命名**为 `config.json`。
    
3. 使用文本编辑器打开 `config.json` 文件，并根据您的需求填入API信息。
    

**`config.json` 文件示例:**

```
{
  "configurations": [
    {
      "name": "官方 ChatGPT (gpt-4o)",
      "type": "ChatGPT",
      "api_key": "请在此处填入您的OpenAI API密钥 (sk-...)",
      "api_base": "https://api.openai.com/v1/chat/completions",
      "model": "gpt-4o-mini"
    },
    {
      "name": "官方 DeepSeek (deepseek-chat)",
      "type": "DeepSeek",
      "api_key": "请在此处填入您的DeepSeek API密钥 (sk-...)",
      "api_base": "https://api.deepseek.com/v1/chat/completions",
      "model": "deepseek-chat"
    },
    {
      "name": "官方 Gemini (gemini-1.5-flash)",
      "type": "Gemini",
      "api_key": "请在此处填入您的Google Gemini API密钥",
      "api_base": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
      "model": "gemini-2.5-flash"
    },
    {
      "name": "我的第三方代理",
      "type": "ChatGPT",
      "api_key": "sk-your-provider-key",
      "api_base": "https://your-proxy-provider.com/v1/chat/completions",
      "model": "gpt-4-turbo"
    },
    {
      "name": "本地模型服务 (Llama3)",
      "type": "ChatGPT",
      "api_key": "no-key-needed-for-local",
      "api_base": "http://127.0.0.1:8080/v1/chat/completions",
      "model": "llama3"
    }
  ]
}
```

**字段说明:**

- `name`: (必需) 您为这个配置起的名字，它会显示在节点的下拉菜单中。
    
- `type`: (必需) 服务的类型，必须是 `ChatGPT`, `DeepSeek`, `Gemini` 中的一个。这决定了插件如何构造请求。
    
- `api_key`: (必需) 您的API密钥。
    
- `api_base`: (必需) **完整的API接口地址**。请注意，必须是接口地址，而不仅仅是域名。
    
- `model`: (必需) 您想要使用的模型名称。
    

## 节點介紹 (Nodes Introduction)

您可以在 `AI提示词工具` 分类下找到本插件的节点。

### 🤖 AI提示词优化器 (AI Prompt Refiner)

一键将简单的想法变成专业级的AI绘画提示词。

- **输入 (Inputs):**
    
    - `prompt`: 您的基本想法或关键词，例如 "a cute cat"。
        
    - `image` (可选): 连接一张图片，AI会参考图片内容进行优化。
        
- **设置 (Settings):**
    
    - `config_selection`: 选择您在 `config.json` 中配置好的AI服务。
        
    - `target_model`: 选择提示词的目标风格 (`通用`, `SDXL`, `Flux`)。插件会根据您的选择，指导AI生成最适合该模型的提示词。
        
    - `style`: 为您的提示词选择一个艺术风格，例如“摄影”、“动漫”等。
        
    - `detail_level`: 控制提示词的细节丰富程度。
        
    - `negative_mode`: 选择一套预设的负面提示词模板，或选择“自定义”。
        
    - `custom_negative`: 当 `negative_mode` 为“自定义”时，此处内容生效。
        
- **输出 (Outputs):**
    
    - `优化后的提示词`: 生成的专业级英文提示词，可直接用于文生图。
        
    - `负面提示词`: 根据您选择的模板生成的负面提示词。
        
    - `优化笔记`: AI对本次优化的思路和中文说明。
        

### 🌐 AI翻译器 (AI Translator)

一个简单易用的翻译工具，支持多种免费和AI翻译引擎。

- **输入 (Inputs):**
    
    - `text_to_translate`: 需要翻译的文本。
        
- **设置 (Settings):**
    
    - `translation_direction`: 选择翻译方向（中->英 或 英->中）。
        
    - `service_selection`: 选择翻译服务。除了免费的谷歌翻译，还会自动列出您在 `config.json` 中配置的所有AI服务。
        
- **输出 (Outputs):**
    
    - `翻译后的文本`: 翻译结果。
        

## 💡 使用流程示例

1. 添加一个 `AI提示词优化器` 节点。
    
2. 在 `prompt` 中输入您的想法，例如 "一只在雨中打瞌睡的橘猫"。
    
3. 选择您在 `config.json` 中配置好的服务。
    
4. 选择目标模型为 `Flux`，艺术风格为 `摄影`。
    
5. 添加一个第三方的 `Show Text` 节点（或其他文本显示节点）。
    
6. 将 `优化后的提示词` 和 `优化笔记` 连接到 `Show Text` 节点的 `text` 输入口。
    
7. 点击 "Queue Prompt"，等待片刻，您就能在 `Show Text` 节点中看到优化好的提示词和分析笔记了！
    

## 依赖 (Dependencies)

本插件需要 `requests` 库，通常ComfyUI自带的环境中已包含。如果没有，您可以通过以下方式安装：

```
pip install requests
```

## 致谢 (Acknowledgements)

感谢所有为ComfyUI社区做出贡献的开发者们。
