from flask import Flask, render_template, request, jsonify
import ast
import re

app = Flask(__name__)


# ============================================================
# ISSUE HELPER
# ============================================================

def add_issue(
    issues,
    line,
    severity,
    message,
    category,
    rule
):
    issues.append({
        "line": line or 1,
        "severity": severity,
        "message": message,
        "category": category,
        "rule": rule
    })


# ============================================================
# SOURCE-BASED RULES
# ============================================================

def check_source_rules(code, issues):

    lines = code.splitlines()

    # --------------------------------------------------------
    # Rule 1: Line too long
    # --------------------------------------------------------

    for line_no, line in enumerate(lines, start=1):

        if len(line) > 79:
            add_issue(
                issues,
                line_no,
                "warning",
                f"Line too long ({len(line)} chars). "
                "PEP8 recommends a maximum of 79 characters.",
                "Style",
                "line-too-long"
            )

    # --------------------------------------------------------
    # Rule 2: Trailing whitespace
    # --------------------------------------------------------

    for line_no, line in enumerate(lines, start=1):

        if line != line.rstrip():
            add_issue(
                issues,
                line_no,
                "info",
                "Trailing whitespace found.",
                "Style",
                "trailing-whitespace"
            )

    # --------------------------------------------------------
    # Rule 3: Tabs
    # --------------------------------------------------------

    for line_no, line in enumerate(lines, start=1):

        if "\t" in line:
            add_issue(
                issues,
                line_no,
                "warning",
                "Tab character detected. Use spaces for indentation.",
                "Style",
                "tabs"
            )

    # --------------------------------------------------------
    # Rule 4: TODO / FIXME
    # --------------------------------------------------------

    for line_no, line in enumerate(lines, start=1):

        if re.search(
            r"#.*\b(TODO|FIXME)\b",
            line,
            re.IGNORECASE
        ):
            add_issue(
                issues,
                line_no,
                "info",
                "Unresolved TODO/FIXME comment found.",
                "Maintenance",
                "todo-fixme"
            )


# ============================================================
# AST VISITOR
# ============================================================

class CodeLintVisitor(ast.NodeVisitor):

    def __init__(self, issues):

        self.issues = issues

    # ========================================================
    # FUNCTION RULES
    # ========================================================

    def visit_FunctionDef(self, node):

        self.check_function(node)

        self.generic_visit(node)

    # Also analyze async functions
    def visit_AsyncFunctionDef(self, node):

        self.check_function(node)

        self.generic_visit(node)

    def check_function(self, node):

        # ----------------------------------------------------
        # Rule: Missing docstring
        # ----------------------------------------------------

        if ast.get_docstring(node) is None:

            add_issue(
                self.issues,
                node.lineno,
                "info",
                f"Function '{node.name}' is missing a docstring.",
                "Documentation",
                "missing-docstring"
            )

        # ----------------------------------------------------
        # Rule: Too many arguments
        # ----------------------------------------------------

        arguments = (
            node.args.posonlyargs
            + node.args.args
            + node.args.kwonlyargs
        )

        if node.args.vararg:
            arguments.append(node.args.vararg)

        if node.args.kwarg:
            arguments.append(node.args.kwarg)

        if len(arguments) > 5:

            add_issue(
                self.issues,
                node.lineno,
                "warning",
                f"Function '{node.name}' has "
                f"{len(arguments)} parameters. "
                "Consider reducing its complexity.",
                "Code Quality",
                "too-many-arguments"
            )

        # ----------------------------------------------------
        # Rule: Mutable default arguments
        # ----------------------------------------------------

        defaults = list(node.args.defaults)

        defaults += [
            default
            for default in node.args.kw_defaults
            if default is not None
        ]

        for default in defaults:

            if isinstance(
                default,
                (ast.List, ast.Dict, ast.Set)
            ):

                add_issue(
                    self.issues,
                    getattr(default, "lineno", node.lineno),
                    "warning",
                    "Mutable default argument detected. "
                    "Use None and initialize it inside the function.",
                    "Best Practice",
                    "mutable-default"
                )

        # ----------------------------------------------------
        # Rule: Long function
        # ----------------------------------------------------

        if hasattr(node, "end_lineno") and node.end_lineno:

            function_length = (
                node.end_lineno - node.lineno + 1
            )

            if function_length > 50:

                add_issue(
                    self.issues,
                    node.lineno,
                    "warning",
                    f"Function '{node.name}' is "
                    f"{function_length} lines long. "
                    "Consider breaking it into smaller functions.",
                    "Code Quality",
                    "long-function"
                )


    # ========================================================
    # CALL RULES
    # ========================================================

    def visit_Call(self, node):

        # ----------------------------------------------------
        # Rule: eval / exec
        # ----------------------------------------------------

        if isinstance(node.func, ast.Name):

            function_name = node.func.id

            if function_name in {"eval", "exec"}:

                add_issue(
                    self.issues,
                    node.lineno,
                    "error",
                    f"Use of {function_name}() is a potential "
                    "security risk.",
                    "Security",
                    f"dangerous-{function_name}"
                )

            # ------------------------------------------------
            # Rule: print
            # ------------------------------------------------

            if function_name == "print":

                add_issue(
                    self.issues,
                    node.lineno,
                    "info",
                    "print() statement found. "
                    "Consider using logging in production code.",
                    "Best Practice",
                    "print-statement"
                )

        # ----------------------------------------------------
        # Rule: subprocess.call / run / Popen
        # ----------------------------------------------------

        if isinstance(node.func, ast.Attribute):

            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "subprocess"
            ):

                add_issue(
                    self.issues,
                    node.lineno,
                    "warning",
                    f"subprocess.{node.func.attr}() detected. "
                    "Review external command execution carefully.",
                    "Security",
                    "subprocess-call"
                )

        self.generic_visit(node)


    # ========================================================
    # EXCEPTION RULES
    # ========================================================

    def visit_ExceptHandler(self, node):

        # ----------------------------------------------------
        # Rule: Bare except
        # ----------------------------------------------------

        if node.type is None:

            add_issue(
                self.issues,
                node.lineno,
                "error",
                "Bare 'except:' catches all exceptions. "
                "Specify an exception type.",
                "Best Practice",
                "bare-except"
            )

        self.generic_visit(node)


    # ========================================================
    # IMPORT RULES
    # ========================================================

    def visit_ImportFrom(self, node):

        # ----------------------------------------------------
        # Rule: Wildcard import
        # ----------------------------------------------------

        for alias in node.names:

            if alias.name == "*":

                add_issue(
                    self.issues,
                    node.lineno,
                    "warning",
                    "Wildcard import detected. "
                    "Import specific names instead.",
                    "Best Practice",
                    "wildcard-import"
                )

        self.generic_visit(node)


    # ========================================================
    # IMPORT RULES
    # ========================================================

    def visit_Import(self, node):

        for alias in node.names:

            if alias.name == "subprocess":

                add_issue(
                    self.issues,
                    node.lineno,
                    "warning",
                    "subprocess module imported. "
                    "Review external command execution carefully.",
                    "Security",
                    "subprocess-import"
                )

        self.generic_visit(node)


    # ========================================================
    # VARIABLE NAMING
    # ========================================================

    def visit_Assign(self, node):

        for target in node.targets:

            if isinstance(target, ast.Name):

                name = target.id

                # Ignore private variables and constants
                if (
                    name
                    and name[0].isupper()
                    and not name.isupper()
                ):

                    add_issue(
                        self.issues,
                        node.lineno,
                        "info",
                        f"Variable '{name}' should use snake_case.",
                        "Style",
                        "variable-naming"
                    )

        self.generic_visit(node)


