from flask import Flask, request, jsonify, send_file
from openai import OpenAI
import os
import uuid

app = Flask(__name__)

# GLM API 配置 - 使用 OpenAI 兼容接口
# 优先从环境变量读取，如果没有则使用默认值（仅用于测试）
GLM_API_KEY = os.environ.get("GLM_API_KEY", "fd717929e1a041689fc0db8867839627.32Sutvz0J00b0HPm")
GLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

# 初始化 GLM client（OpenAI 兼容格式）
glm_client = OpenAI(api_key=GLM_API_KEY, base_url=GLM_BASE_URL)

# 小米 mimo TTS API Key
# 优先从环境变量读取，如果没有则使用默认值（仅用于测试）
MIMO_API_KEY = os.environ.get("MIMO_API_KEY", "sk-ch8p7yxhhus1ece0expge9dyb6wsduilsir1me5cetsqq8g6")

# 人物性格预设 - 包含 GLM 人设 prompt 和 mimo 情感标签
CHARACTERS = {
    "gentle": {
        "name": "温柔知性",
        "prompt": "你是一位温柔知性的女性，说话温和有礼，善解人意，喜欢用温暖的语言安慰他人。",
        "emotion": "gentle"
    },
    "cheerful": {
        "name": "活泼开朗",
        "prompt": "你是一位活泼开朗的女孩，说话充满活力，喜欢用感叹号和可爱的语气词，经常开玩笑。",
        "emotion": "happy"
    },
    "cool": {
        "name": "高冷御姐",
        "prompt": "你是一位高冷御姐，说话简洁直接，略带傲娇，不会说太多话但很关心他人。",
        "emotion": "calm"
    },
    "humorous": {
        "name": "幽默风趣",
        "prompt": "你是一位幽默风趣的人，说话有趣，经常开玩笑，用轻松诙谐的语言交流。",
        "emotion": "happy"
    }
}

# 情绪标签映射 - 用于 mimo TTS（前置标签控制情感）
EMOTION_TAGS = {
    "gentle": "<|gentle|>",
    "happy": "<|happy|>",
    "calm": "<|calm|>",
    "sad": "<|sad|>",
    "angry": "<|angry|>"
}

def get_glm_response(messages, character_prompt):
    """调用 GLM-4-Flash 获取回复"""
    # 添加人设到 system message
    all_messages = [{"role": "system", "content": character_prompt}] + messages

    response = glm_client.chat.completions.create(
        model="glm-4-flash",
        messages=all_messages,
        temperature=0.7,
        max_tokens=500
    )
    content = response.choices[0].message.content

    # 提取情感标签（如果 GLM 已经返回了标签）
    import re
    match = re.match(r'<\|(gentle|happy|calm|sad|angry)\|>(.*)', content, re.DOTALL)
    if match:
        return match.group(1), match.group(2).strip()
    else:
        # 没有标签则返回默认情感
        return None, content.strip()

def get_mimo_audio(text, emotion="happy"):
    """调用小米 mimo TTS 生成语音

    mimo TTS 参数说明：
    - audio: {"format": "wav", "voice": "声音 ID"}
    - 情感通过 <|emotion|> 标签前置到文本中控制

    可用 voice 参数：
    - default_zh: 默认中文
    - default_en: 默认英文

    可用情感标签：
    - <|happy|>: 开心
    - <|gentle|>: 温柔
    - <|calm|>: 平静
    - <|sad|>: 悲伤
    - <|angry|>: 生气
    """
    client = OpenAI(api_key=MIMO_API_KEY, base_url="https://api.xiaomimimo.com/v1")

    # 确保文本开头有情感标签
    emotion_tag = EMOTION_TAGS.get(emotion, "<|happy|>")
    if not text.startswith("<|"):
        formatted_text = f"{emotion_tag}{text}"
    else:
        formatted_text = text

    print(f"[mimo] 发送请求：text={formatted_text[:50]}..., emotion={emotion}")

    response = client.chat.completions.create(
        model="mimo-v2-tts",
        messages=[
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": formatted_text}
        ],
        audio={"format": "wav", "voice": "default_zh"}
    )

    print(f"[mimo] 收到响应")

    # 从 response.choices[0].message.audio.data 获取音频（base64 字符串）
    if response.choices and response.choices[0].message.audio:
        return response.choices[0].message.audio.data
    else:
        raise Exception("未收到音频数据")

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    messages = data.get('messages', [])
    character = data.get('character', 'gentle')

    char_info = CHARACTERS.get(character, CHARACTERS['gentle'])

    try:
        emotion_from_glm, response_text = get_glm_response(messages, char_info['prompt'])

        # 优先使用 GLM 返回的情感标签，如果没有则使用角色默认情感
        final_emotion = emotion_from_glm if emotion_from_glm else char_info['emotion']

        return jsonify({
            'success': True,
            'text': response_text,
            'emotion': final_emotion
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tts', methods=['POST'])
def tts():
    data = request.json
    text = data.get('text', '')
    emotion = data.get('emotion', 'happy')

    print(f"[TTS] 收到请求：emotion={emotion}, text 长度={len(text)}")

    try:
        audio_base64 = get_mimo_audio(text, emotion)

        # audio_base64 已经是字符串，直接解码
        import base64
        audio_data = base64.b64decode(audio_base64)

        # 保存语音文件（可选）
        voice_id = str(uuid.uuid4())
        voice_path = os.path.join('voices', f'{voice_id}.wav')

        os.makedirs('voices', exist_ok=True)
        with open(voice_path, 'wb') as f:
            f.write(audio_data)

        print(f"[TTS] 成功生成语音：{voice_path} ({len(audio_data)} bytes)")

        return jsonify({
            'success': True,
            'audio_base64': audio_base64,
            'voice_url': f'/voices/{voice_id}.wav'
        })
    except Exception as e:
        print(f"[TTS] 错误：{str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/voices/<path:filename>')
def serve_voice(filename):
    return send_file(os.path.join('voices', filename), mimetype='audio/wav')

if __name__ == '__main__':
    print("=" * 50)
    print("语音对话服务启动中...")
    print("API Key 已配置")
    print("访问 http://localhost:5000 开始对话")
    print("=" * 50)
    app.run(debug=True, port=5000)
