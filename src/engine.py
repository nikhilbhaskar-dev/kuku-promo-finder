import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from dotenv import load_dotenv
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

ROOT = Path(__file__).resolve().parent.parent


class PromoEngine:
    """
    Hybrid AI engine supporting:
    - Built-in High-Precision Semantic Reasoning Engine (offline, deterministic, fast, zero cost)
    - Google Gemini API (when valid key with available quota is provided)
    - Graceful fallback: Never crashes if API rate limit or quota occurs.
    """

    def __init__(self, mode: str = "auto", api_key: Optional[str] = None, model: str = "gemini-3.8-flash"):
        self.mode = mode
        self.model_name = model
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None

        if HAS_GENAI and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[Warning] Could not initialize Gemini Client: {e}")
                self.client = None

    def evaluate_with_llm(self, promo: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call Gemini to evaluate and enrich a promo candidate."""
        if not self.client:
            return None

        script_text = "\n".join(
            f"[{e['start']:.1f}s - {e['end']:.1f}s] {e['type']}" +
            (f" ({e['speaker']}): " if e.get('speaker') else ": ") +
            e['content']
            for e in promo.get("events_summary", [])
        )

        prompt = f"""
You are an expert short-form drama promo editor and growth marketer for vertical apps (ReelShort, DramaBox, KUKU).

Evaluate this candidate promo from Episode {promo['episode']}.
Duration: {promo['total_duration']:.1f} seconds.

PROMO SCRIPT:
{script_text}

Task:
1. Evaluate Hook Strength (1-10): Does the first 3 seconds stop mobile feed scrolling?
2. Evaluate Cliffhanger Strength (1-10): Does the cut-point leave maximum unresolved curiosity?
3. Evaluate Story Clarity (1-10): Can someone who has never seen the show understand the core conflict?
4. Evaluate Emotional Impact (1-10): Conflict density and vocal/physical intensity.
5. Provide a crisp 1-sentence Hook description.
6. Provide a crisp 1-sentence Cliffhanger description.
7. Provide a crisp 1-line 'Why it works' marketing rationale.
8. Identify honest weaknesses (e.g. slow opening shot, obscure lore).
9. Select posting category: "Day 1 Cold Acquisition", "Mid-Funnel Re-engagement", or "Late Retargeting".
10. Verdict: "SELECT" or "REJECT".

Return valid JSON with exactly these keys:
{{
  "hook_strength": <int 1-10>,
  "cliffhanger_strength": <int 1-10>,
  "story_clarity": <int 1-10>,
  "emotional_impact": <int 1-10>,
  "hook": "<string>",
  "cliffhanger": "<string>",
  "why_it_works": "<string>",
  "weaknesses": "<string>",
  "posting_category": "<string>",
  "verdict": "<SELECT|REJECT>"
}}
"""
        for attempt in range(1, 3):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        "http_options": {"timeout": 30000}
                    }
                )
                if response.text:
                    res_json = json.loads(response.text)
                    return res_json
            except Exception as e:
                # If quota exhausted (429) or other API issue, log and fallback
                print(f"[Engine] LLM call failed (attempt {attempt}): {e}")
                time.sleep(2)

        return None

    def enrich_candidate(self, cand: Dict[str, Any], use_llm: bool = False) -> Dict[str, Any]:
        """Enriches candidate promo with scores, marketing rationale, and posting category."""
        if use_llm and self.client:
            llm_result = self.evaluate_with_llm(cand)
            if llm_result:
                # Merge LLM results
                cand["hook_strength"] = float(llm_result.get("hook_strength", cand["hook_strength"]))
                cand["cliffhanger_strength"] = float(llm_result.get("cliffhanger_strength", cand["cliffhanger_strength"]))
                cand["story_clarity"] = float(llm_result.get("story_clarity", cand["story_clarity"]))
                cand["emotional_impact"] = float(llm_result.get("emotional_impact", cand["emotional_impact"]))
                cand["hook"] = llm_result.get("hook", cand["hook"])
                cand["cliffhanger"] = llm_result.get("cliffhanger", cand["cliffhanger"])
                cand["why_it_works"] = llm_result.get("why_it_works", cand["why_it_works"])
                cand["weaknesses"] = llm_result.get("weaknesses", cand["weaknesses"])
                cand["posting_category"] = llm_result.get("posting_category", self.determine_posting_category(cand))
                cand["verdict"] = llm_result.get("verdict", cand["verdict"])
                cand["engine_source"] = f"Gemini ({self.model_name})"
                return cand

        # Fallback to Built-in Semantic Reasoning Engine
        cand["posting_category"] = self.determine_posting_category(cand)
        cand["engine_source"] = "Deterministic Semantic Engine"
        return cand

    @staticmethod
    def determine_posting_category(cand: Dict[str, Any]) -> str:
        ep = cand["episode"]
        if ep <= 2:
            return "Day 1 Cold Acquisition (Launch Phase)"
        elif ep <= 10:
            return "Mid-Funnel Retargeting & Protagonist Vindication"
        else:
            return "High-Tension Episodic Climax / Whale Conversion"
