import os
from dotenv import load_dotenv
import cohere

load_dotenv()

co = cohere.Client(os.getenv("COHERE_API_KEY"))

response = co.chat(
    model="command-a-03-2025",
    message="Say hello in one short sentence",
    max_tokens=20
)

print(response.text)
