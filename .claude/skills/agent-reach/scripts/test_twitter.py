"""Offline tests for scripts/twitter.py (no network, no twitter-cli needed)."""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import twitter  # noqa: E402

CFG = (
    "groq_api_key: gsk_x\n"
    "twitter_auth_token: 'AUTH123'\n"
    'twitter_ct0: "CT0456"  # comment\n'
)


class TwitterWrapperTests(unittest.TestCase):
    def test_reads_quoted_values_and_strips_comment(self):
        self.assertEqual(twitter.read_config_value(CFG, "twitter_auth_token"), "AUTH123")
        self.assertEqual(twitter.read_config_value(CFG, "twitter_ct0"), "CT0456")
        self.assertEqual(twitter.read_config_value(CFG, "nope"), "")

    def test_config_fills_missing_env(self):
        env = twitter.build_env({}, CFG)
        self.assertEqual(env["TWITTER_AUTH_TOKEN"], "AUTH123")
        self.assertEqual(env["TWITTER_CT0"], "CT0456")

    def test_existing_env_wins(self):
        env = twitter.build_env({"TWITTER_AUTH_TOKEN": "FROM_ENV"}, CFG)
        self.assertEqual(env["TWITTER_AUTH_TOKEN"], "FROM_ENV")
        self.assertEqual(env["TWITTER_CT0"], "CT0456")

    def test_redact_hides_both_values(self):
        env = twitter.build_env({}, CFG)
        out = twitter.redact("a AUTH123 b CT0456 c", env)
        self.assertNotIn("AUTH123", out)
        self.assertNotIn("CT0456", out)

    def test_missing_credentials_exit_2(self):
        old = os.environ.copy()
        try:
            for k in twitter.KEYS:
                os.environ.pop(k, None)
            os.environ["AGENT_REACH_CONFIG"] = str(Path(__file__).with_name("does-not-exist.yaml"))
            self.assertEqual(twitter.main(["search", "x"]), 2)
        finally:
            os.environ.clear()
            os.environ.update(old)


if __name__ == "__main__":
    unittest.main()
