
import os
import groq
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

try:
    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful college student support assistant."
            },
            {
                "role": "user",
                "content": "Explain how a student can check their fee status in two simple sentences."
            }
        ],
        max_tokens=150
    )

    print("\nSUCCESS! Groq AI is responding.")
    print("\nAI Response:")
    print(response.choices[0].message.content)

except groq.APIStatusError as error:
    print("API error status:", error.status_code)
    print("Error details:", str(error))

except groq.APIConnectionError:
    print("Connection failed. Please check your internet.")

except Exception as error:
    print("Error type:", type(error).__name__)
    print("Details:", str(error))
