# Prompt Engineering Lab - Experiment 9

## Structured JSON Output and Validation

Demonstrates how to prompt an LLM for JSON, validate the result with
`json.loads()`, and retry with a stricter prompt on parse failure.

## Task

Generate a JSON array of 3 books with keys: `title`, `author`, `year`.

## Method

| Stage | What happens |
|-------|--------------|
| 1 | Send JSON prompt with a schema example |
| 2 | Try `json.loads()` on the response |
| 3a | On success - validate required keys and field types |
| 3b | On failure - retry with a stricter prompt (no fences, no prose) |
| 4 | (Optional) Generate the same data as YAML and compare |

## Model and Parameters

- Model: openai/gpt-oss-20b
- Temperature: 0.0 (deterministic)
- Max tokens: 500

## Setup

Reuse the environment from Experiment 1:

    Copy-Item ..\EXP_1\.env .
    python -m pip install -r requirements.txt

Optional - for the YAML section:

    python -m pip install pyyaml

## Run

    python json_output.py

## Expected Output

- JSON prompt, raw response, and parse result
- Schema validation (required keys, correct types)
- Pretty-printed JSON on success
- Stricter retry prompt and second parse attempt on failure
- Optional YAML generation and parsing
- Summary of findings

## Key Findings

1. **JSON prompting usually works** when a schema example is included.

2. **Common JSON pitfalls:**
   - Code fences (` ```json ... ``` `) wrap the output
   - Prose before/after the JSON
   - Single quotes instead of double quotes
   - Trailing commas

3. **Retry strategy** - a stricter prompt fixes most failures:
   - "Output valid JSON only"
   - "Do not use code fences"
   - "Do not write any words before or after the JSON"

4. **Always validate** - never assume the model's JSON is well-formed:
   - `json.loads()` catches syntax errors
   - Schema checks catch missing keys and wrong types
   - Required keys: `title`, `author`, `year`
   - Type check: `year` must be an integer

5. **YAML (optional)** - more human-friendly, more permissive.
   - Use `yaml.safe_load()` (never `yaml.load()`)
   - Good for configs; JSON for APIs and data interchange

## Security

- Never commit .env
- Never paste API keys in chat, logs, or screenshots

## License

For educational / lab use only.
