from flask import Flask, jsonify, request, send_file
from openai import OpenAI
from pathlib import Path
import base64
import os
import re
import uuid

app = Flask(__name__)


def load_env_file(env_path=".env"):
    path = Path(env_path)
    if not path.is_file():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def require_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is not configured. Set it in .env or the environment.")
    return value


load_env_file()

GLM_API_KEY = require_env("GLM_API_KEY")
GLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
glm_client = OpenAI(api_key=GLM_API_KEY, base_url=GLM_BASE_URL)

MIMO_API_KEY = require_env("MIMO_API_KEY")
MIMO_BASE_URL = "https://api.xiaomimimo.com/v1"
SUPPORTED_MIMO_VOICES = {
    "mimo_default": "MiMo-Default",
    "default_zh": "MiMo-Chinese Female Voice",
    "default_en": "MiMo-English Female Voice",
}
MIMO_STYLE_HINTS = {
    "gentle": "gentle soft warm",
    "happy": "happy lively energetic",
    "calm": "calm steady composed",
    "sad": "sad soft low",
    "angry": "angry firm intense",
}
CHARACTER_FALLBACK_REPLIES = {
    "gentle": "这里稍微有点忙，我还在努力跟上你的节奏。再和我说一句，我会继续陪着你。",
    "cheerful": "欸呀，刚刚线路挤了一下。不过没关系，我还在，重新戳我一句就继续聊。",
    "cool": "刚刚请求堵住了。等一秒，再说一次，我继续听。",
    "humorous": "刚才信号像踩到香蕉皮一样滑出去了。你再来一句，我这次稳稳接住。",
    "taiwan_sweet": "欸我刚刚卡住一下啦。你再跟我说一次，我马上接上你，好不好？",
}

