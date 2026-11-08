import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Key dramatic indicators for microdrama promos
HOOK_KEYWORDS = {
    # High-conflict dialogue words
    "marry", "marriage", "wedding", "altar", "groom", "bride", "gown", "dress",
    "divorce", "betray", "betrayal", "cheating", "affair", "mistress", "bastard",
    "cripple", "broken", "soldier", "duke", "monster", "disown", "disowned",
    "worthless", "trash", "whore", "slap", "kneel", "beg", "strip", "ruined",
    "kill", "die", "blood", "poison", "arrest", "guard", "liar", "lie", "secret",
    "shame", "humiliation", "refuse", "stop", "never", "dare", "shut up", "disgusting"
}

CLIFFHANGER_KEYWORDS = {
    "who", "why", "how", "what", "dare", "never", "regret", "kneel", "beg",
    "kill", "destroy", "watch", "see", "sign", "leave", "pay", "answer",
    "mine", "husband", "wife", "duke", "choice", "consequences", "dead", "alive"
}

HIGH_EMOTION_TONES = {
    "furious", "cold", "commanding", "mocking", "sneering", "spiteful", "cruel",
    "desperate", "shouting", "screaming", "defiant", "steely", "tearful",
    "taunting", "arrogant", "shocked", "shellshocked", "venomous", "icy", "ruthless"
}

PHYSICAL_ACTION_KEYWORDS = {
    "slap", "slaps", "grab", "grabs", "shove", "shoves", "push", "pushes",
    "kneel", "kneels", "drop", "drops", "tear", "tears", "strike", "strikes",
    "kick", "kicks", "slam", "slams", "shatter", "shatters", "collapse", "collapses",
    "seize", "seizes", "gasp", "gasps", "tremble", "trembles", "draws weapon"
}


def compute_hook_strength(events: List[Dict[str, Any]], window_start: float) -> Tuple[float, str]:
    """
    Evaluate the first 3.5 seconds of the window.
    Returns (score_1_to_10, hook_description).
    """
    first_events = [e for e in events if e["start"] <= window_start + 3.5]
    if not first_events:
        first_events = events[:1]

    score = 5.0
    reasons = []

    dialogue_events = [e for e in first_events if e["type"] == "DIALOGUE"]
    action_events = [e for e in first_events if e["type"] == "ACTION"]
    camera_events = [e for e in first_events if e["type"] == "CAMERA"]

    # 1. Immediate speech (starts within 1.5s)
    if dialogue_events:
        d = dialogue_events[0]
        start_delay = d["start"] - window_start
        if start_delay <= 1.0:
            score += 1.5
            reasons.append("immediate dialogue impact")
        elif start_delay <= 2.5:
            score += 0.8

        # Emotional tone check
        tone = (d["tone"] or "").lower()
        if any(t in tone for t in HIGH_EMOTION_TONES):
            score += 1.5
            reasons.append(f"intense vocal delivery ({d['tone']})")

        # Shocking keywords
        words = set(re.findall(r"\w+", d["content"].lower()))
        matched_hook_words = words.intersection(HOOK_KEYWORDS)
        if matched_hook_words:
            score += 1.2
            reasons.append(f"high-stakes hook line ('{d['content'][:45]}...')")
        else:
            reasons.append(f"opens with dialogue: '{d['content'][:40]}...'")

    # 2. Physical action in opening
    if action_events:
        a = action_events[0]
        act_text = a["content"].lower()
        if any(k in act_text for k in PHYSICAL_ACTION_KEYWORDS):
            score += 1.5
            reasons.append("visceral physical action in opening")

    # 3. Only camera / slow visual start penalty
    if not dialogue_events and not action_events and camera_events:
        score -= 2.0
        reasons.append("pure camera shot opening with delayed narrative grab")

    score = max(1.0, min(10.0, round(score, 1)))

    # Generate hook summary sentence
    if dialogue_events:
        d = dialogue_events[0]
        speaker = d["speaker"] or "A character"
        hook_desc = f"{speaker} shocks the viewer with an immediate confrontation: \"{d['content']}\""
    elif action_events:
        hook_desc = f"Opens with immediate physical drama: {action_events[0]['content']}"
    else:
        hook_desc = f"Visual opening hook: {events[0]['content']}"

    return score, hook_desc


