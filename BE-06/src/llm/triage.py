import os
from dotenv import load_dotenv
from openai import OpenAI

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