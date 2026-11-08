import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent


class QualityAuditor:
    """
    Audits promo candidate quality, identifies systematic edge cases,
    and flags failure modes where automated tools pick badly.
    """

    def __init__(self, ranked_file: Path):
        self.ranked_file = ranked_file
        with open(ranked_file, "r", encoding="utf-8") as f:
            self.promos = json.load(f)

    def run_audit(self) -> Dict[str, Any]:
        failure_categories = {
            "camera_heavy_openings": [],
            "lore_heavy_context": [],
            "soft_resolution_cliffhangers": [],
            "monologue_heavy": [],
            "high_quality_approved": []
        }

        for p in self.promos:
            events = p.get("events_summary", [])
            weaknesses = []

            # 1. Camera-heavy opening check (first event is CAMERA > 2.5s)
            if events and events[0]["type"] == "CAMERA":
                cam_dur = events[0]["end"] - events[0]["start"]
                if cam_dur >= 2.5:
                    weaknesses.append(
                        f"Opens on a {cam_dur:.1f}s silent camera shot before first line, risking 1.5s scroll-drop on TikTok."
                    )
                    failure_categories["camera_heavy_openings"].append({
                        "rank": p.get("overall_rank"),
                        "episode": p["episode"],
                        "issue": "Slow visual grab",
                        "details": weaknesses[-1]
                    })

            # 2. Lore-heavy / obscure context (Episode > 20 with no primary archetype mention)
            if p["episode"] > 20:
                all_text = " ".join(e["content"].lower() for e in events)
                archetypes = ["juliana", "gerald", "clarissa", "duke", "soldier", "husband", "sister", "bride"]
                if not any(a in all_text for a in archetypes):
                    weaknesses.append(
                        "Dialogue references secondary plotlines without mentioning core protagonist/antagonist dynamics; cold viewers may lack context."
                    )
                    failure_categories["lore_heavy_context"].append({
                        "rank": p.get("overall_rank"),
                        "episode": p["episode"],
                        "issue": "Lore dependency",
                        "details": weaknesses[-1]
                    })

            # 3. Soft resolution cut (cliffhanger ends on neutral phrase or non-interrogative)
            if events and events[-1]["type"] == "DIALOGUE":
                last_line = events[-1]["content"].strip()
                if last_line.endswith(".") and not any(w in last_line.lower() for w in ["never", "regret", "kneel", "beg", "die", "kill", "leave", "pay"]):
                    weaknesses.append(
                        "Ending dialogue is grammatically complete rather than open-ended, reducing compulsive click urgency."
                    )
                    failure_categories["soft_resolution_cliffhangers"].append({
                        "rank": p.get("overall_rank"),
                        "episode": p["episode"],
                        "issue": "Soft cutoff",
                        "details": weaknesses[-1]
                    })

            # 4. Monologue heavy (single speaker has > 80% of lines)
            dialogue_evs = [e for e in events if e["type"] == "DIALOGUE"]
            if dialogue_evs:
                speakers = [e.get("speaker") for e in dialogue_evs if e.get("speaker")]
                if speakers and len(set(speakers)) == 1 and len(dialogue_evs) >= 3:
                    weaknesses.append("Segment is predominantly a monologue; lacks dynamic ping-pong confrontation.")
                    failure_categories["monologue_heavy"].append({
                        "rank": p.get("overall_rank"),
                        "episode": p["episode"],
                        "issue": "Monologue pacing",
                        "details": weaknesses[-1]
                    })

            if not weaknesses and p.get("final_score", 0) >= 8.5:
                failure_categories["high_quality_approved"].append({
                    "rank": p.get("overall_rank"),
                    "episode": p["episode"],
                    "score": p["final_score"]
                })

        audit_summary = {
            "total_promos_audited": len(self.promos),
            "camera_heavy_count": len(failure_categories["camera_heavy_openings"]),
            "lore_heavy_count": len(failure_categories["lore_heavy_context"]),
            "soft_resolution_count": len(failure_categories["soft_resolution_cliffhangers"]),
            "monologue_count": len(failure_categories["monologue_heavy"]),
            "flawless_high_quality_count": len(failure_categories["high_quality_approved"]),
            "failure_breakdown": failure_categories
        }

        return audit_summary


def main():
    ranked_file = ROOT / "data/processed/ranked_promos.json"
    auditor = QualityAuditor(ranked_file)
    summary = auditor.run_audit()

    report_file = ROOT / "raw_outputs/quality_audit_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("=== Quality Audit Report ===")
    print(f"Total evaluated promos: {summary['total_promos_audited']}")
    print(f"Flawless high-confidence promos: {summary['flawless_high_quality_count']}")
    print(f"Camera-heavy opening warnings: {summary['camera_heavy_count']}")
    print(f"Lore-heavy / context-dependent warnings: {summary['lore_heavy_count']}")
    print(f"Soft resolution / weak cliffhanger warnings: {summary['soft_resolution_count']}")
    print(f"Saved audit report to: {report_file}")


if __name__ == "__main__":
    main()
