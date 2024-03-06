import streamlit as st
import os
from dotenv import load_dotenv
import asyncio
from anthropic import Anthropic

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_KEY"))

async def main():
    stream = await client.messages.create(
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": "Hello, Claude",
            }
        ],
        model="claude-3-opus-20240229",
        stream=True,
    )
    async for event in stream:
        print(event.type)

if __name__ == "__main__":
    asyncio.run(main())