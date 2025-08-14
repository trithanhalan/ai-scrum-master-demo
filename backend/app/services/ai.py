from openai import OpenAI
from app.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def summarize_list(markdown_list: str) -> str:
    prompt = f"""
Summarize the following Jira issues into stand-up style points:

{markdown_list}

Format:
- Yesterday: ...
- Today: ...
- Blockers: ...
"""
    chat = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )
    return chat.choices[0].message.content.strip()