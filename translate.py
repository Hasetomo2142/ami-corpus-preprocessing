import os
import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_agraph import graphviz_layout
from classes.dialogue_turn import DialogueTurn
import textwrap  # 改行処理のために使用
from tqdm import tqdm  # 進捗バーを表示するために使用

csv_dir = '/home/hasegawa_tomokazu/ami_analysis/CSV_topics'

# CSVディレクトリ内のすべてのCSVファイルを取得
csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]# CSVディレクトリ内の

all_sentences_len = 0

# 進捗バーを表示しながら処理を実行
for csv_file in tqdm(csv_files, desc="Processing CSV files"):
    csv_path = os.path.join(csv_dir, csv_file)
    dialogue_turns = DialogueTurn.from_csv(csv_path)
    for turn in dialogue_turns:
        size = len(turn.sentence)
        all_sentences_len += size

print(all_sentences_len)

