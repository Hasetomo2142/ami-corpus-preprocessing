import csv
import os
import sys
import openai

openai.api_key = 'your-api-key'

# 自作クラスのインポート
from classes.meeting import Meeting
from classes.dialogue_turn import DialogueTurn

# ファイルのパス
dir_path = os.path.dirname(os.path.abspath(__file__))
ami_corpus_path = os.path.join(dir_path, 'ami_public_manual_1.6.2')
csv_topics_path = os.path.join(dir_path, 'CSV_topics')
manifest_path = os.path.join(ami_corpus_path, 'MANIFEST_MANUAL.txt')

# csv_topics_path内のすべてのCSVファイルのパスを取得
def get_csv_files(csv_topics_path):
    csv_files = [f for f in os.listdir(csv_topics_path) if f.endswith('.csv')]
    return [os.path.join(csv_topics_path, csv_file) for csv_file in csv_files]

# プロンプト生成
def generate_prompt(current_utterance, previous_utterances):
    previous_utterance_pairs = "\n".join([f"AE_ID {turn.ae_id}: \"{turn.sentence}\"" for turn in previous_utterances])
    
    prompt = f"""Please analyze the following dialogue turn and determine which past turns influenced it, if any.

Current turn AE_ID {current_utterance.ae_id}: 
"{current_utterance.sentence}"

Past dialogue turns:
{previous_utterance_pairs}

If none of the past turns influenced the current turn, respond with 'NONE'. Otherwise, respond with only the AE_ID of the turns that influenced the current turn. Do not include any explanations or additional information.
"""
    return prompt




# GPT-4oのモックメソッド
def mock_gpt4o_api(prompt):
    # Simulate the decision-making process of the model
    # For demonstration, let's randomly choose to return an AE_ID or "NONE"
    import random
    choices = ["AE_ID 123", "AE_ID 456", "NONE"]
    selected_choice = random.choice(choices)
    
    # Return a JSON-like dictionary response
    return {"result": selected_choice}

def call_gpt4o_mini(prompt):
    try:
        # Adjust the model name as needed; as of now, 'gpt-4o-mini' is hypothetical and may not exist.
        # Check OpenAI's documentation for the correct model identifier.
        response = openai.Completion.create(
            model="text-davinci-003",  # Use the appropriate model identifier
            prompt=prompt,
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.7
        )
        return response.choices[0].text.strip()
    except Exception as e:
        print("An error occurred:", e)
        return None
    
# プロンプトの長さを保持するリスト
prompt_lengths = []

def store_prompt_length(prompt):
    length = len(prompt)
    prompt_lengths.append(length)
    return length

# コストを概算する関数
def calculate_cost(prompt_lengths):
    tokens_per_char = 0.25  # 仮のトークン数
    cost_per_token = 0.00000015
    total_tokens = sum([length * tokens_per_char for length in prompt_lengths])
    total_cost = total_tokens * cost_per_token
    return total_cost

# メイン処理
def main():
    csv_file_list = get_csv_files(csv_topics_path)
    print (csv_file_list[0])
    
    for csv_file in csv_file_list:
        dialogue_turns = DialogueTurn.from_csv(csv_file)
        for index, turn in enumerate(dialogue_turns):
            if index > 0:
                # 前の5個（またはそれ以下）のturn（ae_idとsentenceのペア）を取得
                start_index = max(0, index - 5)
                previous_utterances = dialogue_turns[start_index:index]
            else:
                previous_utterances = []

            # プロンプト生成
            prompt = generate_prompt(turn, previous_utterances)
            
            # GPT-4oモックAPIに送信
            result = mock_gpt4o_api(prompt)
            relationship_exists = DialogueTurn.relationship_exists(dialogue_turns,turn.ae_id, result)
            print('---------------------------------')
            print('source:',index,turn.ae_id)
            print(result)
            print(relationship_exists)
            print(prompt)
            print('---------------------------------')
            
            # プロンプトの長さを保持
            prompt_length = store_prompt_length(prompt)
            
        break

    # コストを概算
    total_cost = calculate_cost(prompt_lengths)
    print(f"Estimated cost: ${total_cost:.5f}")


        
if __name__ == '__main__':
    main()
    