def compute_cliffhanger_strength(events: List[Dict[str, Any]], window_end: float) -> Tuple[float, str]:
    """
    Evaluate the final 4 seconds of the window.
    Returns (score_1_to_10, cliffhanger_description).
    """
    last_events = [e for e in events if e["end"] >= window_end - 4.0]
    if not last_events:
        last_events = events[-1:]

    score = 5.0
    reasons = []

    final_event = events[-1]

    if final_event["type"] == "DIALOGUE":
        content = final_event["content"].strip()
        speaker = final_event["speaker"] or "Character"

        # Interrogative or suspended cutoff
        if content.endswith("?"):
            score += 2.0
            reasons.append("unanswered provocative question cutoff")
        elif content.endswith("...") or content.endswith("--") or content.endswith("—"):
            score += 1.8
            reasons.append("sentence cut mid-revelation")
        elif content.endswith("!"):
            score += 1.2
            reasons.append("high-voltage exclamation cutoff")

        words = set(re.findall(r"\w+", content.lower()))
        if words.intersection(CLIFFHANGER_KEYWORDS):
            score += 1.0

        tone = (final_event["tone"] or "").lower()
        if any(t in tone for t in HIGH_EMOTION_TONES):
            score += 1.0

        cliff_desc = f"Cuts sharply on {speaker}'s unresolved words: \"{content}\", leaving the outcome hanging."

    elif final_event["type"] == "ACTION":
        act_text = final_event["content"].lower()
        if any(k in act_text for k in PHYSICAL_ACTION_KEYWORDS):
            score += 1.5
            reasons.append("cuts right as physical conflict escalates")
        cliff_desc = f"Freezes at the climax of physical escalation: {final_event['content']}"

    else:
        # CAMERA final event: often a dramatic close-up reaction
        score += 0.5
        cliff_desc = f"Cuts abruptly on a dramatic visual reaction: {final_event['content']}"

    score = max(1.0, min(10.0, round(score, 1)))
    return score, cliff_desc


def compute_clarity_score(events: List[Dict[str, Any]]) -> Tuple[float, str]:
    """
    Evaluate standalone comprehensibility:
    Can someone who has never seen the show understand who is who and what is at stake?
    """
    score = 6.0
    dialogue_events = [e for e in events if e["type"] == "DIALOGUE"]
    speakers = list({e["speaker"] for e in dialogue_events if e["speaker"]})

    # Needs at least 2 distinct characters in conflict or 1 intense confrontation
    if len(speakers) >= 2:
        score += 1.5
    elif len(speakers) == 1 and len(dialogue_events) >= 2:
        score += 0.8
    elif not dialogue_events:
        score -= 2.0

    # Archetype keywords that require zero lore
    all_text = " ".join(e["content"].lower() for e in events)
    archetype_words = {
        "marry", "wedding", "sister", "fiancé", "father", "daughter",
        "mother", "family", "bride", "groom", "soldier", "duke", "in-law"
    }
    if any(w in all_text for w in archetype_words):
        score += 1.5

    # Check for confusing jargon or off-screen names without context
    if "earl" in all_text and "council" in all_text and "decree" in all_text:
        score -= 0.5

    score = max(1.0, min(10.0, round(score, 1)))

    if len(speakers) >= 2:
        clarity_desc = f"Instantly readable clash between {', '.join(speakers[:2])} with clear relationship stakes."
    elif len(speakers) == 1:
        clarity_desc = f"Focused character breakdown of {speakers[0]}, clear emotional vulnerability."
    else:
        clarity_desc = "Visually descriptive sequence; relies heavily on physical atmosphere."

    return score, clarity_desc


