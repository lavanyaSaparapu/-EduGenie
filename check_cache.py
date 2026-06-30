import os
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_name = "MBZUAI/LaMini-Flan-T5-783M"
print("Checking if local model is cached...")
try:
    tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name, local_files_only=True)
    print("Local model is cached and loaded successfully!")
except Exception as e:
    print("Local model is NOT cached or failed to load:", e)
