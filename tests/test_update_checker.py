import unittest

from utils.update_checker import check_for_update, is_newer_version, normalize_version


class UpdateCheckerTests(unittest.TestCase):
    def test_normalize_version_removes_v_prefix(self):
        self.assertEqual(normalize_version("v1.2.3"), "1.2.3")
        self.assertEqual(normalize_version(" V2.0.0 "), "2.0.0")

    def test_is_newer_version_compares_semantic_versions(self):
        self.assertTrue(is_newer_version("v1.1.0", "1.0.0"))
        self.assertFalse(is_newer_version("v1.0.0", "1.0.0"))
        self.assertFalse(is_newer_version("invalid", "1.0.0"))

    def test_check_for_update_detects_new_release(self):
        def fetch_release():
            return {
                "tag_name": "v1.1.0",
                "html_url": "https://github.com/matiasrmb/estacionamiento-central/releases/tag/v1.1.0",
                "prerelease": False,
            }

        result = check_for_update("1.0.0", fetch_release)

        self.assertTrue(result.update_available)
        self.assertEqual(result.latest_version, "1.1.0")
        self.assertEqual(result.current_version, "1.0.0")
        self.assertEqual(
            result.release_url,
            "https://github.com/matiasrmb/estacionamiento-central/releases/tag/v1.1.0",
        )

    def test_check_for_update_ignores_prerelease(self):
        def fetch_release():
            return {
                "tag_name": "v2.0.0-beta.1",
                "html_url": "https://github.com/matiasrmb/estacionamiento-central/releases/tag/v2.0.0-beta.1",
                "prerelease": True,
            }

        result = check_for_update("1.0.0", fetch_release)

        self.assertFalse(result.update_available)

    def test_check_for_update_fails_silently(self):
        def fetch_release():
            raise OSError("network unavailable")

        result = check_for_update("1.0.0", fetch_release)

        self.assertFalse(result.update_available)
        self.assertIn("network unavailable", result.error)

    def test_check_for_update_ignores_malformed_response(self):
        result = check_for_update("1.0.0", lambda: None)

        self.assertFalse(result.update_available)
        self.assertIsNone(result.error)


if __name__ == "__main__":
    unittest.main()