def compute_emotional_impact(events: List[Dict[str, Any]]) -> Tuple[float, str]:
    """Evaluate conflict density and emotional pacing."""
    score = 5.0
    dialogue_events = [e for e in events if e["type"] == "DIALOGUE"]

    emotion_count = 0
    for d in dialogue_events:
        tone = (d.get("tone") or "").lower()
        if any(h in tone for h in HIGH_EMOTION_TONES):
            emotion_count += 1

    density = emotion_count / max(1, len(dialogue_events))
    if density >= 0.5:
        score += 2.5
    elif density >= 0.25:
        score += 1.5
    else:
        score += 0.5

    # Rapid turn-taking increases pace
    turns = len(dialogue_events)
    if turns >= 5:
        score += 1.5
    elif turns >= 3:
        score += 1.0

    score = max(1.0, min(10.0, round(score, 1)))
    desc = f"High emotional velocity with {emotion_count} high-intensity dialogue exchanges."
    return score, desc


def generate_why_it_works(
    hook_desc: str,
    cliff_desc: str,
    clarity_desc: str,
    duration: float,
    scores: Dict[str, float]
) -> str:
    """Generate concise, actionable marketing rationale for why this promo converts."""
    hook_score = scores.get("hook_strength", 7.0)
    cliff_score = scores.get("cliffhanger_strength", 7.0)

    reasons = []
    if hook_score >= 8.0:
        reasons.append("stops feed scroll with immediate high-status conflict")
    else:
        reasons.append("draws viewer into a clear character dilemma")

    if cliff_score >= 8.5:
        reasons.append("cuts at peak unresolved tension to drive instant next-episode clicks")
    else:
        reasons.append("leaves the audience needing immediate resolution")

    return (
        f"At {duration:.0f}s, this promo {reasons[0]} and {reasons[1]}, "
        f"delivering an emotionally complete micro-drama hook."
    )


def identify_weaknesses(events: List[Dict[str, Any]], scores: Dict[str, float]) -> str:
    """Transparently identify weaknesses / failure points for quality checking."""
    weaknesses = []
    first_ev = events[0]
    last_ev = events[-1]

    if scores.get("hook_strength", 10) < 7.0:
        weaknesses.append("Slower opening pacing; first 2 seconds lack an aggressive visual or audio shock.")

    if scores.get("cliffhanger_strength", 10) < 7.0:
        weaknesses.append("Cut-point does not end on an explicit question or shock line, reducing click urgency.")

    if scores.get("story_clarity", 10) < 7.0:
        weaknesses.append("Assumes some prior familiarity with character relationships or off-screen backstory.")

    if first_ev["type"] == "CAMERA" and (first_ev["end"] - first_ev["start"] >= 3.0):
        weaknesses.append("Opens on a wide camera shot without immediate dialogue, risking mobile feed scroll-by.")

    if not weaknesses:
        weaknesses.append("Strong overall; requires crisp sound design and punchy mobile audio mix to maximize retention.")

    return " ".join(weaknesses)


