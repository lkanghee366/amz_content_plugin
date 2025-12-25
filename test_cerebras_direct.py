import os
from dotenv import load_dotenv
from cerebras.cloud.sdk import Cerebras

load_dotenv()

# Load API keys from file
api_keys_file = 'cerebras_api_keys.txt'
with open(api_keys_file, 'r') as f:
    api_keys = [line.strip() for line in f if line.strip() and not line.startswith('#')]

print(f"Loaded {len(api_keys)} API keys")

# Use first key
api_key = api_keys[0]
print(f"Using key: ...{api_key[-4:]}")

client = Cerebras(api_key=api_key)

# Test keyword
test_keyword = "wine cooler ge"

# Prompt
prompt = f"""Classify this keyword: '{test_keyword}'
Return ONLY 1, 2, or 3:
1 = REVIEW (buying intent: 'best laptop', 'wine cooler fridge', 'samsung vs lg')
2 = INFO (learning intent: 'how to', 'what is', 'recipe', 'guide')
3 = SKIP (sensitive/wrong geo/nonsense)

Output only the number: 1, 2, or 3"""

print("\n" + "="*60)
print("PROMPT:")
print("="*60)
print(prompt)
print("="*60)

print("\nCalling Cerebras API (zai-glm-4.6)...\n")

# Non-streaming version with system message
response = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are a classifier. Output ONLY the number 1, 2, or 3. No explanation, no reasoning, just the number."
        },
        {
            "role": "user",
            "content": prompt
        }
    ],
    model="zai-glm-4.6",
    stream=False,
    max_completion_tokens=100,
    temperature=0.6,
    top_p=0.95
)

print("="*60)
print("RESPONSE (Non-streaming):")
print("="*60)
print(f"Full response object type: {type(response)}")
print(f"Choices: {len(response.choices)}")
if response.choices:
    message = response.choices[0].message
    print(f"Message content: {message.content}")
    print(f"Has reasoning attr: {hasattr(message, 'reasoning')}")
    if hasattr(message, 'reasoning'):
        print(f"Reasoning: {message.reasoning}")
print("="*60)

# Now test streaming
print("\n" + "="*60)
print("RESPONSE (Streaming):")
print("="*60)

stream = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are a classifier. Output ONLY the number 1, 2, or 3. No explanation, no reasoning, just the number."
        },
        {
            "role": "user",
            "content": prompt
        }
    ],
    model="zai-glm-4.6",
    stream=True,
    max_completion_tokens=10,
    temperature=0.1
)

full_content = ""
for chunk in stream:
    if chunk.choices and len(chunk.choices) > 0:
        delta = chunk.choices[0].delta
        if hasattr(delta, 'content') and delta.content:
            content = delta.content
            print(content, end="", flush=True)
            full_content += content

print("\n" + "="*60)
print(f"Full streamed content: '{full_content}'")
print("="*60)
