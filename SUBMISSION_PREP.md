# 📋 KUKU AI Generalist Assignment — Submission Cheat Sheet

This guide provides everything needed to fill out and submit the official Kuku submission form.

---

## 1. Candidate Details & Form Fields

| Form Field | Suggested Entry |
| :--- | :--- |
| **Full Name** | *[Your Full Name]* |
| **Roll Number** | *[Your College Roll Number]* |
| **Branch / Degree** | *[e.g., Computer Science / Electrical / AI & Data Science]* |
| **Problem Chosen** | **Problem 1: Find the Promos (Ads)** |
| **Solution Doc Link / File** | Upload or link `solution_doc/Kuku_AI_Generalist_Solution_Doc.pdf` *(Strictly 2 pages)* |
| **Prototype Link** | GitHub repository link *(see 2-minute push steps below)* or Streamlit Cloud URL |
| **Raw Outputs Folder Link** | Google Drive / GitHub folder link to `raw_outputs/` |
| **Walkthrough Video Link** | *(Optional, recommended)* Loom / Google Drive link (3-minute screen recording) |

---

## 2. Pushing the Repository to GitHub (2-Minute Steps)

1. Open your browser and create a new repository on [GitHub](https://github.com/new):
   - Repository Name: `kuku-promo-finder`
   - Set to **Public** (so the Kuku review team can open it without permission walls).
   - Leave "Initialize with README" unchecked.

2. Run these commands in your terminal:
   ```bash
   cd "/Users/nikhilbhaskar/Desktop/KUKU Deck/kuku-promo_finder-g"
   git remote add origin https://github.com/YOUR_USERNAME/kuku-promo-finder.git
   git branch -M main
   git push -u origin main
   ```

3. Paste your new GitHub repo URL into the **Prototype Link** field!

---

## 3. Quick Reference for Interview Questions

If shortlisted, Kuku reviewers will interview you on your decisions. Here are concise, confident answers:

### Q1: "Why did you build a hybrid engine instead of just asking Gemini / GPT-4 for everything?"
> *"Microdrama studios release multiple shows a week. Running 500+ sliding windows through a paid LLM API costs ~$7.50 per show, exhausts rate limits, and is slow. By building a deterministic Tier-1 screenplay parser and dramatic beat extractor, we process the entire 50-episode show in 2.93 seconds at $0.00 compute cost, while reserving swappable LLM hooks for high-tier synthesis and editorial enrichment."*

### Q2: "Which promo would you post first on TikTok/Reels, and why?"
> *"Rank #1 from Episode 2 (00:00–00:27). When a cold user clicks a social media ad, they install the app and enter Episode 1. Showing the inciting altar betrayal provides 100% narrative onboarding continuity. Exposing later episodes causes confusion and user drop-off. Later episodes (like Episode 45's identity unmasking) are reserved for mid-funnel retargeting and coin unlocks."*

### Q3: "Where does your tool pick badly?"
> *"Our automated audit of 878 candidate windows revealed 4 systematic failure modes:*
> 1. *Camera-heavy openings (453 instances): Screenplays with 4-second slow pans fail on mobile feeds unless dialogue begins within 1.5 seconds.*
> 2. *Lore-heavy context (96 instances): Shouting matches between secondary characters that lack core archetype clarity.*
> 3. *Grammatically closed cuts (215 instances): Statements ending on complete periods provide closure rather than open curiosity.*
> 4. *Sarcasm ambiguity: Sarcastic lines that appear polite unless actor direction tags (e.g. `(Mocking, Venomous)`) are parsed into the conflict matrix."*

### Q4: "Can you run this on a brand new show we give you right now?"
> *"Yes. We built a dedicated episode importer module (`python src/importer.py --input <file_or_zip> --run-pipeline`) and a drag-and-drop web uploader in the Streamlit app. It validates timestamps, parses scenes, and re-ranks candidate promos in under 3 seconds."*

---

## 4. 3-Minute Walkthrough Video Script

Follow this script if recording a video via Loom or phone screen recording:

1. **[0:00 - 0:35] Problem Framing:**
   - Introduce yourself and Problem 1.
   - Explain that microdrama platforms scale through paid user acquisition on TikTok and Reels, where editors spend 15–20 hours a week clipping episodes manually.
2. **[0:35 - 1:15] Technical Architecture:**
   - Highlight the Two-Tier Hybrid Architecture (Screenplay NLP + Swappable AI Engine).
   - Show terminal running `python src/pipeline.py` and finishing in ~2.9 seconds.
3. **[1:15 - 2:05] Interactive Studio Demo:**
   - Open Streamlit Studio (`http://localhost:8501`).
   - Showcase the 9:16 Mobile Feed Simulator showing Rank #1 from Episode 2.
   - Show the new **"📥 Import New Episodes"** tab and demonstrate how new scripts can be uploaded and re-ranked instantly.
4. **[2:05 - 2:40] Quality Checking & Failure Modes:**
   - Show the Quality Audit tab and explain the 4 systematic failure modes (camera pans, lore dependency, soft cuts).
5. **[2:40 - 3:00] Wrap-up:**
   - Mention the 2-page PDF solution doc and the full unedited outputs in `raw_outputs/`.