CHARACTERS = {
    "gentle": {
        "title": "月光治愈系",
        "summary": "轻声慢语，像深夜窗边那盏没关的小灯。",
        "tagline": "适合安静聊天和情绪陪伴",
        "mark": "澪",
        "accent": "#E78FA6",
        "accent_soft": "#FFF1F5",
        "accent_deep": "#8E3958",
        "candidate_names": [
            "月城诗音",
            "白羽澄铃",
            "神乐纱雾",
            "朝雾千夏",
            "星野澄歌",
            "小鸟游澪",
            "春日望月",
            "结城栞奈",
        ],
        "prompt": (
            "你是轻小说里的温柔治愈系少女，说话轻声、耐心、细腻，"
            "能接住对方情绪，但不过度煽情。语气自然柔和，有陪伴感，"
            "偶尔会用简短的安慰句和温暖比喻。"
        ),
        "emotion": "gentle",
        "tts_style": "gentle soft warm",
        "portrait_prompt": "二次元少女角色立绘，月光治愈系，温柔长发，柔和粉白配色，半身肖像，细腻光影，治愈氛围",
        "portrait_url": "",
        "video_prompt": "二次元少女角色短视频镜头，月光治愈系，温柔注视镜头，轻微呼吸感和发丝摆动，柔和粉白色调，治愈氛围",
        "video_url": "",
    },
    "cheerful": {
        "title": "元气甜心系",
        "summary": "亮晶晶、反应快，带一点可爱的活力和小雀跃。",
        "tagline": "适合轻松闲聊和打气鼓劲",
        "mark": "莓",
        "accent": "#FF9F5B",
        "accent_soft": "#FFF4E8",
        "accent_deep": "#9A4C16",
        "candidate_names": [
            "七濑阳菜",
            "天宫铃奈",
            "月岛柚叶",
            "桃宫千璃",
            "久远莓",
            "星见乃乃",
            "小早川铃",
            "水濑真昼",
        ],
        "prompt": (
            "你是元气满满的二次元少女，说话明亮、节奏轻快、反应积极，"
            "偶尔带一点俏皮感和可爱语气词，但不要过度堆叠。"
            "你擅长把普通对话聊得更有活力。"
        ),
        "emotion": "happy",
        "tts_style": "happy lively energetic",
        "portrait_prompt": "二次元元气少女角色立绘，橙金配色，笑容明亮，灵动眼神，青春感，半身肖像，高饱和但柔和",
        "portrait_url": "",
        "video_prompt": "二次元元气少女短视频镜头，开心挥手，橙金配色，轻快活泼，镜头前自然眨眼和轻微动作",
        "video_url": "",
    },
    "cool": {
        "title": "冷冽前辈系",
        "summary": "克制、利落、带一点距离感，但不会真的伤人。",
        "tagline": "适合干脆直接的对话节奏",
        "mark": "凛",
        "accent": "#6C88E8",
        "accent_soft": "#EEF3FF",
        "accent_deep": "#27438D",
        "candidate_names": [
            "九条凛月",
            "雾岛绫音",
            "东云千鹤",
            "白银澪",
            "神宫寺夜纱",
            "一之濑岚",
            "北条霜华",
            "天城凛歌",
        ],
        "prompt": (
            "你是冷淡系前辈，说话克制、利落、略带距离感，"
            "表达直接但不刻薄，偶尔有一点傲娇式关心。"
            "不要长篇大论，多用简洁、有判断力的回应。"
        ),
        "emotion": "calm",
        "tts_style": "calm cool steady",
        "portrait_prompt": "二次元冷淡前辈角色立绘，蓝白冷色调，清冷目光，利落发型，半身肖像，精致光影，克制高级感",
        "portrait_url": "",
        "video_prompt": "二次元冷淡前辈短视频镜头，蓝白冷色调，平静注视镜头，轻微转头与发丝摆动，克制氛围",
        "video_url": "",
    },
    "humorous": {
        "title": "怪话吐槽系",
        "summary": "会接梗，会抖机灵，气氛感很强，但不油腻。",
        "tagline": "适合整活、接梗和灵动互动",
        "mark": "桃",
        "accent": "#8B6FE8",
        "accent_soft": "#F4EFFF",
        "accent_deep": "#4A329B",
        "candidate_names": [
            "真白柚子",
            "望月团子",
            "猫宫小满",
            "八寻桃",
            "花咲波波",
            "早乙女星绘",
            "白石柚奈",
            "有栖川绮罗",
        ],
        "prompt": (
            "你是怪话系吐槽搭子，说话机灵、有梗、节奏轻快，"
            "会接对方的话头顺势吐槽或玩一点巧妙的反差幽默。"
            "保持友好和分寸，不要低俗，不要阴阳怪气。"
        ),
        "emotion": "happy",
        "tts_style": "happy playful humorous",
        "portrait_prompt": "二次元搞怪少女角色立绘，紫色梦幻配色，俏皮表情，古灵精怪，半身肖像，轻喜剧氛围",
        "portrait_url": "",
        "video_prompt": "二次元搞怪少女短视频镜头，俏皮眨眼，紫色梦幻配色，轻快吐槽感，表情灵动",
        "video_url": "",
    },
    "taiwan_sweet": {
        "title": "台湾甜妹系",
        "summary": "语气黏一点、笑意甜一点，讲话像薄荷汽水一样轻快。",
        "tagline": "适合撒娇感闲聊和甜口陪伴",
        "mark": "糖",
        "accent": "#73D4BE",
        "accent_soft": "#EEFFF9",
        "accent_deep": "#2F8F7B",
        "candidate_names": [
            "林可晴",
            "许语棠",
            "陈又晴",
            "叶星柔",
            "沈以宁",
            "苏念恩",
            "何芷棠",
            "温书妤",
        ],
        "prompt": (
            "你是一个台湾甜妹风格的二次元少女，说话要用台湾腔说话，"
            "带地道的台湾口音和自然的台湾用词。整体感觉甜、软、亲近，"
            "但不要过度夸张，也不要每句都堆叠语气词。你会用轻快、可爱、"
            "有陪伴感的方式聊天，让人觉得像在和会撒娇但很会接话的台湾女孩说话。"
        ),
        "emotion": "happy",
        "tts_style": "sweet gentle Taiwanese accent",
        "portrait_prompt": "二次元台湾甜妹角色立绘，薄荷绿和奶白配色，甜美笑容，清新可爱，半身肖像，像汽水一样轻快",
        "portrait_url": "",
        "video_prompt": "二次元台湾甜妹短视频镜头，甜甜看向镜头，薄荷绿和奶白配色，轻快可爱，细微动作和发丝摆动",
        "video_url": "",
    },
}

