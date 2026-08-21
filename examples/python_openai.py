"""OmniRouter — Python OpenAI SDK examples"""
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:8787/v1", api_key="anything")

# router-auto — smart free-first failover
resp = client.chat.completions.create(
    model="router-auto",
    messages=[{"role": "user", "content": "Say hi in 3 words"}],
)
print("router-auto:", resp.choices[0].message.content)
print("via:", resp.headers.get("x-router-provider") if hasattr(resp, "headers") else "see X-Router-Provider header")

# router-code — best free coder
resp = client.chat.completions.create(
    model="router-code",
    messages=[{"role": "user", "content": "Write a python function to reverse a string. Only code."}],
)
print("\nrouter-code:", resp.choices[0].message.content[:200])

# streaming
print("\nstreaming (router-fast):")
stream = client.chat.completions.create(
    model="router-fast",
    messages=[{"role": "user", "content": "Count 1 to 5."}],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print()
