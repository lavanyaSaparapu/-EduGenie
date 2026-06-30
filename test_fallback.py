import os
import sys

# Import first, which triggers load_dotenv()
import explanation_module

# Now clear the environment variables to simulate no API key
if "GEMINI_API_KEY" in os.environ:
    del os.environ["GEMINI_API_KEY"]
if "GOOGLE_API_KEY" in os.environ:
    del os.environ["GOOGLE_API_KEY"]

print("Running explanation module without API keys for 'photosynthesis' (demo topic)...")
try:
    res, model_used = explanation_module.explain_topic("photosynthesis")
    print("Model Used:", model_used)
    print("Result:")
    print(res.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8'))
except Exception as e:
    print("Exception occurred:")
    import traceback
    traceback.print_exc()

print("\nRunning explanation module without API keys for a non-demo topic 'quantum entanglement'...")
try:
    res, model_used = explanation_module.explain_topic("quantum entanglement")
    print("Model Used:", model_used)
    print("Result:")
    print(res.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8'))
except Exception as e:
    print("Exception occurred:")
    import traceback
    traceback.print_exc()
