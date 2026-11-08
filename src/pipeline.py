import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Add ROOT to sys.path so imports work
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.parser import ScreenplayParser
from src.analyzer import DramaticAnalyzer
from src.ranker import rank_and_export_all
from src.quality_audit import QualityAuditor


def run_full_pipeline(use_llm: bool = False, model_name: str = "gemini-3.8-flash"):
    print("=" * 60)
    print("🚀 KUKU PROMO FINDER — END-TO-END PIPELINE")
    print("=" * 60)
    t0 = time.time()

    # Step 1: Parse Screenplays
    print("\n[Step 1/4] Parsing all 50 episode screenplays...")
    input_dir = ROOT / "data/input/episodes"
    parser = ScreenplayParser(str(input_dir))
    episodes = parser.parse_all()

    parsed_path = ROOT / "data/processed/parsed_episodes.json"
    parsed_path.parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(parsed_path, "w", encoding="utf-8") as f:
        json.dump(episodes, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Parsed {len(episodes)} episodes, {sum(e['events_count'] for e in episodes)} total events.")

    # Step 2: Extract Dramatic Candidate Windows
    print("\n[Step 2/4] Extracting candidate promo windows (20s-60s)...")
    analyzer = DramaticAnalyzer(min_duration=20.0, max_duration=60.0)
    all_candidates = []
    for ep in episodes:
        cands = analyzer.analyze_episode(ep)
        all_candidates.extend(cands)

    candidates_path = ROOT / "data/processed/candidate_promos.json"
    with open(candidates_path, "w", encoding="utf-8") as f:
        json.dump(all_candidates, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Extracted {len(all_candidates)} candidate promos across all episodes.")

    # Step 3: Rank, Categorize, and Export
    print("\n[Step 3/4] Ranking promos and generating raw exports...")
    rank_and_export_all()
    print("  ✓ Top 50 promos, per-episode promos, and CSV exported.")

    # Step 4: Quality & Failure Modes Audit
    print("\n[Step 4/4] Running Quality & Failure Modes Audit...")
    ranked_file = ROOT / "data/processed/ranked_promos.json"
    auditor = QualityAuditor(ranked_file)
    summary = auditor.run_audit()
    audit_path = ROOT / "raw_outputs/quality_audit_report.json"
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Quality audit complete: {summary['flawless_high_quality_count']} flawless promos, {summary['camera_heavy_count']} camera warnings flagged.")

    elapsed = time.time() - t0
    print("\n" + "=" * 60)
    print(f"🎉 Pipeline finished successfully in {elapsed:.2f} seconds!")
    print("All outputs available in:")
    print(f"  - raw_outputs/ranked_promos_top50.json")
    print(f"  - raw_outputs/all_episodes_best_promos.json")
    print(f"  - raw_outputs/promos_export.csv")
    print(f"  - raw_outputs/by_episode/ (50 files)")
    print(f"  - raw_outputs/quality_audit_report.json")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kuku Promo Finder Pipeline")
    parser.add_argument("--use-llm", action="store_true", help="Enrich top promos with LLM")
    parser.add_argument("--model", type=str, default="gemini-3.8-flash", help="LLM model name")
    args = parser.parse_args()

    run_full_pipeline(use_llm=args.use_llm, model_name=args.model)
