import subprocess
import xml.etree.ElementTree as ET
import datetime as dt
import glob
import sys
import re
import os
import csv
from collections import defaultdict, deque
import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_agraph import graphviz_layout

# 自作クラスのインポート
from classes.meeting import Meeting
from classes.dialogue_turn import DialogueTurn

# グラフの初期化
Graph = nx.DiGraph()

# ファイルのパス
dir_path = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(dir_path, 'CSV_topics')

# CSVディレクトリからすべてのCSVファイルを取得
csv_files = glob.glob(os.path.join(csv_path, '*.csv'))
print(f"Processing CSV file: {csv_files[0]}")

dialogue_turns = DialogueTurn.from_csv(csv_files[0])

# ae_idをキー、DialogueTurnオブジェクトを値とする辞書を作成
dialogue_dict = {dt.ae_id: dt for dt in dialogue_turns}

# 'ROOT' ノードを追加
Graph.add_node('ROOT', label='ROOT', speaker='ROOT', depth=0)

# ソースが 'ROOT' のノードをキューに追加
queue = deque()
visited = set()

for dt in dialogue_turns:
    if dt.source == 'ROOT':
        # ノードを追加
        Graph.add_node(dt.ae_id, label=dt.sentence, speaker=dt.speaker, depth=1)
        # 'ROOT' からのエッジを追加
        Graph.add_edge('ROOT', dt.ae_id)
        # キューに追加
        queue.append((dt.ae_id, 1))  # (ae_id, 深さ)
        visited.add(dt.ae_id)

# 幅優先探索でグラフを構築し、深さを記録
while queue:
    current_ae_id, depth = queue.popleft()
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
                    Graph.add_node(target_ae_id, label=target_dt.sentence, speaker=target_dt.speaker, depth=depth + 1)
                else:
                    # ターゲットがdialogue_turnsに存在しない場合
                    Graph.add_node(target_ae_id, label='[Unknown]', speaker='Unknown', depth=depth + 1)
                queue.append((target_ae_id, depth + 1))
                visited.add(target_ae_id)
            # エッジを追加
            Graph.add_edge(current_ae_id, target_ae_id)

# グラフの描画と保存
plt.figure(figsize=(12, 8))

# レイアウトの設定（深さ順で表示するためにgraphvizのdotを使用）
pos = graphviz_layout(Graph, prog='dot')

# ノードラベルを取得
labels = nx.get_node_attributes(Graph, 'label')

# ノードの色を話者ごとに分ける
speakers = list(set([data['speaker'] for node, data in Graph.nodes(data=True)]))
color_map = {speaker: idx for idx, speaker in enumerate(speakers)}
node_colors = [color_map[data['speaker']] for node, data in Graph.nodes(data=True)]

# 四角形ノードの描画
for node, (x, y) in pos.items():
    plt.text(x, y, s=labels[node], bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.5'), 
            horizontalalignment='center', fontsize=8)

# エッジの描画
nx.draw_networkx_edges(Graph, pos, arrows=True)

plt.axis('off')
plt.tight_layout()

# グラフをPNGで保存
output_image_path = os.path.join(dir_path, 'graph.png')
plt.savefig(output_image_path, format='png', dpi=300)
plt.show()

print(f"Graph saved as {output_image_path}")