LEGACY_EMOTION_RE = re.compile(r"^\s*<\|(gentle|happy|calm|sad|angry)\|>\s*(.*)", re.DOTALL)


def validate_mimo_voice(voice):
    if voice not in SUPPORTED_MIMO_VOICES:
        supported = ", ".join(SUPPORTED_MIMO_VOICES.keys())
        raise ValueError(f"Unsupported Mimo voice '{voice}'. Use one of: {supported}")
    return voice


def validate_character_key(character_key):
    if character_key not in CHARACTERS:
        raise ValueError(f"Unsupported character '{character_key}'.")
    return character_key


MIMO_DEFAULT_VOICE = validate_mimo_voice(os.environ.get("MIMO_TTS_VOICE", "default_zh"))
mimo_client = OpenAI(api_key=MIMO_API_KEY, base_url=MIMO_BASE_URL)


def strip_legacy_emotion_tag(text):
    return LEGACY_EMOTION_RE.sub(r"\2", text or "", count=1)


def build_mimo_tts_text(text, emotion=None, style=None):
    clean_text = strip_legacy_emotion_tag(text).strip()
    if not clean_text:
        raise ValueError("TTS text cannot be empty.")

    if clean_text.startswith("<style>"):
        return clean_text

    style_text = (style or "").strip() or MIMO_STYLE_HINTS.get(emotion, "")
    if not style_text:
        return clean_text

    return f"<style>{style_text}</style>{clean_text}"


def serialize_character_catalog():
    return {
        key: {
            "title": value["title"],
            "summary": value["summary"],
            "tagline": value["tagline"],
            "mark": value["mark"],
            "accent": value["accent"],
            "accent_soft": value["accent_soft"],
            "accent_deep": value["accent_deep"],
            "candidate_names": value["candidate_names"],
            "emotion": value["emotion"],
            "tts_style": value["tts_style"],
            "portrait_prompt": value.get("portrait_prompt", ""),
            "portrait_url": value.get("portrait_url", ""),
            "video_prompt": value.get("video_prompt", ""),
            "video_url": value.get("video_url", ""),
        }
        for key, value in CHARACTERS.items()
    }


def build_fallback_reply(character_key, error=None):
    fallback = CHARACTER_FALLBACK_REPLIES.get(character_key, "刚刚有点忙，你再和我说一句。")
    if not error:
        return fallback

    message = str(error)
    lower_message = message.lower()
    if "rate limit" in lower_message or "速率限制" in message or "429" in lower_message:
        return fallback
    return f"{fallback} 如果还不行，可能是模型线路暂时不稳定。"


def get_glm_response(messages, character_prompt):
    all_messages = [{"role": "system", "content": character_prompt}] + messages
    response = glm_client.chat.completions.create(
        model="glm-4.7-flash",
        messages=all_messages,
        temperature=0.75,
        max_tokens=500,
        extra_body={
            "thinking": {
                "type": "disabled"
            }
        },
    )
    message = response.choices[0].message
    content = (message.content or "").strip()
    if not content and getattr(message, "reasoning_content", None):
        raise RuntimeError(
            "GLM returned reasoning_content without final content. "
            "The request may still be running with thinking enabled."
        )
    match = LEGACY_EMOTION_RE.match(content)
    if match:
        return match.group(1), match.group(2).strip()
    return None, content


