"""
examples/quickstart_gemini.py

Minimal standalone example of the exact google-genai call pattern
this project's core/brain.py builds on:

    import google.genai as g
    obj = g.Client(api_key=key)
    response = obj.models.generate_content(
        model='gemini-3-flash-preview',
        contents='Explain quantum computing'
    )
    print(response.text)

Run:
    export GEMINI_API_KEY=your_key_here
    python examples/quickstart_gemini.py
"""

import os
import google.genai as g

key = os.getenv("GEMINI_API_KEY")
if not key:
    raise SystemExit("Set the GEMINI_API_KEY environment variable first.")

obj = g.Client(api_key=key)
response = obj.models.generate_content(
    model='gemini-3-flash-preview',
    contents='Explain quantum computing'
)
print(response.text)
