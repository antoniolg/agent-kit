import importlib.util
from importlib.machinery import SourceFileLoader
import pathlib
import sys
import unittest
from unittest import mock


SCRIPT_DIR = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

loader = SourceFileLoader("slack_inbox", str(SCRIPT_DIR / "slack-inbox"))
spec = importlib.util.spec_from_loader("slack_inbox", loader)
slack_inbox = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(slack_inbox)


class SlackInboxTests(unittest.TestCase):
    def test_enriches_missing_last_read_even_without_unread_hint(self):
        convs = [
            {
                "id": "C1",
                "is_im": False,
                "updated": 2_000,
                "unread_count": 0,
            }
        ]

        with mock.patch.object(
            slack_inbox,
            "_fetch_conversation_info",
            return_value={"id": "C1", "last_read": "1000"},
        ):
            enriched = slack_inbox._enrich_conversations(convs, token="fake-token")

        self.assertEqual(enriched[0]["last_read"], "1000")
        self.assertTrue(slack_inbox._should_check_history(enriched[0]))

    def test_skips_history_when_updated_is_not_newer_than_last_read(self):
        conv = {
            "id": "C1",
            "last_read": "2000",
            "updated": 1_500,
            "unread_count": 0,
        }

        self.assertFalse(slack_inbox._should_check_history(conv))


if __name__ == "__main__":
    unittest.main()
