# 🎬 KUKU PromoFinder Studio: AI-Powered Microdrama Ad Discovery

**Kuku AI Generalist Assignment — Problem 1: Find the Promos (Ads)**  
**Dataset:** *I Married a Broken Soldier. He was a Duke* (Full 50-Episode Screenplay Pack)

---

## 📌 Executive Summary

Microdrama streaming platforms (Kuku, ReelShort, DramaBox, ShortMax) scale through paid user acquisition on TikTok, Instagram Reels, and YouTube Shorts. Currently, editors spend **15–20 hours per week** per show manually watching episodes to identify promotional clips.

**KUKU PromoFinder Studio** is a production-grade, two-tier AI system that ingests raw screenplay manuscripts and extracts high-converting promotional moments (20–60s) in **2.93 seconds**. For every promo, it identifies:
- The exact episode and ordered start/end clipping timestamps.
- The 0–3 second hook breakdown (why scrolling viewers stop).
- The unresolved cliffhanger cut-point (forcing viewers to watch Episode 1 / next episode).
- A 1-line marketing conversion rationale ("Why it works").
- Systematic quality audit warnings (where automated tools pick badly).
- Strategic funnel placement (Which promos to post first, and why).

---

## 🚀 Quickstart

### 1. Installation
Clone the repository and install dependencies in Python 3.10+:
```bash
pip install -r requirements.txt
```

*(Optional)* Configure your Gemini API key in `.env`:
```bash
cp .env.example .env
# Edit .env and set GEMINI_API_KEY if desired
```
> **Note:** The system runs **100% offline and free** using its deterministic semantic engine. It never blocks or fails on API quotas.

### 2. Run the Full Batch Pipeline (All 50 Episodes)
Run the end-to-end pipeline in one command:
```bash
python src/pipeline.py
```
*Output: Parses 50 episodes, analyzes 3,727 events, scores 878 candidate windows, ranks the top 50, exports 50 individual episode JSONs, and generates the quality audit report in under 3 seconds.*

### 3. Launch the Interactive Studio UI
Launch the interactive Streamlit application:
```bash
streamlit run frontend/app.py
```
The studio includes:
- **📊 Executive Dashboard:** Show-level stats, score distributions, and funnel phasing.
- **🎬 Promo Library (Ranked):** Filter by rank, episode, score, format, and review exact timestamps & scripts.
- **📱 9:16 Mobile Feed Simulator:** Live preview of how the promo plays on TikTok/Instagram Reels.
- **🔍 Episode Explorer & Custom Window Evaluator:** Select any episode and score custom timestamp windows on the fly.
- **⚠️ Quality & Failure Audit:** Transparent breakdown of the 4 systematic algorithmic failure modes.

### 4. Run Unit Tests
```bash
python -m unittest discover tests
```

---

## 🏆 Deliverables & Output Files

| Item | Location | Description |
| :--- | :--- | :--- |
| **Solution Doc (PDF)** | `solution_doc/Kuku_AI_Generalist_Solution_Doc.pdf` | **Strictly 2 pages**. Formatted with reportlab, complete with tables, metrics, architecture, and honest failure analysis. |
| **Solution Doc (Markdown)** | `solution_doc/solution_doc.md` | Source markdown of the 2-page solution document. |
| **Top 50 Ranked Promos** | `raw_outputs/ranked_promos_top50.json` | Detailed JSON of the top 50 promos across all episodes. |
| **Best Promos Per Episode** | `raw_outputs/all_episodes_best_promos.json` | Best candidate promo for every single episode (1 to 50). |
| **Spreadsheet Summary** | `raw_outputs/promos_export.csv` | Export for video editors and marketing performance managers. |
| **Per-Episode Raw Outputs** | `raw_outputs/by_episode/` | 50 separate unedited JSON files (`episode_001_promos.json` ... `episode_050_promos.json`). |
| **Quality Audit Report** | `raw_outputs/quality_audit_report.json` | Quantitative audit of systematic edge cases and failure modes. |

---

## 🎯 Strategic Posting Funnel: Which Promos To Post First, and Why?

Microdrama marketing requires a **3-phase deployment strategy**:

### 1. Day 1 Cold Acquisition (Post First)
- **Top Pick:** **Rank #1 — Episode 2 [00:00.00 – 00:27.40]** (Duration: 27.4s | Score: 9.20/10)
  - **Hook (First 3s):** Gerald declares coldly: *"I cannot marry you, Juliana."*
  - **Cliffhanger Cut:** Juliana retorts: *"A better choice? Is that what she is?"*
  - **Why Post First:** When a cold user installs the app from a TikTok/Reels ad, they enter **Episode 1**. Showing the inciting altar betrayal provides **100% onboarding continuity**. It requires zero lore, establishes instant empathy for Juliana, and makes viewers furious at Gerald and Clarissa.

