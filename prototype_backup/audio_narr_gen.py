import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from text_to_speech import save

load_dotenv()

with open('data/exps.json', 'r') as f:
    exps = json.load(f)

for key, exp in exps.items():
    script = (exp['narration_script'])
    language = "en"
    audio_loc = exp["audio_loc"]
    print(f"{exp['narration_script']}")
    print(f"Generating audio for {exp['apparatus']}...")
    save(script,language, file = audio_loc)
