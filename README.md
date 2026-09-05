# CodeLint — Python Code Review Tool

A rule-based static code analyzer that detects common Python anti-patterns, security risks, and PEP8 violations — built without relying on any external AI API.

## Overview

CodeLint scans submitted Python code using a mix of line-based checks and AST (Abstract Syntax Tree) analysis, flagging issues across six categories: security, best practice, style, documentation, code quality, and maintenance. Each issue carries a severity level (error, warning, info), and the full result is boiled down into a single 0–100 code quality score.

## Features

- **Security checks** — dangerous use of `eval()` / `exec()`, `subprocess` imports and calls
- **Best practice checks** — bare `except:` blocks, mutable default arguments, leftover `print()` statements, wildcard imports
- **Style checks** — line length (PEP8), tabs vs. spaces, trailing whitespace, non-snake_case variable naming
- **Documentation checks** — missing function docstrings
- **Code quality checks** — functions with too many parameters (>5), functions over 50 lines
- **Maintenance checks** — unresolved `TODO` / `FIXME` comments
- **Syntax checks** — reports parse errors with line and column when the code doesn't parse at all
- **Duplicate suppression** — identical findings on the same line are collapsed to one
- **Quality score** — starts at 100, −10 per error, −5 per warning, −1 per info, floored at 0
- **Severity-based summary** — issues grouped and counted as errors, warnings, and info

## Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript (vanilla, no frameworks) — editor-style input with live line numbers, findings shown as inline margin annotations
- **Logic:** Python's built-in `ast` module for structural analysis, plus regex/line-based checks for formatting — no external AI/ML dependency

## Project Structure

```
codelint/
├── app.py                 # Flask backend + analysis engine
├── templates/
│   └── index.html         # Frontend UI
└── README.md
```

## How It Works

```
User pastes Python code in browser
            │
            ▼
   Frontend sends code via fetch() to /review
            │
            ▼
   Flask backend runs analyze_code()
            │
            ▼
   Line-based rules scan raw source (length, whitespace, tabs, TODOs)
   AST rules walk the parsed tree (functions, calls, imports, except blocks, assigns)
            │
            ▼
   Duplicates removed, issues sorted by line, score calculated
            │
            ▼
   JSON response: { issues, summary }
            │
            ▼
   Frontend renders findings + tally by severity
```

## System Architecture

![CodeLint system architecture](architecture.svg)

The browser only ever talks to two routes — `GET /` for the page shell, and `POST /review` for analysis. Everything else (source-line checks, AST traversal, dedupe, scoring) runs inside a single Flask process per request; there's no database, queue, or external service in the loop.

## Setup & Run Locally

```bash
# clone the repo
git clone https://github.com/YOUR_USERNAME/codelint.git
cd codelint

# create a virtual environment
python -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate

# install dependencies
pip install flask

# run the app
python app.py
```

Visit `http://localhost:5000` in your browser.

## Example

Input:
```python
def calculate_total(items=[]):
    try:
        result = eval(items[0])
    except:
        pass
    print(result)
    return result
```

Output flags:
- Mutable default argument (`items=[]`) — warning, Best Practice
- Use of `eval()` — error, Security
- Bare `except:` — error, Best Practice
- `print()` statement — info, Best Practice
- Missing docstring on `calculate_total` — info, Documentation

Resulting quality score: `100 − 10 (error) − 10 (error) − 5 (warning) − 1 (info) − 1 (info) = 73`

## Future Improvements

- [ ] Add support for JavaScript code review
- [ ] Integrate an optional AI-powered review mode (LLM-based suggestions)
- [ ] Add a downloadable report (PDF/JSON export)
- [ ] Syntax highlighting in the code input panel
- [ ] Surface the quality score in the frontend UI (currently computed but not yet displayed)

## License

MIT
