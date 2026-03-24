# Reply-by-voice

一个基于 Flask 的二次元语音聊天页面。当前版本聚焦在三件事：

- 4 个角色人格，每个角色带一组随机二次元姓名
- GLM 生成文本，MiMo TTS 生成语音
- 更偏角色卡片式的 UI，而不是普通聊天框

## 当前功能

- 角色人格：
  - `gentle` 月光治愈系
  - `cheerful` 元气甜心系
  - `cool` 冷冽前辈系
  - `humorous` 怪话吐槽系
  - `taiwan_sweet` 台湾甜妹系
- 每次切换角色都会从候选池里随机抽一个姓名，并在当前轮对话中保持不变
- 首页欢迎语使用“我是某个角色名”的形式，不再直接展示风格型见面语
- MiMo TTS 按官方文档使用 `<style>...</style>` 控制风格
- 当 GLM 上游限流或返回空文本时，后端会返回一条符合当前角色语气的 fallback 文案，避免整条语音链路直接断掉
- 台湾甜妹人设的 prompt 明确要求“用台湾腔说话，地道的台湾口音”

## 技术栈

- Backend: Flask
- Text model: GLM-4.7-Flash
- TTS: Xiaomi MiMo TTS
- Frontend: 原生 HTML / CSS / JavaScript

## 目录结构

```text
Reply-by-voice/
├── app.py
├── index.html
├── run_server.py
├── test_app.py
├── .env.example
├── .gitignore
└── voices/
```

## 环境变量

复制 `.env.example` 为 `.env`：

```powershell
Copy-Item .env.example .env
```

填写以下配置：

```env
GLM_API_KEY=your_glm_api_key
MIMO_API_KEY=your_mimo_api_key
MIMO_TTS_VOICE=default_zh
```

`MIMO_TTS_VOICE` 目前只支持：

- `mimo_default`
- `default_zh`
- `default_en`

## 启动方式

推荐使用稳定启动脚本：

```powershell
python run_server.py
```

启动后访问：

```text
http://127.0.0.1:5000
```

说明：

- `run_server.py` 会关闭 Flask reloader，适合本地常驻运行
- 如果用 `python app.py`，会进入 debug 模式，行为更偏开发态

## API

### `GET /api/characters`

返回当前前端所需的角色目录，包括：

- 角色标题
- 角色摘要
- tagline
- 主题色
- 候选姓名池
- 默认 TTS 风格

### `POST /api/chat`

请求体示例：

```json
{
  "messages": [
    { "role": "user", "content": "你好" }
  ],
  "character": "gentle"
}
```

响应体示例：

```json
{
  "success": true,
  "text": "这里稍微有点忙，我还在努力跟上你的节奏。再和我说一句，我会继续陪着你。",
  "emotion": "gentle",
  "tts_style": "gentle soft warm",
  "voice": "default_zh",
  "character_title": "月光治愈系",
  "fallback": true
}
```

说明：

- 正常情况下返回 GLM 文本
- 如果 GLM 限流或上游异常，返回角色化 fallback 文案，并把 `fallback` 置为 `true`

### `POST /api/tts`

请求体示例：

```json
{
  "text": "你好，很高兴见到你。",
  "emotion": "gentle",
  "character": "gentle",
  "voice": "default_zh",
  "style": "gentle soft warm"
}
```

响应体示例：

```json
{
  "success": true,
  "audio_base64": "...",
  "voice_url": "/voices/xxx.wav",
  "voice": "default_zh",
  "style": "gentle soft warm"
}
```

## MiMo TTS 说明

当前实现遵循官方文档：

- voice 只使用 `mimo_default`、`default_zh`、`default_en`
- 没有单独的 `gender` 参数
- 风格和情绪通过合成文本前缀的 `<style>...</style>` 控制
- 旧版 `<|happy|>` 一类标签只做兼容清理，不再作为正式调用格式

## 前端 UI

当前界面不是简单聊天框，而是角色导向布局：

- 顶部 hero 区 + 当前搭子角色卡
- 中间角色切换 rail
- 下方聊天面板
- 底部输入区和语音播放器
- 角色 rail 已适配 5 张卡的自适应布局

设计方向：

- 轻玻璃态
- 柔和渐变背景
- 角色主题色驱动局部视觉
- 更偏二次元陪伴感，而不是工具面板感

## 测试

运行：

```powershell
python -m unittest -q
```

当前测试覆盖：

- 角色目录包含随机姓名池
- MiMo TTS 风格文本拼装
- 旧情绪标签清理
- voice 校验
- fallback 回复构造

## 已知说明

- 当前语音是“生成后提供播放按钮”，不是自动播放
- 如果 GLM 被限流，页面仍然会有文本和语音，但文本内容会是 fallback 文案
- `voices/` 下的 wav 文件是运行时产物，已在 Git 中忽略

## 参考

- MiMo Speech Synthesis:
  `https://platform.xiaomimimo.com/docs/usage-guide/speech-synthesis.md`
- MiMo V2 TTS Release Note:
  `https://platform.xiaomimimo.com/docs/news/v2-tts-release.md`