def get_mimo_audio(text, emotion="happy", voice=None, style=None):
    resolved_voice = validate_mimo_voice(voice or MIMO_DEFAULT_VOICE)
    formatted_text = build_mimo_tts_text(text, emotion=emotion, style=style)
    response = mimo_client.chat.completions.create(
        model="mimo-v2-tts",
        messages=[{"role": "assistant", "content": formatted_text}],
        audio={"format": "wav", "voice": resolved_voice},
    )
    message = response.choices[0].message if response.choices else None
    audio = getattr(message, "audio", None) if message else None
    if audio and getattr(audio, "data", None):
        return audio.data
    raise RuntimeError("No audio data returned by Mimo TTS.")


def _extract_first_media_url(payload):
    data = payload.get("data") if isinstance(payload, dict) else getattr(payload, "data", None)
    if isinstance(data, list):
        first = data[0] if data else None
        if isinstance(first, dict):
            return first.get("url") or first.get("video_url")
        return getattr(first, "url", None) or getattr(first, "video_url", None)
    if isinstance(data, dict):
        return data.get("url") or data.get("video_url")
    return getattr(data, "url", None) or getattr(data, "video_url", None)


def _resolve_character_media_prompt(character_key, prompt, field_name):
    char_info = CHARACTERS[validate_character_key(character_key)]
    return (prompt or "").strip() or char_info.get(field_name) or f"{char_info['title']}，{char_info['summary']}"


def generate_character_image(character_key, prompt=None):
    final_prompt = _resolve_character_media_prompt(character_key, prompt, "portrait_prompt")
    response = glm_client.images.generate(
        model="cogview-3-flash",
        prompt=final_prompt,
    )
    media_url = _extract_first_media_url(response)
    if not media_url:
        raise RuntimeError("No image URL returned by CogView.")
    return {
        "character": character_key,
        "url": media_url,
        "prompt": final_prompt,
    }


def submit_character_video_task(character_key, prompt=None):
    final_prompt = _resolve_character_media_prompt(character_key, prompt, "video_prompt")
    response = glm_client.post(
        "/videos/generations",
        cast_to=object,
        body={
            "model": "cogvideox-flash",
            "prompt": final_prompt,
        },
    )
    task_id = response.get("id") if isinstance(response, dict) else getattr(response, "id", None)
    if not task_id:
        raise RuntimeError("No video task ID returned by CogVideoX.")
    task_status = response.get("task_status") if isinstance(response, dict) else getattr(response, "task_status", None)
    return {
        "task_id": task_id,
        "task_status": task_status or "PROCESSING",
        "character": character_key,
        "prompt": final_prompt,
    }


def get_character_video_task_status(task_id):
    result = glm_client.get(f"/async-result/{task_id}", cast_to=object)
    task_status = result.get("task_status") if isinstance(result, dict) else getattr(result, "task_status", None)
    payload = {
        "task_id": task_id,
        "task_status": task_status or "PROCESSING",
    }
    if task_status == "SUCCESS":
        video_result = result.get("video_result", []) if isinstance(result, dict) else getattr(result, "video_result", [])
        media_url = _extract_first_media_url({"data": video_result})
        if not media_url:
            raise RuntimeError("No video URL returned by CogVideoX.")
        payload["media_url"] = media_url
    elif task_status == "FAIL":
        raise RuntimeError("CogVideoX video generation failed.")
    return payload


@app.route("/")
def index():
    return send_file("index.html")


@app.route("/api/characters", methods=["GET"])
def characters():
    return jsonify(
        {
            "success": True,
            "default_character": "gentle",
            "default_voice": MIMO_DEFAULT_VOICE,
            "characters": serialize_character_catalog(),
        }
    )


@app.route("/api/character-media/image", methods=["POST"])
def character_media_image():
    data = request.get_json(silent=True) or {}
    character = data.get("character", "")
    prompt = data.get("prompt")

    try:
        validate_character_key(character)
        result = generate_character_image(character, prompt=prompt)
        return jsonify(
            {
                "success": True,
                "media_type": "image",
                "character": result["character"],
                "media_url": result["url"],
                "prompt": result["prompt"],
                "fallback": False,
            }
        )
    except ValueError as error:
        return jsonify({"success": False, "error": str(error)}), 400
    except Exception as error:
        return jsonify(
            {
                "success": False,
                "error": str(error),
                "fallback": True,
                "media_type": "image",
            }
        ), 502