class DramaticAnalyzer:
    """Finds optimal continuous and joined promo segments across screenplay episodes."""

    def __init__(self, min_duration: float = 20.0, max_duration: float = 60.0):
        self.min_duration = min_duration
        self.max_duration = max_duration

    def analyze_episode(self, episode_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        ep_num = episode_data["episode"]
        events = episode_data["events"]
        candidates = []

        if not events:
            return candidates

        n = len(events)

        # 1. Candidate window search: pair natural dramatic start with natural dramatic end
        for i in range(n):
            start_ev = events[i]
            # Must start on a dialogue or an action, not an empty camera shot unless followed immediately by speech
            if start_ev["type"] not in ["DIALOGUE", "ACTION"]:
                if i + 1 < n and events[i + 1]["start"] - start_ev["start"] > 2.0:
                    continue

            start_time = start_ev["start"]

            for j in range(i, n):
                end_ev = events[j]
                end_time = end_ev["end"]
                dur = round(end_time - start_time, 2)

                if dur < self.min_duration:
                    continue
                if dur > self.max_duration:
                    break

                # End event should be dialogue or impactful action / dramatic camera close-up
                window_events = events[i : j + 1]

                hook_score, hook_desc = compute_hook_strength(window_events, start_time)
                cliff_score, cliff_desc = compute_cliffhanger_strength(window_events, end_time)
                clarity_score, clarity_desc = compute_clarity_score(window_events)
                emotion_score, emotion_desc = compute_emotional_impact(window_events)

                # Composite score with marketing weights
                composite_score = round(
                    0.30 * hook_score +
                    0.35 * cliff_score +
                    0.20 * clarity_score +
                    0.15 * emotion_score,
                    2
                )

                # Only keep candidates with viable potential
                if composite_score >= 6.0:
                    scores_dict = {
                        "hook_strength": hook_score,
                        "cliffhanger_strength": cliff_score,
                        "story_clarity": clarity_score,
                        "emotional_impact": emotion_score,
                        "composite_score": composite_score
                    }
                    why_works = generate_why_it_works(
                        hook_desc, cliff_desc, clarity_desc, dur, scores_dict
                    )
                    weaknesses = identify_weaknesses(window_events, scores_dict)

                    candidates.append({
                        "episode": ep_num,
                        "promo_type": "continuous",
                        "segments": [
                            {
                                "segment_index": 1,
                                "episode": ep_num,
                                "start": start_time,
                                "end": end_time,
                                "duration": dur,
                                "start_time_fmt": self.format_time(start_time),
                                "end_time_fmt": self.format_time(end_time)
                            }
                        ],
                        "total_duration": dur,
                        "hook_strength": hook_score,
                        "cliffhanger_strength": cliff_score,
                        "story_clarity": clarity_score,
                        "emotional_impact": emotion_score,
                        "composite_score": composite_score,
                        "hook": hook_desc,
                        "cliffhanger": cliff_desc,
                        "why_it_works": why_works,
                        "weaknesses": weaknesses,
                        "verdict": "SELECT" if composite_score >= 7.5 else "REJECT",
                        "events_summary": [
                            {
                                "start": e["start"],
                                "end": e["end"],
                                "type": e["type"],
                                "speaker": e["speaker"],
                                "content": e["content"]
                            }
                            for e in window_events
                        ]
                    })

        # 2. Non-Maximum Suppression (NMS) to eliminate near-duplicate overlapping windows
        pruned = self.non_maximum_suppression(candidates, iou_threshold=0.60)
        return pruned

    def non_maximum_suppression(
        self, candidates: List[Dict[str, Any]], iou_threshold: float = 0.60
    ) -> List[Dict[str, Any]]:
        """Remove redundant overlapping promo windows, keeping highest scored ones."""
        if not candidates:
            return []

        candidates.sort(key=lambda x: x["composite_score"], reverse=True)
        selected = []

        for cand in candidates:
            c_seg = cand["segments"][0]
            c_start, c_end = c_seg["start"], c_seg["end"]

            overlap = False
            for sel in selected:
                s_seg = sel["segments"][0]
                s_start, s_end = s_seg["start"], s_seg["end"]

                # Intersection over Union
                inter = max(0.0, min(c_end, s_end) - max(c_start, s_start))
                union = (c_end - c_start) + (s_end - s_start) - inter
                iou = inter / union if union > 0 else 0

                if iou > iou_threshold:
                    overlap = True
                    break

            if not overlap:
                selected.append(cand)

        return selected

    @staticmethod
    def format_time(seconds: float) -> str:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins:02d}:{secs:05.2f}"


def main():
    root = Path(__file__).resolve().parent.parent
    in_file = root / "data/processed/parsed_episodes.json"
    with open(in_file, "r", encoding="utf-8") as f:
        episodes = json.load(f)

    analyzer = DramaticAnalyzer(min_duration=20.0, max_duration=60.0)
    all_candidates = []

    for ep in episodes:
        cands = analyzer.analyze_episode(ep)
        all_candidates.extend(cands)
        print(f"Episode {ep['episode']:02d}: found {len(cands)} candidate promos")

    out_file = root / "data/processed/candidate_promos.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_candidates, f, indent=2, ensure_ascii=False)

    print(f"\nTotal candidate promos extracted: {len(all_candidates)}")
    print(f"Saved to: {out_file}")


if __name__ == "__main__":
    main()
