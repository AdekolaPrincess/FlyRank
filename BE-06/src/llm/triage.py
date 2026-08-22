import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime, timezone


load_dotenv()

llm_client = OpenAI(
    base_url=os.environ["LLM_BASE_URL"],
    api_key=os.environ["LLM_API_KEY"],
)

def load_prompt(filename: str) -> str:
    """Reads a prompt file from the prompts/ folder and returns its text."""
    with open(f"prompts/{filename}", "r", encoding="utf-8") as f:
        return f.read()

TRIAGE_PROMPT = load_prompt("triage-v1.md")

def run_triage(text: str) -> str:
    """Sends the support message to the model and returns its raw reply text."""
    response = llm_client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        temperature=0.2,
        messages=[
            {"role": "system", "content": TRIAGE_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    return response.choices[0].message.content


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