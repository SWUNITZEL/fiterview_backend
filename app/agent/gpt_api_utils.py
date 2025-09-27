import os
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("OPENAI_MODEL")
TEMPERATURE = float(os.getenv("TEMPERATURE"))

client = OpenAI(api_key=API_KEY)

def load_prompt(file_path, **kwargs):
    with open(file_path, "r", encoding="utf-8") as f:
        template = f.read()
    return template.format(**kwargs)

def call_gpt(system_prompt, user_prompt, temperature=TEMPERATURE):
    response = client.responses.create(
        model=MODEL_NAME,
        input=[
            {
                "role": "system",
                "content": [
                    {
                    "type": "input_text",
                    "text": system_prompt
                    }
                ]
                },
                {
                "role": "user",
                "content": [
                    {
                    "type": "input_text",
                    "text": user_prompt
                    }
                ]
            }    
        ],
        temperature=temperature,
        top_p=0.8,
        reasoning={},
        text={},
        store=False,
        max_output_tokens=4096
    )
    return response.output_text
