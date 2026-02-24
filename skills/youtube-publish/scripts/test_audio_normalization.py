#!/usr/bin/env python3
import unittest

from audio_normalization import evaluate_normalization_need


class TestEvaluateNormalizationNeed(unittest.TestCase):
    def test_within_target_skips_normalization(self):
        needs, reasons = evaluate_normalization_need(
            metrics={
                "input_i": -14.2,
                "input_tp": -1.3,
                "input_lra": 6.5,
                "input_thresh": -24.0,
                "target_offset": 0.2,
            },
            target_lufs=-14.0,
            target_true_peak=-1.0,
            max_lra=9.0,
            lufs_tolerance=1.0,
            true_peak_tolerance=0.3,
        )
        self.assertFalse(needs)
        self.assertEqual(reasons, [])

    def test_out_of_target_requires_normalization(self):
        needs, reasons = evaluate_normalization_need(
            metrics={
                "input_i": -18.5,
                "input_tp": -0.2,
                "input_lra": 12.0,
                "input_thresh": -28.0,
                "target_offset": 4.5,
            },
            target_lufs=-14.0,
            target_true_peak=-1.0,
            max_lra=9.0,
            lufs_tolerance=1.0,
            true_peak_tolerance=0.3,
        )
        self.assertTrue(needs)
        self.assertGreaterEqual(len(reasons), 2)


if __name__ == "__main__":
    unittest.main()
