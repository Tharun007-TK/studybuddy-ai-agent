
import os
import asyncio
from google import genai
from dotenv import load_dotenv

# Set dummy key for inspection
os.environ["GOOGLE_API_KEY"] = "dummy"

from google.adk.runners import Runner
import inspect

async def inspect_runner():
    print("Runner init signature:")
    try:
        print(inspect.signature(Runner.__init__))
    except Exception as e:
        print(f"Could not get signature: {e}")
        
    print("Runner attributes:")
    # Create a dummy runner if possible, or just inspect class
    # We need a dummy agent
    from agents import root_agent
    try:
        r = Runner(agent=root_agent, app_name="test")
        for attr in dir(r):
            if not attr.startswith("__"):
                print(attr)
    except Exception as e:
        print(f"Could not instantiate Runner: {e}")

if __name__ == "__main__":
    asyncio.run(inspect_runner())
