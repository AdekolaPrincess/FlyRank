import os
import json
import re
import time
import random
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIStatusError, APITimeoutError
from datetime import datetime, timezone


load_dotenv()

llm_client = OpenAI(
    base_url=os.environ["LLM_BASE_URL"],
    api_key=os.environ["LLM_API_KEY"],
    timeout = 30.0,
    max_retries = 0
)

def load_prompt(filename: str) -> str:
    """Reads a prompt file from the prompts/ folder and returns its text."""
    with open(f"prompts/{filename}", "r", encoding="utf-8") as f:
        return f.read()

TRIAGE_PROMPT = load_prompt("triage-v1.md")

def run_triage(text: str):
    """Sends the support message to the model and returns the full response object."""
    return llm_client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        temperature=0.2,
        messages=[
            {"role": "system", "content": TRIAGE_PROMPT},
            {"role": "user", "content": text},
        ],
    )


def parse_model_output(raw_text: str) -> dict:
    """Strips code fences/extra text and parses the model's reply as JSON.
    Raises json.JSONDecodeError if it still isn't valid JSON."""
    cleaned = raw_text.strip()
    # Remove markdown code fences like ```json ... ``` or ``` ... ```
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.MULTILINE)
    # Find the first { ... last } in case there's extra text around it
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1:
        cleaned = cleaned[start:end + 1]
    return json.loads(cleaned)

def repair_triage(text: str, broken_output: str, error_message: str) -> str:
    """Sends the model its own broken answer plus the validation error, asking for a fix."""
    response = llm_client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        temperature=0.2,
        messages=[
            {"role": "system", "content": TRIAGE_PROMPT},
            {"role": "user", "content": text},
            {"role": "assistant", "content": broken_output},
            {"role": "user", "content": f"Your previous answer was rejected for this reason: {error_message}. Return only corrected JSON matching the schema."},
        ],
    )
    return response.choices[0].message.content

from datetime import datetime, timezone

def log_quarantine(input_text: str, raw_output: str, error: str, prompt_version: str = "triage-v1"):
    """Appends a record of a failed (unrepairable) model output to logs/quarantine.jsonl"""
    os.makedirs("logs", exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_version": prompt_version,
        "input": input_text,
        "raw_output": raw_output,
        "error": error,
    }
    with open("logs/quarantine.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def run_triage_with_retry(text: str, max_attempts: int = 3) -> str:
    """Calls run_triage, retrying on timeouts, 429s, and 5xx errors only.
    Never retries on 400/401/403 - those won't fix themselves."""
    for attempt in range(max_attempts):
        try:
            return run_triage(text)
        except (RateLimitError, APITimeoutError) as e:
            if attempt == max_attempts - 1:
                raise
            wait = (2 ** attempt) + random.uniform(0, 1)
            print(f"Retryable error ({type(e).__name__}), waiting {wait:.1f}s before retry {attempt + 1}/{max_attempts - 1}")
            time.sleep(wait)
        except APIStatusError as e:
            if e.status_code >= 500 and attempt < max_attempts - 1:
                wait = (2 ** attempt) + random.uniform(0, 1)
                print(f"Server error {e.status_code}, waiting {wait:.1f}s before retry {attempt + 1}/{max_attempts - 1}")
                time.sleep(wait)
            else:
                raise

def log_cost(prompt_version: str, model: str, usage, duration_ms: float, repaired: bool):
    """Writes one structured log line per AI call - what it cost, how long it took."""
    log_line = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_version": prompt_version,
        "model": model,
        "input_tokens": usage.prompt_tokens if usage else None,
        "output_tokens": usage.completion_tokens if usage else None,
        "duration_ms": round(duration_ms, 1),
        "repaired": repaired,
    }
    print("COST LOG:", json.dumps(log_line))