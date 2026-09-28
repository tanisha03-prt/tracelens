import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("OPENAI_API_KEY is not set")

client = OpenAI(api_key=api_key)


def ask_llm(prompt: str):
    response = client.responses.create(
        model="gpt-5.6-luna",
        input=prompt
    )

    return response.output_text


if __name__ == "__main__":
    print("OpenAI client configured successfully")

    answer = ask_llm("Say hello in one short sentence.")
    print(answer)
    