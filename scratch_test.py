import os
import sys

# Clear API keys to force local model or demo fallback
if "GEMINI_API_KEY" in os.environ:
    del os.environ["GEMINI_API_KEY"]
if "GOOGLE_API_KEY" in os.environ:
    del os.environ["GOOGLE_API_KEY"]

# Make sure we import explanation_module after setting the env
import explanation_module

print("Running explanation module without API keys for 'photosynthesis'...")
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

