import unittest
from unittest.mock import patch
from io import BytesIO
from vision.ollama_vision import validate_image, analyze_image, MODEL


class VisionTest(unittest.TestCase):
    def test_png(self):
        self.assertEqual(validate_image(b"\x89PNG\r\n\x1a\nabc"), "image/png")

    def test_webp(self):
        self.assertEqual(validate_image(b"RIFF1234WEBPabc"), "image/webp")

    def test_reject_unknown(self):
        with self.assertRaises(ValueError):
            validate_image(b"hello")

    def test_reject_large(self):
        with self.assertRaises(ValueError):
            validate_image(b"x" * (12 * 1024 * 1024 + 1))

    @patch("vision.ollama_vision.urlopen")
    def test_request_uses_11b(self, mock_urlopen):
        import json
        mock_urlopen.return_value.__enter__.return_value = BytesIO(json.dumps({"message": {"content": "test"}, "done": True}).encode())
        result = analyze_image(b"\x89PNG\r\n\x1a\nabc", "Co widzisz?")
        self.assertEqual(result["model"], MODEL)
        self.assertEqual(result["answer"], "test")
        request = mock_urlopen.call_args.args[0]
        self.assertEqual(json.loads(request.data)["model"], "llama3.2-vision:11b")

    def test_reject_bad_endpoint(self):
        with self.assertRaises(ValueError):
            analyze_image(b"\x89PNG\r\n\x1a\nabc", "test", base_url="file:///etc/passwd")


if __name__ == "__main__":
    unittest.main()
