import unittest

import app


class MimoConfigTests(unittest.TestCase):
    def test_character_catalog_contains_random_name_pool(self):
        catalog = app.serialize_character_catalog()
        self.assertIn("gentle", catalog)
        self.assertGreaterEqual(len(catalog["gentle"]["candidate_names"]), 4)

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

    def test_validate_mimo_voice_accepts_supported_voice(self):
        self.assertEqual(app.validate_mimo_voice("default_zh"), "default_zh")

    def test_validate_mimo_voice_rejects_unknown_voice(self):
        with self.assertRaises(ValueError):
            app.validate_mimo_voice("male")


if __name__ == "__main__":
    unittest.main()