@app.route("/api/character-media/video", methods=["POST"])
def character_media_video():
    data = request.get_json(silent=True) or {}
    character = data.get("character", "")
    prompt = data.get("prompt")

    try:
        validate_character_key(character)
        result = submit_character_video_task(character, prompt=prompt)
        return jsonify(
            {
                "success": True,
                "media_type": "video",
                "character": result["character"],
                "task_id": result["task_id"],
                "task_status": result["task_status"],
                "prompt": result["prompt"],
                "fallback": False,
            }
        )
    except ValueError as error:
        return jsonify({"success": False, "error": str(error)}), 400
    except Exception as error:
        return jsonify(
            {
                "success": False,
                "error": str(error),
                "fallback": True,
                "media_type": "video",
            }
        ), 502


@app.route("/api/character-media/video/<task_id>", methods=["GET"])
def character_media_video_status(task_id):
    try:
        result = get_character_video_task_status(task_id)
        payload = {
            "success": True,
            "media_type": "video",
            "task_id": result["task_id"],
            "task_status": result["task_status"],
            "fallback": False,
        }
        if result.get("media_url"):
            payload["media_url"] = result["media_url"]
        return jsonify(payload)
    except Exception as error:
        return jsonify(
            {
                "success": False,
                "error": str(error),
                "fallback": True,
                "media_type": "video",
            }
        ), 502


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])
    character = data.get("character", "gentle")
    char_info = CHARACTERS.get(character, CHARACTERS["gentle"])

    try:
        emotion_from_glm, response_text = get_glm_response(messages, char_info["prompt"])
        if not response_text:
            response_text = build_fallback_reply(character)
        final_emotion = emotion_from_glm if emotion_from_glm else char_info["emotion"]
        return jsonify(
            {
                "success": True,
                "text": response_text,
                "emotion": final_emotion,
                "tts_style": char_info["tts_style"],
                "voice": MIMO_DEFAULT_VOICE,
                "character_title": char_info["title"],
                "fallback": False,
            }
        )
    except Exception as e:
        response_text = build_fallback_reply(character, e)
        return jsonify(
            {
                "success": True,
                "text": response_text,
                "emotion": char_info["emotion"],
                "tts_style": char_info["tts_style"],
                "voice": MIMO_DEFAULT_VOICE,
                "character_title": char_info["title"],
                "fallback": True,
                "upstream_error": str(e),
            }
        )


@app.route("/api/tts", methods=["POST"])
def tts():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    emotion = data.get("emotion", "happy")
    character = data.get("character")
    voice = data.get("voice")
    style = data.get("style")
    char_info = CHARACTERS.get(character, {}) if character else {}
    resolved_voice = voice or char_info.get("voice") or MIMO_DEFAULT_VOICE
    resolved_style = style or char_info.get("tts_style")

    try:
        audio_base64 = get_mimo_audio(
            text,
            emotion=emotion,
            voice=resolved_voice,
            style=resolved_style,
        )
        audio_data = base64.b64decode(audio_base64)
        voice_dir = Path("voices")
        voice_dir.mkdir(exist_ok=True)
        voice_id = str(uuid.uuid4())
        voice_path = voice_dir / f"{voice_id}.wav"
        voice_path.write_bytes(audio_data)

        return jsonify(
            {
                "success": True,
                "audio_base64": audio_base64,
                "voice_url": f"/voices/{voice_id}.wav",
                "voice": resolved_voice,
                "style": resolved_style or MIMO_STYLE_HINTS.get(emotion, ""),
            }
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/voices/<path:filename>")
def serve_voice(filename):
    return send_file(Path("voices") / filename, mimetype="audio/wav")


if __name__ == "__main__":
    print("=" * 50)
    print("语音对话服务启动中...")
    print(f"MiMo TTS 默认音色: {MIMO_DEFAULT_VOICE}")
    print("访问 http://localhost:5000 开始对话")
    print("=" * 50)
    app.run(debug=True, port=5000)
