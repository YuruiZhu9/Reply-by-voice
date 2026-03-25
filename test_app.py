import unittest
from unittest.mock import patch

import app


class MimoConfigTests(unittest.TestCase):
    def test_character_catalog_contains_random_name_pool(self):
        catalog = app.serialize_character_catalog()
        self.assertIn("gentle", catalog)
        self.assertIn("taiwan_sweet", catalog)
        self.assertGreaterEqual(len(catalog["gentle"]["candidate_names"]), 4)
        self.assertGreaterEqual(len(catalog["taiwan_sweet"]["candidate_names"]), 4)

    def test_character_catalog_exposes_media_fields(self):
        catalog = app.serialize_character_catalog()
        gentle = catalog["gentle"]
        self.assertIn("portrait_prompt", gentle)
        self.assertIn("portrait_url", gentle)
        self.assertIn("video_prompt", gentle)
        self.assertIn("video_url", gentle)

    def test_build_fallback_reply_for_rate_limit(self):
        text = app.build_fallback_reply("gentle", Exception("429 rate limit"))
        self.assertIn("再和我说一句", text)

    def test_build_mimo_tts_text_uses_style_tag_for_emotion(self):
        result = app.build_mimo_tts_text("你好，今天过得怎么样？", emotion="gentle")
        self.assertTrue(result.startswith("<style>gentle soft warm</style>"))
        self.assertIn("你好，今天过得怎么样？", result)

    def test_build_mimo_tts_text_strips_legacy_emotion_tag(self):
        result = app.build_mimo_tts_text("<|happy|>你好", emotion="happy")
        self.assertNotIn("<|happy|>", result)
        self.assertTrue(result.startswith("<style>happy lively energetic</style>"))

    def test_get_glm_response_disables_thinking_in_openai_compatible_call(self):
        class DummyMessage:
            def __init__(self):
                self.content = "你好，我在。"
                self.reasoning_content = None

        class DummyChoice:
            def __init__(self):
                self.message = DummyMessage()

        class DummyResponse:
            def __init__(self):
                self.choices = [DummyChoice()]

        with patch.object(app.glm_client.chat.completions, "create", return_value=DummyResponse()) as mocked_create:
            emotion, content = app.get_glm_response(
                [{"role": "user", "content": "你好"}],
                "你是一个有帮助的助手。"
            )

        self.assertIsNone(emotion)
        self.assertEqual(content, "你好，我在。")
        self.assertEqual(
            mocked_create.call_args.kwargs["extra_body"],
            {"thinking": {"type": "disabled"}}
        )

    def test_validate_mimo_voice_accepts_supported_voice(self):
        self.assertEqual(app.validate_mimo_voice("default_zh"), "default_zh")

    def test_validate_mimo_voice_rejects_unknown_voice(self):
        with self.assertRaises(ValueError):
            app.validate_mimo_voice("male")

    def test_generate_character_image_uses_cogview_flash_model(self):
        with patch.object(app.glm_client.images, "generate", return_value={"data": [{"url": "https://example.com/gentle.png"}]}) as mocked_generate:
            result = app.generate_character_image("gentle")

        self.assertEqual(result["url"], "https://example.com/gentle.png")
        self.assertEqual(result["character"], "gentle")
        self.assertEqual(mocked_generate.call_args.kwargs["model"], "cogview-3-flash")

    def test_submit_character_video_task_uses_cogvideox_flash_model(self):
        async_response = {
            "id": "video-task-123",
            "model": "cogvideox-flash",
            "task_status": "PROCESSING"
        }

        with patch.object(app.glm_client, "post", return_value=async_response) as mocked_post:
            result = app.submit_character_video_task("gentle")

        self.assertEqual(result["task_id"], "video-task-123")
        self.assertEqual(result["task_status"], "PROCESSING")
        self.assertEqual(result["character"], "gentle")
        self.assertEqual(mocked_post.call_args.args[0], "/videos/generations")
        self.assertEqual(mocked_post.call_args.kwargs["body"]["model"], "cogvideox-flash")

    def test_get_character_video_task_status_returns_media_url_on_success(self):
        result_response = {
            "model": "cogvideox-flash",
            "task_status": "SUCCESS",
            "video_result": [{"url": "https://example.com/gentle.mp4"}],
            "request_id": "req-1"
        }

        with patch.object(app.glm_client, "get", return_value=result_response) as mocked_get:
            result = app.get_character_video_task_status("video-task-123")

        self.assertEqual(result["task_id"], "video-task-123")
        self.assertEqual(result["task_status"], "SUCCESS")
        self.assertEqual(result["media_url"], "https://example.com/gentle.mp4")
        self.assertEqual(mocked_get.call_args.args[0], "/async-result/video-task-123")


class CharacterMediaRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()

    def test_character_image_route_returns_generated_media(self):
        with patch.object(app, "generate_character_image", return_value={
            "character": "gentle",
            "url": "https://example.com/generated.png",
            "prompt": "soft anime portrait"
        }):
            response = self.client.post("/api/character-media/image", json={"character": "gentle"})

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["media_type"], "image")
        self.assertEqual(payload["media_url"], "https://example.com/generated.png")

    def test_character_video_route_submits_task_metadata(self):
        with patch.object(app, "submit_character_video_task", return_value={
            "task_id": "video-task-123",
            "task_status": "PROCESSING",
            "character": "gentle",
            "prompt": "anime motion portrait"
        }):
            response = self.client.post("/api/character-media/video", json={"character": "gentle"})

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["media_type"], "video")
        self.assertEqual(payload["task_id"], "video-task-123")
        self.assertEqual(payload["task_status"], "PROCESSING")
        self.assertNotIn("media_url", payload)

    def test_character_video_status_route_returns_processing_state(self):
        with patch.object(app, "get_character_video_task_status", return_value={
            "task_id": "video-task-123",
            "task_status": "PROCESSING"
        }):
            response = self.client.get("/api/character-media/video/video-task-123")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["task_status"], "PROCESSING")
        self.assertNotIn("media_url", payload)

    def test_character_video_status_route_returns_final_media_url(self):
        with patch.object(app, "get_character_video_task_status", return_value={
            "task_id": "video-task-123",
            "task_status": "SUCCESS",
            "media_url": "https://example.com/generated.mp4"
        }):
            response = self.client.get("/api/character-media/video/video-task-123")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["task_status"], "SUCCESS")
        self.assertEqual(payload["media_url"], "https://example.com/generated.mp4")

    def test_character_video_status_route_returns_provider_failure(self):
        with patch.object(app, "get_character_video_task_status", side_effect=RuntimeError("CogVideoX video generation failed.")):
            response = self.client.get("/api/character-media/video/video-task-123")

        self.assertEqual(response.status_code, 502)
        payload = response.get_json()
        self.assertFalse(payload["success"])
        self.assertEqual(payload["media_type"], "video")

    def test_character_video_route_rejects_unknown_character(self):
        response = self.client.post("/api/character-media/video", json={"character": "missing"})
        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertFalse(payload["success"])


if __name__ == "__main__":
    unittest.main()
