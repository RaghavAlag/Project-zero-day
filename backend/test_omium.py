import os
from dotenv import load_dotenv
import omium
import time

load_dotenv()

api_key = os.getenv("OMIUM_API_KEY")
print(f"Using API Key: {api_key[:10]}...")

try:
    omium.init(api_key=api_key, project="project-zero-day")
    print("Init successful")

    @omium.trace(name="Test Trace")
    def test_func():
        print("Executing test function...")
        time.sleep(1)
        return "success"

    result = test_func()
    print(f"Result: {result}")
    
    # Give it time to send
    time.sleep(5)
    print("Done")
except Exception as e:
    print(f"Error: {e}")