# ============================================================
# AST ANALYZER
# ============================================================

def check_ast_rules(code, issues):

    try:

        tree = ast.parse(code)

    except SyntaxError as error:

        line = error.lineno or 1

        message = error.msg

        if error.offset:
            message += f" (column {error.offset})"

        add_issue(
            issues,
            line,
            "error",
            f"Syntax error: {message}",
            "Syntax",
            "syntax-error"
        )

        return False

    visitor = CodeLintVisitor(issues)

    visitor.visit(tree)

    return True


# ============================================================
# DUPLICATE REMOVAL
# ============================================================

def remove_duplicate_issues(issues):

    seen = set()
    unique = []

    for issue in issues:

        key = (
            issue["line"],
            issue["rule"],
            issue["message"]
        )

        if key not in seen:

            seen.add(key)
            unique.append(issue)

    return unique


# ============================================================
# CODE QUALITY SCORE
# ============================================================

def calculate_score(issues):

    score = 100

    for issue in issues:

        if issue["severity"] == "error":
            score -= 10

        elif issue["severity"] == "warning":
            score -= 5

        elif issue["severity"] == "info":
            score -= 1

    return max(0, score)


# ============================================================
# MAIN ANALYZER
# ============================================================

def analyze_code(code):

    issues = []

    # Source-level checks
    check_source_rules(code, issues)

    # AST-level checks
    check_ast_rules(code, issues)

    # Remove duplicate findings
    issues = remove_duplicate_issues(issues)

    # Sort by line number
    issues.sort(
        key=lambda issue: (
            issue["line"],
            issue["severity"]
        )
    )

    return issues


# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def home():

    return render_template("index.html")


@app.route("/review", methods=["POST"])
def review():

    # --------------------------------------------------------
    # Validate JSON
    # --------------------------------------------------------

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "error": "Invalid JSON request."
        }), 400

    # --------------------------------------------------------
    # Get source code
    # --------------------------------------------------------

    code = data.get("code", "")

    if not isinstance(code, str):

        return jsonify({
            "error": "Code must be provided as a string."
        }), 400

    if not code.strip():

        return jsonify({
            "issues": [],
            "summary": {
                "total": 0,
                "errors": 0,
                "warnings": 0,
                "info": 0,
                "score": 100
            }
        })

    # --------------------------------------------------------
    # Analyze
    # --------------------------------------------------------

    issues = analyze_code(code)

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    error_count = sum(
        1
        for issue in issues
        if issue["severity"] == "error"
    )

    warning_count = sum(
        1
        for issue in issues
        if issue["severity"] == "warning"
    )

    info_count = sum(
        1
        for issue in issues
        if issue["severity"] == "info"
    )

    score = calculate_score(issues)

    summary = {
        "total": len(issues),
        "errors": error_count,
        "warnings": warning_count,
        "info": info_count,
        "score": score
    }

    return jsonify({
        "issues": issues,
        "summary": summary
    })


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
