# CodeLint — Python Code Review Tool

A rule-based static code analyzer that detects common Python anti-patterns, security risks, and PEP8 violations — built without relying on any external AI API.

## Overview

CodeLint scans submitted Python code line by line and flags issues across four categories: security, best practices, style, and documentation. Each issue is tagged with a severity level (error, warning, info) so the most critical problems stand out first.

## Features

- **Security checks** — flags dangerous use of `eval()` / `exec()`
- **Best practice checks** — bare `except:` blocks, mutable default arguments, leftover `print()` statements
- **Style checks** — line length (PEP8), tabs vs spaces, trailing whitespace, naming conventions
- **Documentation checks** — missing docstrings, unresolved `TODO` / `FIXME` comments
- **Severity-based summary** — issues grouped into errors, warnings, and info

## Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript (vanilla, no frameworks)
- **Logic:** Regex-based pattern matching, no external AI/ML dependency

## Project Structure

```
CODEMINT/
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
   Regex rules scan each line for issues
            │
            ▼
   JSON response: { issues, summary }
            │
            ▼
   Frontend renders categorized results
```

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

Output includes flags for: mutable default argument, use of `eval()`, bare `except:`, leftover `print()`, and missing docstring.

## Future Improvements

- [ ] Add support for JavaScript code review
- [ ] Integrate an optional AI-powered review mode (LLM-based suggestions)
- [ ] Add a downloadable report (PDF/JSON export)
- [ ] Syntax highlighting in the code input panel

## License

MIT
