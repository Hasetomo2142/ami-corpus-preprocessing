import subprocess
import xml.etree.ElementTree as ET
import datetime as dt
import glob
import sys
import re
import os
import csv
from collections import defaultdict, deque  # dequeを追加
import networkx as nx
import matplotlib.pyplot as plt

# 自作クラスのインポート
from classes.meeting import Meeting
from classes.dialogue_turn import DialogueTurn

# グラフの初期化
Graph = nx.DiGraph()

# ファイルのパス
dir_path = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(dir_path, 'CSV')

# CSVディレクトリからすべてのCSVファイルを取得
csv_files = glob.glob(os.path.join(csv_path, '*.csv'))
print(f"Processing CSV file: {csv_files[0]}")

dialogue_turns = DialogueTurn.from_csv(csv_files[0])

# ae_idをキー、DialogueTurnオブジェクトを値とする辞書を作成
dialogue_dict = {dt.ae_id: dt for dt in dialogue_turns}

# 'ROOT' ノードを追加
Graph.add_node('ROOT', label='ROOT', speaker='ROOT')

# ソースが 'ROOT' のノードをキューに追加
queue = deque()
visited = set()

for dt in dialogue_turns:
    if dt.source == 'ROOT':
        # ノードを追加
        Graph.add_node(dt.ae_id, label=dt.sentence, speaker=dt.speaker)
        # 'ROOT' からのエッジを追加
        Graph.add_edge('ROOT', dt.ae_id)
        # キューに追加
        queue.append(dt.ae_id)
        visited.add(dt.ae_id)

# 幅優先探索でグラフを構築
while queue:
    current_ae_id = queue.popleft()
    current_dt = dialogue_dict.get(current_ae_id)
    if not current_dt:
        continue  # 対応するDialogueTurnが存在しない場合はスキップ

    # ターゲットを取得
    for target_ae_id in current_dt.targets:
        if target_ae_id and target_ae_id != 'None':
            # ターゲットノードを追加（未訪問の場合）
            if target_ae_id not in visited:
                target_dt = dialogue_dict.get(target_ae_id)
                if target_dt:
                    Graph.add_node(target_ae_id, label=target_dt.sentence, speaker=target_dt.speaker)
                else:
                    # ターゲットがdialogue_turnsに存在しない場合
                    Graph.add_node(target_ae_id, label='[Unknown]', speaker='Unknown')
                queue.append(target_ae_id)
                visited.add(target_ae_id)
            # エッジを追加
            Graph.add_edge(current_ae_id, target_ae_id)

# グラフの描画と保存
plt.figure(figsize=(12, 8))

# レイアウトの設定
pos = nx.spring_layout(Graph, k=0.5, seed=42)

# ノードラベルを取得
labels = nx.get_node_attributes(Graph, 'label')

# ノードの色を話者ごとに分ける
speakers = list(set([data['speaker'] for node, data in Graph.nodes(data=True)]))
color_map = {speaker: idx for idx, speaker in enumerate(speakers)}
node_colors = [color_map[data['speaker']] for node, data in Graph.nodes(data=True)]

# グラフを描画
nx.draw_networkx_nodes(Graph, pos, node_color=node_colors, cmap=plt.cm.Set1, node_size=500)
nx.draw_networkx_edges(Graph, pos, arrows=True)
nx.draw_networkx_labels(Graph, pos, labels, font_size=8)

plt.axis('off')
plt.tight_layout()

# グラフをPNGで保存
output_image_path = os.path.join(dir_path, 'graph.png')
plt.savefig(output_image_path, format='png', dpi=300)
plt.show()

print(f"Graph saved as {output_image_path}")
