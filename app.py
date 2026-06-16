from flask import Flask, render_template, request, jsonify
import re

app = Flask(__name__)


def analyze_code(code):
    """
    Rule-based Python code reviewer.
    Returns a list of issues found in the submitted code.
    """
    issues = []
    lines = code.split("\n")

    # ---------- Rule 1: Line length check ----------
    for i, line in enumerate(lines, start=1):
        if len(line) > 79:
            issues.append({
                "line": i,
                "severity": "warning",
                "message": f"Line too long ({len(line)} chars). PEP8 recommends max 79.",
                "category": "Style"
            })

    # ---------- Rule 2: Trailing whitespace ----------
    for i, line in enumerate(lines, start=1):
        if line != line.rstrip() and line.strip() != "":
            issues.append({
                "line": i,
                "severity": "info",
                "message": "Trailing whitespace found.",
                "category": "Style"
            })

    # ---------- Rule 3: Tabs vs spaces ----------
    for i, line in enumerate(lines, start=1):
        if "\t" in line:
            issues.append({
                "line": i,
                "severity": "warning",
                "message": "Tab character used for indentation. Use spaces instead (PEP8).",
                "category": "Style"
            })

    # ---------- Rule 4: Bare except ----------
    for i, line in enumerate(lines, start=1):
        if re.search(r"except\s*:", line):
            issues.append({
                "line": i,
                "severity": "error",
                "message": "Bare 'except:' catches all exceptions, including system ones. Specify exception type.",
                "category": "Best Practice"
            })

    # ---------- Rule 5: Use of eval/exec ----------
    for i, line in enumerate(lines, start=1):
        if re.search(r"\b(eval|exec)\s*\(", line):
            issues.append({
                "line": i,
                "severity": "error",
                "message": "Use of eval()/exec() is a security risk. Avoid unless absolutely necessary.",
                "category": "Security"
            })

    # ---------- Rule 6: Mutable default argument ----------
    for i, line in enumerate(lines, start=1):
        if re.search(r"def\s+\w+\(.*=\s*(\[\]|\{\})", line):
            issues.append({
                "line": i,
                "severity": "warning",
                "message": "Mutable default argument (list/dict) detected. Can cause unexpected bugs.",
                "category": "Best Practice"
            })

    # ---------- Rule 7: Variable naming convention ----------
    for i, line in enumerate(lines, start=1):
        match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*[^=]", line)
        if match:
            var_name = match.group(1)
            if re.match(r"^[A-Z]", var_name) and not var_name.isupper():
                issues.append({
                    "line": i,
                    "severity": "info",
                    "message": f"Variable '{var_name}' should be snake_case, not CamelCase (PEP8).",
                    "category": "Style"
                })

    # ---------- Rule 8: Missing docstring on functions ----------
    for i, line in enumerate(lines):
        if re.match(r"\s*def\s+\w+\(.*\):", line):
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if not (next_line.startswith('"""') or next_line.startswith("'''")):
                issues.append({
                    "line": i + 1,
                    "severity": "info",
                    "message": "Function is missing a docstring.",
                    "category": "Documentation"
                })

    # ---------- Rule 9: TODO / FIXME comments ----------
    for i, line in enumerate(lines, start=1):
        if re.search(r"#.*\b(TODO|FIXME)\b", line, re.IGNORECASE):
            issues.append({
                "line": i,
                "severity": "info",
                "message": "Unresolved TODO/FIXME comment found.",
                "category": "Maintenance"
            })

    # ---------- Rule 10: print() left in code (debugging leftover) ----------
    for i, line in enumerate(lines, start=1):
        if re.search(r"\bprint\s*\(", line):
            issues.append({
                "line": i,
                "severity": "info",
                "message": "print() statement found — consider using logging for production code.",
                "category": "Best Practice"
            })

    return issues


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/review", methods=["POST"])
def review():
    data = request.get_json()
    code = data.get("code", "")

    if not code.strip():
        return jsonify({"issues": [], "summary": "No code provided."})

    issues = analyze_code(code)

    # Build a summary
    error_count = sum(1 for i in issues if i["severity"] == "error")
    warning_count = sum(1 for i in issues if i["severity"] == "warning")
    info_count = sum(1 for i in issues if i["severity"] == "info")

    summary = {
        "total": len(issues),
        "errors": error_count,
        "warnings": warning_count,
        "info": info_count
    }

    return jsonify({"issues": issues, "summary": summary})


if __name__ == "__main__":
    app.run(debug=True)
