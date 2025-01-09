from openai import OpenAI

client = OpenAI(
  api_key="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"
)

completion = client.chat.completions.create(
  model="gpt-4o-mini",
  store=True,
  messages=[
    {"role": "user", "content": "write a haiku about tree"}
  ]
)

print(completion.choices[0].message);