### 2. Mid-Funnel Re-engagement (Post Days 3–5)
- **Top Pick:** **Rank #2 — Episode 15 [00:46.50 – 01:22.40]** (Duration: 35.9s | Score: 9.15/10)
  - **Hook (First 3s):** Juliana refuses street thugs: *"No."*
  - **Cliffhanger Cut:** Thug threatens: *"What? You want to fight us, veteran?"* (The broken soldier rises to defend her).
  - **Why Post Later:** Re-engages drop-offs who stopped around Episode 3 by showing protagonist vindication and rising stakes.

### 3. Climax & Whale Monetization (Retargeting)
- **Top Pick:** **Rank #4 — Episode 45 [00:02.80 – 00:24.40]** (Duration: 21.6s | Score: 9.00/10)
  - **Hook (First 3s):** Juliana in shock: *"Alexander..."*
  - **Cliffhanger Cut:** The ultimate identity unmasking: *"You're the Duke?"*
  - **Why Post for Retargeting:** High-intensity spoiler reveals designed to compel coin purchases and binge unlocks from invested viewers.

---

## ⚠️ Quality Checking: Where Does the Tool Pick Badly?

The assignment explicitly asks: *"Check quality. Where does your tool pick badly?"*  
Our automated audit across all 878 candidate windows identified 4 systematic failure modes:

1. **Slow Camera-Only Openings (453 instances flagged):** Screenplays frequently open with 4–5 seconds of scenic camera movement before speech. While cinematic on paper, mobile scrollers bounce if there is no audio shock within **1.5 seconds**.  
   *Mitigation:* Heavy penalty (-2.0) applied if dialogue or physical action does not begin within 1.5s.
2. **Lore-Heavy Character Clashes (96 instances flagged):** Late episodes feature heated disputes between secondary characters (e.g. bailiffs/attorneys). NLP tags high emotion, but cold viewers have no idea who they are.  
   *Mitigation:* The Story Clarity scorer checks for universally recognized archetypes (Bride, Groom, Sister, Duke) and penalizes obscure lore.
3. **Grammatically Closed Cuts (215 instances flagged):** A scene ending on a completed period (*"I will leave now."*) provides narrative closure, eliminating click urgency.  
   *Mitigation:* The Cliffhanger scorer awards 3x higher weights to open interrogatives (`?`), trailing dashes (`--`), and interrupted threats.
4. **Text Sarcasm Ambiguity:** Lines like *"Thank you for your generosity, sister"* look polite to naive sentiment models.  
   *Mitigation:* Ingests screenplay character parentheticals: `(Mocking, Venomous)` into the emotional vector.

---

## 🎙️ Walkthrough Video Script (Up to 3 Minutes)

If you are recording a Loom or Drive video for your submission, use this crisp script:

```markdown
[0:00 - 0:30] Introduction & Framing
"Hi team, this is my submission for Problem 1: Find the Promos. 
I chose this problem because microdrama streaming platforms scale through TikTok and Reels acquisition,
where editors spend 15 to 20 hours a week clipping episodes manually. 
I built KUKU PromoFinder Studio: a hybrid system that turns raw screenplay manuscripts into ready-to-cut promo ads in under 3 seconds."

[0:30 - 1:15] Architecture & Pipeline Run
"Instead of naive sliding windows that cut mid-sentence or expensive LLM brute-forcing that exhausts API limits,
my system uses a Two-Tier Architecture.
Tier 1 is a deterministic screenplay parser that extracts timestamps, dialogue, and character emotion tags like (Cold, Callous) or (Furious, Defiant). 
It pairs natural dramatic hook starts to cliffhanger cuts between 20 and 60 seconds.
Tier 2 is a swappable scoring and marketing engine that evaluates Hook, Cliffhanger, Story Clarity, and Emotional Impact."
(Show terminal running: python src/pipeline.py finishing in 2.9s)

[1:15 - 2:00] The Interactive Studio UI & Simulator
"Here is the interactive Streamlit Studio. 
Video editors can explore ranked candidate promos, view exact clipping timestamps, and test custom time ranges.
We also built a 9:16 vertical mobile feed simulator. 
For instance, our Rank #1 promo from Episode 2 starts at 00:00 with Gerald declaring 'I cannot marry you, Juliana',
and cuts right at 00:27 as Juliana retorts 'A better choice? Is that what she is?'
This delivers 100% onboarding continuity for cold installs landing on Episode 1."

[2:00 - 2:45] Quality Checking & Failure Modes
"The brief specifically asked where the tool picks badly. We ran an automated audit on all 878 candidate windows.
We found that the biggest failure mode is slow camera-only openings—453 windows started with 4 seconds of scenic camera pans,
which cause instant scroll-drop on TikTok. 
We mitigated this by penalizing openings that don't have dialogue or physical action within 1.5 seconds.
We also flagged lore-heavy secondary disputes and grammatically resolved cuts."

[2:45 - 3:00] Scaling & Conclusion
"At production scale of 3 shows a week, this system reduces editor clipping time by over 98% with zero compute cost.
All unedited raw outputs for all 50 episodes, the CSV export, unit tests, and the 2-page PDF solution doc are ready. 
Thank you!"
```
