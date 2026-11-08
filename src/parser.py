import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


def timestamp_to_seconds(ts_str: str) -> Optional[float]:
    """Convert MM:SS or MM:SS.SS to float seconds."""
    if not ts_str:
        return None
    ts_str = ts_str.strip().strip("()")
    parts = ts_str.split(":")
    if len(parts) == 2:
        try:
            return int(parts[0]) * 60 + float(parts[1])
        except ValueError:
            return None
    elif len(parts) == 3:
        try:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        except ValueError:
            return None
    return None


def seconds_to_timestamp(seconds: float) -> str:
    """Convert float seconds to MM:SS.SS string."""
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins:02d}:{secs:05.2f}"


def seconds_to_display_time(seconds: float) -> str:
    """Convert float seconds to MM:SS display format."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def normalize_speaker(header: str) -> tuple[str, Optional[str], Optional[str]]:
    """
    Parse a header like:
    - 'CAMERA'
    - 'ACTION'
    - 'SOUND FX'
    - 'LADY JULIANA (Confused, Breathless)'
    - 'JULIANA (V.O.) (Reflective, Vulnerable)'
    - 'THE FORMER GROOM (Cold, Callous)'
    Returns (event_type, speaker_name, tone_direction).
    """
    cleaned = header.strip()
    upper = cleaned.upper()

    if upper.startswith("CAMERA"):
        return "CAMERA", None, None
    if upper.startswith("ACTION"):
        return "ACTION", None, None
    if upper.startswith("SOUND"):
        return "SOUND_FX", None, None

    # Character dialogue: look for emotions / instructions in parentheses
    tones = re.findall(r"\(([^)]+)\)", cleaned)
    tone_str = ", ".join(tones) if tones else None

    # Strip out parentheticals to extract clean speaker name
    speaker = re.sub(r"\([^)]*\)", "", cleaned).strip().strip(":")
    # Normalize common speaker aliases
    speaker_upper = speaker.upper()
    if "JULIANA" in speaker_upper:
        speaker = "JULIANA"
    elif "GERALD" in speaker_upper or "FORMER GROOM" in speaker_upper:
        speaker = "GERALD"
    elif "CLARISSA" in speaker_upper or "GOLD GOWN" in speaker_upper:
        speaker = "CLARISSA"
    elif "MATRIARCH" in speaker_upper:
        speaker = "MATRIARCH"
    elif "ASHCROFT" in speaker_upper:
        speaker = "LORD ASHCROFT"
    elif "SOLDIER" in speaker_upper or "DUKE" in speaker_upper:
        speaker = "DUKE"

    return "DIALOGUE", speaker, tone_str


class ScreenplayParser:
    """Parses standard microdrama screenplays with timestamped events."""

    def __init__(self, input_dir: str):
        self.input_dir = Path(input_dir)

    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        return self.parse_text(text, filename=file_path.name)

    def parse_text(self, text: str, filename: str = "") -> Dict[str, Any]:
        # 1. Episode metadata
        ep_m = re.search(r"EPISODE NUMBER:\s*(?:Episode\s*)?(\d+)", text, re.IGNORECASE)
        episode_num = int(ep_m.group(1)) if ep_m else 0

        logline_m = re.search(r"EPISODE LOGLINE:\s*(.+?)(?=\n[A-Z0-9 _-]+:|\n---|\Z)", text, re.DOTALL)
        logline = logline_m.group(1).strip() if logline_m else ""

        notes_m = re.search(r"CONTINUITY NOTES:\s*(.+?)(?=\n---|\nSCENE|\Z)", text, re.DOTALL)
        continuity = notes_m.group(1).strip() if notes_m else ""

        # 2. Extract scenes
        scene_splits = re.split(r"(SCENE\s+\d+)", text, flags=re.IGNORECASE)
        scenes = []
        events = []
        event_counter = 0

        for i in range(1, len(scene_splits), 2):
            scene_label = scene_splits[i].strip()
            scene_body = scene_splits[i + 1]

            # Scene number
            num_m = re.search(r"\d+", scene_label)
            scene_num = int(num_m.group(0)) if num_m else len(scenes) + 1

            # Heading
            heading_m = re.search(r"Scene heading:\s*(.+)", scene_body, re.IGNORECASE)
            heading = heading_m.group(1).strip() if heading_m else ""

            # Scene start & end
            start_m = re.search(r"Scene start:\s*(\S+)", scene_body, re.IGNORECASE)
            end_m = re.search(r"Scene end:\s*(\S+)", scene_body, re.IGNORECASE)
            s_sec = timestamp_to_seconds(start_m.group(1)) if start_m else 0.0
            e_sec = timestamp_to_seconds(end_m.group(1)) if end_m else 0.0

            scenes.append({
                "scene_number": scene_num,
                "label": scene_label,
                "heading": heading,
                "start": s_sec,
                "end": e_sec,
                "duration": round(max(0.0, (e_sec or 0.0) - (s_sec or 0.0)), 2)
            })

            # Events within scene: blocks split by **HEADER:**
            blocks = re.split(r"\*\*([^*]+?):\*\*", scene_body)
            for b_idx in range(1, len(blocks), 2):
                header = blocks[b_idx].strip()
                body = blocks[b_idx + 1].strip()

                time_match = re.search(
                    r"Start:\s*\(?(\d{2}:\d{2}(?:\.\d+)?)\)?\s*\|\s*End:\s*\(?(\d{2}:\d{2}(?:\.\d+)?)\)?",
                    body
                )
                if not time_match:
                    continue

                start_val = timestamp_to_seconds(time_match.group(1))
                end_val = timestamp_to_seconds(time_match.group(2))
                if start_val is None or end_val is None:
                    continue

                # Strip out the Start/End line to leave content
                content = re.sub(
                    r"Start:\s*\(?\d{2}:\d{2}(?:\.\d+)?\)?\s*\|\s*End:\s*\(?\d{2}:\d{2}(?:\.\d+)?\)?",
                    "",
                    body
                ).strip()

                # Clean quotes around dialogue
                cleaned_content = content.strip().strip('"').strip("'")

                ev_type, speaker, tone = normalize_speaker(header)
                event_counter += 1

                events.append({
                    "event_id": f"ep{episode_num}_e{event_counter:03d}",
                    "scene_number": scene_num,
                    "type": ev_type,
                    "speaker": speaker,
                    "tone": tone,
                    "start": round(start_val, 2),
                    "end": round(end_val, 2),
                    "duration": round(max(0.1, end_val - start_val), 2),
                    "content": cleaned_content,
                    "raw_header": header
                })

        total_duration = max([e["end"] for e in events]) if events else (scenes[-1]["end"] if scenes else 0.0)

        return {
            "episode": episode_num,
            "filename": filename,
            "logline": logline,
            "continuity": continuity,
            "scenes": scenes,
            "events": events,
            "total_duration": round(total_duration, 2),
            "events_count": len(events)
        }

    def parse_all(self) -> List[Dict[str, Any]]:
        files = sorted(self.input_dir.glob("*.txt"))
        parsed = []
        for f in files:
            p = self.parse_file(f)
            parsed.append(p)
        # Sort by episode number
        parsed.sort(key=lambda x: x["episode"])
        return parsed


def main():
    root = Path(__file__).resolve().parent.parent
    input_dir = root / "data/input/episodes"
    parser = ScreenplayParser(str(input_dir))
    episodes = parser.parse_all()

    out_file = root / "data/processed/parsed_episodes.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(episodes, f, indent=2, ensure_ascii=False)

    print(f"Successfully parsed {len(episodes)} episodes.")
    print(f"Total events extracted: {sum(e['events_count'] for e in episodes)}")
    print(f"Output saved to: {out_file}")


if __name__ == "__main__":
    main()
