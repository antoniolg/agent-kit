import importlib.util
from importlib.machinery import SourceFileLoader
import pathlib
import sys
import unittest


SCRIPT_DIR = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

loader = SourceFileLoader("email_open", str(SCRIPT_DIR / "email-open"))
spec = importlib.util.spec_from_loader("email_open", loader)
email_open = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(email_open)


class EmailOpenTests(unittest.TestCase):
    def test_extracts_top_level_gmail_attachments(self):
        msg_data = {
            "attachments": [
                {
                    "filename": "Invoice-LHBFTW56-0009.pdf",
                    "mimeType": "application/pdf",
                    "size": 32043,
                    "sizeHuman": "31.3 KB",
                    "attachmentId": "att-1",
                }
            ]
        }

        attachments = email_open._extract_gmail_attachments(msg_data)

        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0]["filename"], "Invoice-LHBFTW56-0009.pdf")
        self.assertEqual(attachments[0]["attachment_id"], "att-1")

    def test_falls_back_to_payload_parts_when_needed(self):
        msg_data = {
            "message": {
                "payload": {
                    "parts": [
                        {
                            "mimeType": "multipart/mixed",
                            "parts": [
                                {
                                    "filename": "Receipt.pdf",
                                    "mimeType": "application/pdf",
                                    "body": {"attachmentId": "att-2", "size": 123},
                                }
                            ],
                        }
                    ]
                }
            }
        }

        attachments = email_open._extract_gmail_attachments(msg_data)

        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0]["filename"], "Receipt.pdf")
        self.assertEqual(attachments[0]["attachment_id"], "att-2")


if __name__ == "__main__":
    unittest.main()
