from groq import AsyncGroq
import os
import asyncio
import json

async def call_groq(messages, json_mode=False):
    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    retries = 3
    delay = 2
    
    for attempt in range(retries):
        try:
            await asyncio.sleep(2) # Enforced delay to respect rate limits
            kwargs = {
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "temperature": 0.2
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
                
            response = await client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            print(f"Groq error (attempt {attempt+1}): {str(e)}")
            if attempt == retries - 1:
                # Fallback model
                try:
                    kwargs["model"] = "llama-3.1-8b-instant"
                    response = await client.chat.completions.create(**kwargs)
                    return response.choices[0].message.content
                except Exception as fallback_e:
                    print(f"Groq fallback error: {str(fallback_e)}")
                    raise fallback_e
            await asyncio.sleep(delay)
            delay *= 2
