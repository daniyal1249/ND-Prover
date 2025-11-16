from __future__ import annotations
import os

from flask import Flask, jsonify, render_template, request

from nd_prover import Proof
from nd_prover.cli import logics, parse_and_verify_formula, parse_and_verify_premises
from nd_prover.parser import ParsingError, parse_assumption, parse_line


app = Flask(
    __name__,
    template_folder="site/templates",
    static_folder="site/static",
    static_url_path="/static",
)


def _json_error(message: str, *, status: str = "error", code: int = 400):
    """Return a standardized JSON error response."""
    return jsonify({"ok": False, "status": status, "message": message}), code


def _extract_problem_fields(data):
    """Extract logic label and problem text fields from a JSON payload."""
    logic_name = (data.get("logic") or "").strip()
    premises_text = data.get("premisesText") or ""
    conclusion_text = data.get("conclusionText") or ""
    return logic_name, premises_text, conclusion_text


def _resolve_logic(logic_name):
    """Resolve the logic implementation from its label, or return an error message."""
    logic = logics.get(logic_name)
    if logic is None:
        message = f'Unknown logic: "{logic_name}".'
        return None, message
    return logic, None


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/check-proof")
def check_proof():
    data = request.get_json(silent=True) or {}
    logic_name, premises_text, conclusion_text = _extract_problem_fields(data)
    line_payloads = data.get("lines") or []

    logic, error_message = _resolve_logic(logic_name)
    if logic is None:
        return _json_error(error_message)

    try:
        premises = parse_and_verify_premises(premises_text, logic)
        conclusion = parse_and_verify_formula(conclusion_text, logic)
    except ParsingError as e:
        return _json_error(str(e))

    proof = Proof(logic, premises, conclusion)

    for payload in line_payloads:
        kind = payload.get("kind")
        raw = (payload.get("raw") or "").strip()
        line_no = payload.get("lineNumber")
        formula_text = (payload.get("formulaText") or "").strip()
        just_text = (payload.get("justText") or "").strip()

        prefix = f"Line {line_no}: " if line_no is not None else ""

        # Premises are already encoded in the initial Proof context.
        if kind == "premise":
            continue

        # Assumptions / end-and-begin only carry a formula.
        if kind in {"assumption", "end_and_begin"}:
            if not formula_text:
                message = prefix + "Formula is missing."
                return _json_error(message)
            try:
                assumption = parse_assumption(formula_text)
            except ParsingError as e:
                message = prefix + str(e)
                return _json_error(message)

            if kind == "assumption":
                try:
                    proof.begin_subproof(assumption)
                except Exception as e:
                    message = prefix + str(e)
                    return _json_error(message)
            else:  # end_and_begin
                try:
                    proof.end_and_begin_subproof(assumption)
                except Exception as e:
                    message = prefix + str(e)
                    return _json_error(message)
            continue

        # All other kinds should have both formula and justification.
        if not formula_text:
            message = prefix + "Formula is missing."
            return _json_error(message)

        if not just_text:
            message = prefix + "Justification is missing."
            return _json_error(message)

        # At this point we know both parts are present; raw may still be empty
        # if the serializer was older, so rebuild raw defensively if needed.
        if not raw:
            raw = f"{formula_text}; {just_text}"

        try:
            formula, justification = parse_line(raw)
        except ParsingError as e:
            message = prefix + str(e)
            return _json_error(message)

        try:
            if kind == "line":
                proof.add_line(formula, justification)
            elif kind == "close_subproof":
                proof.end_subproof(formula, justification)
        except Exception as e:
            message = prefix + str(e)
            return _json_error(message)

    is_complete = proof.is_complete()
    if is_complete:
        message = "Proof complete! 🎉"
        status = "complete"
    else:
        message = "No errors yet, but the proof is incomplete!"
        status = "incomplete"

    return jsonify(
        {
            "ok": True,
            "status": status,
            "isComplete": is_complete,
            "message": message,
            "proofString": str(proof),
        }
    )


@app.post("/api/validate-problem")
def validate_problem():
    data = request.get_json(silent=True) or {}

    logic_name, premises_text, conclusion_text = _extract_problem_fields(data)
    logic, error_message = _resolve_logic(logic_name)
    if logic is None:
        return _json_error(error_message)

    # Validate premises and conclusion separately so we can tailor messages.
    try:
        parse_and_verify_premises(premises_text, logic)
    except ParsingError as e:
        message = f"Invalid premise(s): {e}"
        return _json_error(message)

    # Ensure a non-empty conclusion was provided (after premises are checked).
    if not conclusion_text.strip():
        message = "Invalid conclusion: A conclusion must be provided."
        return _json_error(message)

    try:
        parse_and_verify_formula(conclusion_text, logic)
    except ParsingError as e:
        message = f"Invalid conclusion: {e}"
        return _json_error(message)
    except Exception as e:
        # Any unexpected error should still return JSON so the frontend
        # can display a meaningful message instead of a generic fallback.
        return _json_error(str(e))

    return jsonify({"ok": True, "status": "ok", "message": ""})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
