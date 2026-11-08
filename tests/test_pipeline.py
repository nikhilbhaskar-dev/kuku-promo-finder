import json
import os
import unittest
from pathlib import Path

from src.parser import ScreenplayParser, timestamp_to_seconds, seconds_to_timestamp, normalize_speaker
from src.analyzer import DramaticAnalyzer, compute_hook_strength, compute_cliffhanger_strength
from src.ranker import calculate_strategic_score
from src.importer import EpisodeImporter


class TestPromoFinder(unittest.TestCase):

    def test_timestamp_conversions(self):
        self.assertEqual(timestamp_to_seconds("00:00.00"), 0.0)
        self.assertEqual(timestamp_to_seconds("01:30.00"), 90.0)
        self.assertEqual(timestamp_to_seconds("(02:15.50)"), 135.5)
        self.assertEqual(seconds_to_timestamp(90.0), "01:30.00")

    def test_normalize_speaker(self):
        ev_type, speaker, tone = normalize_speaker("LADY JULIANA (Confused, Breathless):")
        self.assertEqual(ev_type, "DIALOGUE")
        self.assertEqual(speaker, "JULIANA")
        self.assertIn("Confused", tone)

        ev_type, speaker, tone = normalize_speaker("CAMERA:")
        self.assertEqual(ev_type, "CAMERA")
        self.assertIsNone(speaker)

        ev_type, speaker, tone = normalize_speaker("THE FORMER GROOM (Cold, Callous):")
        self.assertEqual(speaker, "GERALD")

    def test_duration_constraints(self):
        analyzer = DramaticAnalyzer(min_duration=20.0, max_duration=60.0)
        mock_events = [
            {"event_id": "1", "start": 0.0, "end": 10.0, "type": "DIALOGUE", "speaker": "JULIANA", "tone": "Furious", "content": "How dare you leave me at the altar?"},
            {"event_id": "2", "start": 10.0, "end": 25.0, "type": "DIALOGUE", "speaker": "GERALD", "tone": "Cold", "content": "I cannot marry you."},
            {"event_id": "3", "start": 25.0, "end": 45.0, "type": "DIALOGUE", "speaker": "JULIANA", "tone": "Tearful", "content": "Who is she?"}
        ]
        mock_ep = {"episode": 1, "events": mock_events}
        cands = analyzer.analyze_episode(mock_ep)
        for c in cands:
            self.assertGreaterEqual(c["total_duration"], 20.0)
            self.assertLessEqual(c["total_duration"], 60.0)

    def test_strategic_score_calculation(self):
        mock_promo_ep1 = {
            "episode": 1,
            "hook_strength": 9.0,
            "cliffhanger_strength": 9.0,
            "story_clarity": 9.0,
            "emotional_impact": 9.0
        }
        score_ep1 = calculate_strategic_score(mock_promo_ep1)
        self.assertEqual(score_ep1, 9.25)

    def test_importer_validation(self):
        importer = EpisodeImporter()
        valid_sample = """
        EPISODE NUMBER: Episode 99
        EPISODE LOGLINE: Test logline
        --- SCRIPT START ---
        SCENE 01
        Scene start: 00:00.00
        **CAMERA:**
        Start: (00:00.00) | End: (00:02.00)
        Shot
        **JULIANA (Furious):**
        Start: (00:02.00) | End: (00:06.00)
        "You lied to me!"
        **GERALD (Cold):**
        Start: (00:06.00) | End: (00:10.00)
        "And what will you do about it?"
        """
        val = importer.validate_screenplay_text(valid_sample, "episode-099.txt")
        self.assertTrue(val["is_valid"])
        self.assertEqual(val["episode_number"], 99)
        self.assertEqual(val["events_count"], 3)


if __name__ == "__main__":
    unittest.main()
