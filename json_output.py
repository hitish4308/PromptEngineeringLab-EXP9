"""
Experiment 9 - Structured JSON Output and Validation

Task: Ask the LLM to produce a JSON array of 3 books with keys
      title, author, year. Validate the JSON and required keys.
      On parse failure, retry with a stricter prompt.
      Optional: also generate YAML and compare.
"""

import os
import json
import textwrap
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Optional YAML support - install pyyaml if you want to run this
try:
    import yaml
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False

# ---------- Setup ----------
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.environ.get("NVIDIA_API_KEY")
if not api_key:
    raise SystemExit("NVIDIA_API_KEY not found. Create a .env file.")

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=api_key,
)

MODEL = "openai/gpt-oss-20b"
TEMPERATURE = 0.0
MAX_TOKENS = 500


# ---------- Prompts ----------
JSON_PROMPT = (
    "Generate a JSON array of 3 books. Each object must have keys: "
    "title, author, year. "
    "Output only valid JSON with no explanations, no markdown, no extra text.\n\n"
    "Example format:\n"
    '[\n  {"title": "Book Title", "author": "Author Name", "year": 2000}\n]'
)

JSON_STRICTER_PROMPT = (
    "Output valid JSON only. Do not include explanations, markdown, or extra text.\n"
    "Do not use code fences. Do not write any words before or after the JSON.\n\n"
    "Generate a JSON array of exactly 3 book objects with keys: title, author, year."
)

YAML_PROMPT = (
    "Generate a YAML document describing 3 books. Each book must have keys: "
    "title, author, year. Output only the YAML, no explanations and no markdown fences."
)


# ---------- Helpers ----------
def ask_llm(prompt: str) -> str:
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        content = resp.choices[0].message.content
        return (content or "").strip()
    except Exception as e:
        return f"[API error] {type(e).__name__}: {e}"


def strip_code_fences(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` fences if present."""
    t = text.strip()
    if t.startswith("```"):
        # drop first line
        t = t.split("\n", 1)[1] if "\n" in t else t
        # drop trailing fence
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()


def try_parse_json(text: str):
    """Return (parsed, error_message). parsed is None on failure."""
    cleaned = strip_code_fences(text)
    try:
        return json.loads(cleaned), None
    except json.JSONDecodeError as e:
        return None, f"{e.__class__.__name__}: {e}"


def validate_books(data) -> list:
    """Check schema of the parsed data. Returns list of issues."""
    issues = []
    if not isinstance(data, list):
        issues.append("Top-level value is not a JSON array.")
        return issues
    if len(data) != 3:
        issues.append(f"Expected 3 books, got {len(data)}.")
    for i, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            issues.append(f"Item {i} is not an object.")
            continue
        for key in ("title", "author", "year"):
            if key not in item:
                issues.append(f"Item {i} missing key '{key}'.")
        if "year" in item and not isinstance(item["year"], int):
            issues.append(f"Item {i} 'year' is not an integer.")
    return issues


def show_block(label: str, prompt: str, response: str):
    width = 72
    print("=" * width)
    print(f"  {label}")
    print("=" * width)
    print("PROMPT:")
    print(textwrap.indent(prompt, "  "))
    print()
    print("RESPONSE:")
    print(textwrap.indent(response, "  "))
    print()


# ---------- Main ----------
if __name__ == "__main__":
    print(f"Model: {MODEL}")
    print(f"Temperature: {TEMPERATURE} | Max tokens: {MAX_TOKENS}")

    # ---------- JSON attempt 1 ----------
    print("\n>>> Sending JSON prompt (attempt 1)...")
    raw1 = ask_llm(JSON_PROMPT)
    show_block("JSON PROMPT (attempt 1)", JSON_PROMPT, raw1)

    parsed, err = try_parse_json(raw1)
    if parsed is not None:
        print("PARSE RESULT: SUCCESS")
        print(f"  {len(parsed)} object(s) parsed.")
        issues = validate_books(parsed)
        if issues:
            print("  Schema issues:")
            for issue in issues:
                print(f"    - {issue}")
        else:
            print("  Schema: OK (all objects have title, author, year).")
        print("\n  Pretty-printed JSON:")
        print(textwrap.indent(json.dumps(parsed, indent=2), "    "))
    else:
        print(f"PARSE RESULT: FAILED - {err}")
        print("  Retrying with stricter prompt...\n")

        raw2 = ask_llm(JSON_STRICTER_PROMPT)
        show_block("JSON PROMPT (attempt 2 - stricter)", JSON_STRICTER_PROMPT, raw2)
        parsed, err = try_parse_json(raw2)
        if parsed is not None:
            print("PARSE RESULT: SUCCESS (after retry)")
            print(f"  {len(parsed)} object(s) parsed.")
            issues = validate_books(parsed)
            if issues:
                print("  Schema issues:")
                for issue in issues:
                    print(f"    - {issue}")
            else:
                print("  Schema: OK.")
            print("\n  Pretty-printed JSON:")
            print(textwrap.indent(json.dumps(parsed, indent=2), "    "))
        else:
            print(f"PARSE RESULT: FAILED again - {err}")

    # ---------- Optional YAML ----------
    if HAVE_YAML:
        print("\n>>> Sending YAML prompt...")
        raw_y = ask_llm(YAML_PROMPT)
        show_block("YAML PROMPT", YAML_PROMPT, raw_y)
        try:
            data = yaml.safe_load(strip_code_fences(raw_y))
            print("YAML PARSE: SUCCESS")
            print(textwrap.indent(yaml.safe_dump(data, sort_keys=False), "  "))
        except Exception as e:
            print(f"YAML PARSE: FAILED - {type(e).__name__}: {e}")
    else:
        print("\n(Skipping YAML — run:  python -m pip install pyyaml  to enable.)")

    # ---------- Summary ----------
    print("\n" + "=" * 72)
    print("  SUMMARY")
    print("=" * 72)
    print("""
Findings:

1. JSON PROMPTING
   - Asking for JSON with a schema example usually works
   - Models sometimes wrap output in ```json ... ``` fences - strip
     these before parsing, or ask for "no markdown" explicitly
   - Always validate: json.loads() + a schema check for required keys

2. RETRY STRATEGY
   - If the first parse fails, a stricter prompt often succeeds:
       * "Output valid JSON only"
       * "Do not use code fences"
       * "Do not write any words before or after the JSON"
   - Keeping the same model and temperature ensures the retry is
     a fair comparison

3. VALIDATION CHECKLIST (what to always verify)
   - Parses with json.loads() without exceptions
   - Top-level type matches the expected shape (list, dict, etc.)
   - Every object contains the required keys
   - Field types are correct (year is int, not string, etc.)
   - No trailing commas, double quotes only

4. YAML (OPTIONAL)
   - YAML is more permissive (no strict quotes, allows comments)
   - Machine parsing uses yaml.safe_load() - never yaml.load()
   - YAML is human-friendly; JSON is machine-friendly
   - Many APIs accept both; pick based on downstream consumer
""")
