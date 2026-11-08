import argparse
import json
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EPISODES_DIR = ROOT / "data/input/episodes"


class EpisodeImporter:
    """
    Handles importing, validating, and registering new episode screenplays
    from single files, multiple files, folders, or ZIP archives.
    """

    def __init__(self, target_dir: Optional[Path] = None):
        self.target_dir = target_dir or EPISODES_DIR
        self.target_dir.mkdir(parents=True, exist_ok=True)

    def validate_screenplay_text(self, text: str, filename: str = "") -> Dict[str, Any]:
        """
        Validates whether text matches Kuku microdrama screenplay format:
        - Detects episode number
        - Checks for scene markers
        - Checks for timestamp patterns: Start: (MM:SS) | End: (MM:SS)
        - Checks for dialogue / camera / action tags
        """
        # 1. Episode Number
        ep_m = re.search(r"EPISODE NUMBER:\s*(?:Episode\s*)?(\d+)", text, re.IGNORECASE)
        if not ep_m:
            fn_m = re.search(r"episode[_-]?(\d+)", filename, re.IGNORECASE)
            ep_num = int(fn_m.group(1)) if fn_m else None
        else:
            ep_num = int(ep_m.group(1))

        # 2. Scene Markers
        scenes = re.findall(r"SCENE\s+\d+", text, re.IGNORECASE)

        # 3. Timestamps
        timestamps = re.findall(
            r"Start:\s*\(?(\d{2}:\d{2}(?:\.\d+)?)\)?\s*\|\s*End:\s*\(?(\d{2}:\d{2}(?:\.\d+)?)\)?",
            text
        )

        # 4. Headers / Event types
        headers = re.findall(r"\*\*([^*]+?):\*\*", text)

        is_valid = bool(timestamps and len(timestamps) >= 3)
        warnings = []

        if ep_num is None:
            warnings.append("Could not detect episode number; defaulted to 0.")
            ep_num = 0
        if not scenes:
            warnings.append("No explicit SCENE markers found.")
        if len(timestamps) < 5:
            warnings.append(f"Only {len(timestamps)} timestamped events found (typical episode has 30+).")
        if not headers:
            warnings.append("No bold event headers (**CAMERA:**, **ACTION:**, or characters) found.")

        return {
            "is_valid": is_valid,
            "filename": filename,
            "episode_number": ep_num,
            "scenes_count": len(scenes),
            "events_count": len(timestamps),
            "headers_count": len(headers),
            "warnings": warnings,
            "char_count": len(text)
        }

    def import_text(self, text: str, filename: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Validates and writes screenplay text to target episodes directory."""
        val = self.validate_screenplay_text(text, filename)
        ep_num = val["episode_number"]

        if not filename.endswith(".txt"):
            filename = f"episode-{ep_num:03d}-{filename}.txt"

        clean_filename = re.sub(r"[^\w\.-]", "_", filename)
        dest_path = self.target_dir / clean_filename

        dest_path.write_text(text, encoding="utf-8")
        return True, str(dest_path), val

    def import_from_zip(self, zip_path: Path, clear_existing: bool = False) -> List[Dict[str, Any]]:
        """Extracts and imports all .txt files from a ZIP archive."""
        if clear_existing:
            self.clear_episodes()

        results = []
        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in zf.infolist():
                if member.is_dir() or not member.filename.lower().endswith(".txt"):
                    continue
                # Skip macOS metadata files
                if "__MACOSX" in member.filename or Path(member.filename).name.startswith("."):
                    continue

                content = zf.read(member).decode("utf-8", errors="ignore")
                fname = Path(member.filename).name
                success, path, val = self.import_text(content, fname)
                results.append(val)

        return results

    def import_from_folder(self, folder_path: Path, clear_existing: bool = False) -> List[Dict[str, Any]]:
        """Imports all .txt files from a folder."""
        if clear_existing:
            self.clear_episodes()

        results = []
        for file in sorted(folder_path.glob("*.txt")):
            if file.name.startswith("."):
                continue
            content = file.read_text(encoding="utf-8", errors="ignore")
            success, path, val = self.import_text(content, file.name)
            results.append(val)

        return results

    def clear_episodes(self):
        """Removes all currently loaded episode files."""
        for f in self.target_dir.glob("*.txt"):
            try:
                f.unlink()
            except OSError:
                pass


def main():
    parser = argparse.ArgumentParser(description="Import new screenplay episodes into Kuku Promo Finder")
    parser.add_argument("--input", "-i", type=str, required=True, help="Path to .txt file, folder, or .zip archive")
    parser.add_argument("--clear", action="store_true", help="Clear existing episodes before importing")
    parser.add_argument("--run-pipeline", "-r", action="store_true", help="Automatically run pipeline after import")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Path {input_path} does not exist.")
        sys.exit(1)

    importer = EpisodeImporter()
    imported = []

    if input_path.is_file() and input_path.suffix.lower() == ".zip":
        print(f"Extracting episodes from ZIP: {input_path}...")
        imported = importer.import_from_zip(input_path, clear_existing=args.clear)
    elif input_path.is_file() and input_path.suffix.lower() == ".txt":
        print(f"Importing single screenplay: {input_path}...")
        content = input_path.read_text(encoding="utf-8", errors="ignore")
        success, dest, val = importer.import_text(content, input_path.name)
        imported = [val]
    elif input_path.is_dir():
        print(f"Importing episodes from folder: {input_path}...")
        imported = importer.import_from_folder(input_path, clear_existing=args.clear)
    else:
        print(f"Error: Unsupported input format {input_path}. Please provide a .txt file, folder, or .zip archive.")
        sys.exit(1)

    print(f"\nSuccessfully imported {len(imported)} episode(s):")
    for res in imported[:10]:
        status = "✓ Valid" if res["is_valid"] else "⚠️ Warning"
        print(f"  [{status}] Ep {res['episode_number']}: {res['filename']} ({res['events_count']} events, {res['scenes_count']} scenes)")
    if len(imported) > 10:
        print(f"  ... and {len(imported) - 10} more.")

    if args.run_pipeline:
        print("\nTriggering pipeline re-run...")
        from src.pipeline import run_full_pipeline
        run_full_pipeline()


if __name__ == "__main__":
    main()
