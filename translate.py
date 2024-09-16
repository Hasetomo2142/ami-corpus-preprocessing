# import os
# import csv
# import networkx as nx
# import matplotlib.pyplot as plt
# from networkx.drawing.nx_agraph import graphviz_layout
# from classes.dialogue_turn import DialogueTurn
# import textwrap  # 改行処理のために使用
# from tqdm import tqdm  # 進捗バーを表示するために使用
# from google.cloud import translate_v2 as translate  # Google Translate API

# # サービスアカウントのキーへのパスを環境変数に設定
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/hasegawa_tomokazu/ami_analysis/august-oarlock-435807-v8-60ebb462199b.json"

# csv_dir = '/home/hasegawa_tomokazu/ami_analysis/CSV'
# output_dir = '/home/hasegawa_tomokazu/ami_analysis/CSV_jp'

# # Google Translate APIを使用して、バッチで翻訳を実行する関数
# def translate_text_batch(texts, target_language="ja", source_language="en"):
#     # クライアントを初期化
#     translate_client = translate.Client()

#     # 翻訳を実行 (複数のテキストを一度に渡す)
#     try:
#         results = translate_client.translate(texts, target_language=target_language, source_language=source_language)
#         return [result['translatedText'] for result in results]
#     except Exception as e:
#         print(f"Error during translation: {e}")
#         return [""] * len(texts)  # エラー時は空の翻訳結果を返す

# # ターゲットのフォーマットを修正する関数
# def format_targets(targets):
#     if not targets or targets == ['NONE']:
#         return 'NONE'
#     else:
#         # 1つの場合でも{}で囲む
#         return '{' + ', '.join(targets) + '}'

# # 実際に翻訳してみる
# if __name__ == "__main__":
#     # 出力ディレクトリが存在しない場合は作成
#     os.makedirs(output_dir, exist_ok=True)
    
#     # CSVディレクトリ内のすべてのCSVファイルを取得
#     csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]

#     all_sentences_len = 0

#     # 進捗バーを表示しながら処理を実行
#     for csv_file in tqdm(csv_files, desc="Processing CSV files"):
#         csv_path = os.path.join(csv_dir, csv_file)
#         dialogue_turns = DialogueTurn.from_csv(csv_path)
        
#         # 翻訳する文をまとめて取得
#         sentences_to_translate = [turn.sentence for turn in dialogue_turns]
#         all_sentences_len += sum(len(sentence) for sentence in sentences_to_translate)

#         # バッチ処理で翻訳
#         batch_size = 100  # バッチサイズを適切に設定
#         translated_sentences = []
#         for i in range(0, len(sentences_to_translate), batch_size):
#             batch = sentences_to_translate[i:i+batch_size]
#             translated_sentences += translate_text_batch(batch, target_language="ja", source_language="en")

#         # 新しいCSVファイル名を作成 (元の名前に "_jp.csv" を付加)
#         output_csv_file = os.path.join(output_dir, csv_file.replace('.csv', '_jp.csv'))
        
#         # 新しいCSVファイルに書き込む
#         with open(output_csv_file, 'w', newline='', encoding='utf-8') as outfile:
#             writer = csv.writer(outfile)
            
#             # ヘッダーを書き込む (元のCSVと同じ形式でヘッダーを保持)
#             writer.writerow(['ae_id', 'speaker', 'start_time', 'end_time', 'sentence', 'source', 'targets'])
            
#             # 翻訳結果を新しいCSVに書き込む
#             for turn, translated_sentence in zip(dialogue_turns, translated_sentences):
#                 formatted_targets = format_targets(turn.targets)  # ターゲットのフォーマットを修正
#                 writer.writerow([turn.ae_id, turn.speaker, turn.start_time, turn.end_time, translated_sentence, turn.source, formatted_targets])

#     print(f'All sentences length: {all_sentences_len}')
