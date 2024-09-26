from openai import OpenAI

def get_chat_response(prompt):
    client = OpenAI()

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return completion.choices[0].message.content

# 使用例
system_prompt = "You are a helpful assistant."
prompt = "こんにちは"
response = get_chat_response(prompt)
print(response)
