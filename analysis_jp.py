import os
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import font_manager
from networkx.drawing.nx_agraph import graphviz_layout
from classes.dialogue_turn import DialogueTurn
import textwrap  # 改行処理のために使用
from tqdm import tqdm  # 進捗バーを表示するために使用

# 日本語フォントの設定
def set_japanese_font():
    # Noto Sans CJK JP フォントを使用
    font_path = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    if os.path.exists(font_path):
        font_prop = font_manager.FontProperties(fname=font_path)
        plt.rcParams['font.family'] = font_prop.get_name()
    else:
        print("Warning: Japanese font not found. Make sure to install a Japanese font.")

# ノードのラベルを適切な長さで改行し、150文字を超える場合は省略する関数
def wrap_and_truncate_text(text, width=20, max_len=100):
    if len(text) > max_len:
        text = text[:max_len] + '...'  # 150文字で切り捨てて省略記号を追加
    return '\n'.join(textwrap.wrap(text, width=width))

# 話者ごとに異なる色を設定する関数
def get_color_map(speakers):
    color_palette = ['lightblue', 'lightgreen', 'lightcoral', 'khaki', 'plum']
    color_map = {speaker: color_palette[i % len(color_palette)] for i, speaker in enumerate(speakers)}
    return color_map

# 画像サイズをノード数に応じて計算する関数
def calculate_figsize(num_nodes):
    if num_nodes <= 8:
        return (15, 12)  # デフォルトのサイズ
    else:
        # 8個以上のノードに対して、スケーリングするルール
        width = 15 + (num_nodes - 8) * 1.4  # 横幅を1.4ずつ増やす
        height = 12 + (num_nodes - 8) * 0.6  # 縦幅は0.6ずつ増やす
        return (width, height)

# 凡例のスケーリング（フォントサイズとマーカーサイズを画像全体の大きさに基づいて設定）
def calculate_legend_size(figsize):
    width, height = figsize
    # 画像全体の10%に相当するサイズを計算
    legend_font_size = max(30, 0.1 * width)
    legend_marker_size = max(300, 0.1 * width * 100)  # マーカーサイズはスケーリングを調整
    return legend_font_size, legend_marker_size

# グラフを作成し、PNGファイルとして保存する関数
def save_dialogue_graph_as_png(dialogue_turns, output_path):
    G = nx.DiGraph()
    speakers = set(turn.speaker for turn in dialogue_turns if turn.speaker != 'NONE')
    color_map = get_color_map(speakers)

    # ノードとエッジを追加
    for index, turn in enumerate(dialogue_turns):
        if turn.source == 'NONE' and turn.targets[0] == 'NONE':
            continue  # ソースとターゲットがNONEの場合、ノードを追加しない
        if turn.sentence:  # sentenceが存在することを確認
            node_label = f"{index + 1}: {wrap_and_truncate_text(turn.sentence)}"
            G.add_node(turn.ae_id, label=node_label, color=color_map[turn.speaker])
            if turn.source != 'NONE':
                G.add_edge(turn.source, turn.ae_id)

    # ノードの数に応じて画像サイズを動的に設定
    num_nodes = len(G.nodes)
    figsize = calculate_figsize(num_nodes)  # 画像サイズを計算
    legend_font_size, legend_marker_size = calculate_legend_size(figsize)  # 凡例のサイズを計算
    print(f"Generating graph with {num_nodes} nodes, figsize={figsize}, legend_font_size={legend_font_size}")

    # グラフを描画
    pos = graphviz_layout(G, prog='dot')  # 'dot'レイアウトを使用
    plt.figure(figsize=figsize)  # 計算されたサイズを設定

    for node in G.nodes:
        x, y = pos[node]
        if 'label' in G.nodes[node]:  # labelが存在するか確認
            plt.text(x, y, G.nodes[node]['label'], fontsize=10, ha='center', va='center',
                     bbox=dict(facecolor=G.nodes[node]['color'], edgecolor='black', boxstyle='round,pad=0.3'))

    nx.draw_networkx_edges(G, pos, arrowstyle='-|>', arrowsize=15, edge_color='black')
    plt.axis('off')

    # 話者の凡例を描画（スケーリングされたフォントサイズとマーカーサイズを使用）
    for speaker, color in color_map.items():
        plt.scatter([], [], c=color, label=speaker, s=legend_marker_size)
    plt.legend(title='Speaker Colors', loc='upper left', bbox_to_anchor=(1, 1), fontsize=legend_font_size)

    plt.savefig(output_path, format='png', bbox_inches='tight')
    plt.close()

# CSVディレクトリと出力ディレクトリを指定
csv_dir = '/home/hasegawa_tomokazu/ami_analysis/CSV_topics_jp'
output_dir = '/home/hasegawa_tomokazu/ami_analysis/graph_images_jp'

# 出力ディレクトリが存在しない場合は作成
os.makedirs(output_dir, exist_ok=True)

# 日本語フォントを設定
set_japanese_font()

# CSVディレクトリ内のすべてのCSVファイルを取得
csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]

# 進捗バーを表示しながら処理を実行
for csv_file in tqdm(csv_files, desc="Processing CSV files"):
    csv_path = os.path.join(csv_dir, csv_file)
    dialogue_turns = DialogueTurn.from_csv(csv_path)

    # 出力ファイルの名前をCSVファイルの名前に基づいて決定
    output_file_name = os.path.splitext(csv_file)[0] + '.png'
    output_path = os.path.join(output_dir, output_file_name)

    # グラフを保存
    save_dialogue_graph_as_png(dialogue_turns, output_path)
