# Science Bowl Trainer Pro — complete VS Code project

Practice with your own Science Bowl question PDFs using an offline/local Streamlit quiz platform. Includes a buzzer, optional spoken questions, word-by-word reader, category/round-format announcements, timed answers, a searchable question bank, bookmarks, and full history and analytics.

**The ZIP contains the code, not your PDF files.** You already have the PDFs, so copy them into `input/` after opening the project. All practice history and imported questions stay on **your own computer**.

## Quick start — Windows + VS Code

1. Right-click the downloaded ZIP and choose **Extract All**. Avoid opening code directly *inside* the ZIP.
2. Open VS Code → **File → Open Folder…** → select the extracted `ScienceBowlTrainer` folder. Verify you can see `app.py` and `input/` in the Explorer sidebar.
3. Put all your science bowl PDFs **inside `input/`**, including any nested year/tournament folders. In VS Code, right-click `input` → **Reveal in File Explorer**, then copy/paste your PDFs. Example: `input/2025 Invitationals/Round 1.pdf`. You can paste the entire archive folder at once.
4. In Windows File Explorer, double-click **`setup_windows.bat`** once. It sets up a local `.venv` Python environment and installs all packages. Alternatively, open the integrated VS Code terminal and run `./setup_windows.bat` (PowerShell) or `setup_windows.bat` (cmd).
5. Double-click **`start_windows.bat`**, or run `./start_windows.bat` in the VS Code terminal. The app should open in your browser at <http://localhost:8501>.
6. In the app sidebar, select **Import local PDFs**, then click **Extract files into question bank**. Wait until the import is complete. Switch to **Question bank** to search or **Practice** to train.

If Windows blocks the `.bat` script, you can run the equivalent commands in the VS Code PowerShell terminal:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The app's import button requires the same Python environment, so install packages first.

## Faster import option (without opening the app)

Double-click **`extract_windows.bat`**, or run:

```powershell
.\.venv\Scripts\python.exe extract_science_bowl.py --input input --output output
```

Then start/reload the trainer. The importer scans all subfolders recursively.

## What gets created

```text
ScienceBowlTrainer/
├── app.py                      # Streamlit app + embedded browser buzzer
├── extract_science_bowl.py     # PDF and DOCX/TXT/MD question extractor
├── requirements.txt           # Dependencies
├── setup_windows.bat           # Initial installation
├── start_windows.bat           # Open the app
├── extract_windows.bat         # Optional direct import
├── input/                      # Your PDFs go here (can have nested folders)
│   └── 2025 Tournament/
│       └── Round 1.pdf
├── output/                     # Generated automatically
│   ├── questions.csv           # Your local question bank
│   ├── questions.json
│   ├── questions_needing_review.csv
│   ├── file_report.csv
│   ├── possible_duplicates.csv
│   └── summary.json
├── practice_progress.json      # Generated after practice
├── practice_history.json       # Detailed attempts; generated automatically
└── practice_bookmarks.json     # Generated as needed
```

The app also has an **optional** DOE importer for official sample questions. The local PDF importer is the one to use for files already downloaded on your computer. The DOE importer writes `output/doe_hs_questions.csv` separately and never replaces `output/questions.csv`.

## Trainer features

- **Buzzer:** Click Buzz or press Space when the reader is focused; reading stops immediately.
- **Introductions:** Subject → pause → TOSSUP/BONUS → pause → MULTIPLE CHOICE/SHORT ANSWER → pause → question.
- **Timers:** Tossups: 5 seconds; bonuses: 20 seconds (when reading ends or when you buzz).
- **Optional voice:** Browser speech synthesis, with available voice selection; audio depends on your browser/OS.
- **Optional reveal:** Toggle question text and reading progress bar independently.
- **Search:** Question Bank searches questions, answers, subjects and source names; filters, bookmarks and practice-from-search.
- **History:** Expandable complete questions/answers, your previous responses, buzz percentage and response time; per-subject statistics and exports.
- **Google search:** Search the full prompt after the question is read, or during review.

## Important: verifying completeness

Science Bowl PDFs differ in layout. The extractor does **not** guarantee that every question was captured correctly. It attempts PDF text extraction (not OCR) and supports common numbered tossup/bonus layouts. Scanned/image-only PDFs, diagrams, multi-column pages, equations, unusual numbering and separate answer keys may need review.

After each import:

1. Open `output/file_report.csv`; look for `error`, `no recognizable questions` or `no extractable text`.
2. Open `output/questions_needing_review.csv`; cross-check answers and diagrams with their source PDFs.
3. Check `output/summary.json` for question counts. Duplicate warnings are in `output/possible_duplicates.csv`.
4. Inspect a few PDFs manually before trusting the database, especially for technical notation and math.

The extractor **replaces** `output/questions.csv` on each local import, but **does not change** your `practice_progress.json` or `practice_history.json`. For stable statistics, keep source filenames and folder layout unchanged between imports because that helps keep extracted question IDs stable.

## Existing data from your older trainer

If you have saved `practice_progress.json`, `practice_history.json`, or `output/questions.csv`, copy them into this project **before practicing**. You can also keep the old CSV without re-importing the PDFs. Do not overwrite your existing progress/history files with blank files; this project intentionally does not include them.

## Common fixes

- **`No supported files found`:** Copy PDFs inside `input`, *not* next to `app.py`, and unzip your downloaded archives first.
- **`No questions loaded`:** Import local PDFs on the app's import page. If importing succeeds but finds zero, inspect `file_report.csv` because your PDF layout may need parser adjustments.
- **`ModuleNotFoundError`:** Run `setup_windows.bat` then start through `start_windows.bat` so both commands use the same Python environment.
- **No voice or Space buzzer:** Use Chrome or Edge, turn on Voice in the player, and click inside the player to capture Space. Browser speech voices vary.
- **Buttons reset after code edits:** Streamlit reloads when files change; avoid modifying `app.py` mid-question.

## macOS or Linux

```bash
bash setup_mac_linux.sh
.venv/bin/python -m streamlit run app.py
```

Then select **Import local PDFs** in the app and use the same `input/` folder.
