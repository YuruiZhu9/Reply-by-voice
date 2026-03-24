# AI 语音对话机器人

一个基于 Web 的 AI 语音对话应用，支持多种性格角色和情感语音合成。

## 功能特点

- 🎭 **4 种性格角色**：温柔知性、活泼开朗、高冷御姐、幽默风趣
- 💬 **自然语言对话**：基于 GLM-4-Flash 大模型
- 🔊 **情感语音合成**：小米 mimo TTS，支持 5 种情感（开心、温柔、平静、悲伤、生气）
- 🎨 **精美 UI 界面**：响应式设计，支持波形动画播放
- 💾 **语音下载**：支持保存生成的语音文件

## 项目结构

```
vioce_test/
├── app.py              # Flask 后端服务
├── index.html          # 前端对话界面
├── .gitignore          # Git 忽略文件
├── README.md           # 项目说明
└── voices/             # 语音文件存储目录（运行时自动创建）
```

## 快速开始

### 1. 安装依赖

```bash
pip install flask openai
```

### 2. 配置 API Key

编辑 `app.py`，填写你的 API Key：

```python
# 智谱 AI API Key（GLM-4-Flash）
GLM_API_KEY = "your_glm_api_key"

# 小米 mimo API Key（TTS 语音合成）
MIMO_API_KEY = "your_mimo_api_key"
```

### 3. 启动服务

```bash
python app.py
```

### 4. 访问应用

浏览器打开：**http://localhost:5000**

## API 说明

### /api/chat (POST)

获取 AI 回复

**请求体：**
```json
{
  "messages": [{"role": "user", "content": "你好"}],
  "character": "gentle"
}
```

**响应：**
```json
{
  "success": true,
  "text": "你好！我是你的 AI 伙伴",
  "emotion": "gentle"
}
```

### /api/tts (POST)

生成语音

**请求体：**
```json
{
  "text": "你好",
  "emotion": "gentle"
}
```

**响应：**
```json
{
  "success": true,
  "voice_url": "/voices/xxx.wav",
  "audio_base64": "..."
}
```

## 角色配置

| 角色 | character | 情感标签 | 说明 |
|------|-----------|----------|------|
| 温柔知性 | gentle | `<|gentle|>` | 温和有礼，善解人意 |
| 活泼开朗 | cheerful | `<|happy|>` | 充满活力，可爱 |
| 高冷御姐 | cool | `<|calm|>` | 简洁直接，傲娇 |
| 幽默风趣 | humorous | `<|happy|>` | 有趣，诙谐 |

## 情感标签

mimo TTS 支持以下情感标签：

- `<|happy|>` - 开心
- `<|gentle|>` - 温柔
- `<|calm|>` - 平静
- `<|sad|>` - 悲伤
- `<|angry|>` - 生气

## API Key 获取

### 智谱 AI (GLM-4-Flash)

1. 访问：https://open.bigmodel.cn/
2. 注册并登录
3. 在控制台获取 API Key

### 小米 mimo TTS

1. 访问：https://platform.xiaomimimo.com/
2. 注册并登录
3. 获取 API Key

## 技术栈

- **后端**：Flask
- **对话模型**：智谱 AI GLM-4-Flash
- **语音合成**：小米 mimo TTS
- **前端**：原生 HTML/CSS/JavaScript

## License

MIT
