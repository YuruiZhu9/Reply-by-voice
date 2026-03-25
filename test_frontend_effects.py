import unittest
from pathlib import Path


class FrontendEffectsTests(unittest.TestCase):
    def test_persona_card_contains_visual_stage_markup(self):
        html = Path("D:/个人信息文件/项目开发/Reply-by-voice/index.html").read_text(encoding="utf-8")
        self.assertIn('id="personaCard"', html)
        self.assertIn('class="persona-visual"', html)
        self.assertIn('id="personaPortrait"', html)
        self.assertIn('class="persona-ripple persona-ripple-1"', html)

    def test_persona_card_includes_requested_effect_styles(self):
        html = Path("D:/个人信息文件/项目开发/Reply-by-voice/index.html").read_text(encoding="utf-8")
        self.assertIn('@keyframes personaBreath', html)
        self.assertIn('@keyframes personaGlowPulse', html)
        self.assertIn('@keyframes personaRipple', html)
        self.assertIn('data-speaking="true"', html)

    def test_persona_card_script_controls_speaking_and_parallax(self):
        html = Path("D:/个人信息文件/项目开发/Reply-by-voice/index.html").read_text(encoding="utf-8")
        self.assertIn('function setPersonaSpeaking(isSpeaking)', html)
        self.assertIn('function bindPersonaParallax()', html)
        self.assertIn('personaCard.dataset.speaking = isSpeaking ? "true" : "false";', html)
        self.assertIn('bindPersonaParallax();', html)

    def test_persona_card_contains_media_slots(self):
        html = Path("D:/个人信息文件/项目开发/Reply-by-voice/index.html").read_text(encoding="utf-8")
        self.assertIn('id="personaVideo"', html)
        self.assertIn('id="personaImage"', html)
        self.assertIn('id="generateVideoBtn"', html)

    def test_persona_card_script_contains_media_generation_hooks(self):
        html = Path("D:/个人信息文件/项目开发/Reply-by-voice/index.html").read_text(encoding="utf-8")
        self.assertIn('let currentMediaRequestToken = 0;', html)
        self.assertIn('async function requestCharacterPortrait()', html)
        self.assertIn('async function requestCharacterVideo()', html)
        self.assertIn('function renderPersonaMedia()', html)

    def test_persona_card_script_contains_video_task_polling_hooks(self):
        html = Path("D:/个人信息文件/项目开发/Reply-by-voice/index.html").read_text(encoding="utf-8")
        self.assertIn('videoTaskId: ""', html)
        self.assertIn('videoTaskStatus: ""', html)
        self.assertIn('async function pollCharacterVideoTask(taskId, requestToken, character)', html)
        self.assertIn('await fetch(`/api/character-media/video/${taskId}`)', html)


if __name__ == "__main__":
    unittest.main()
