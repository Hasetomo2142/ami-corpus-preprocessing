#coding:utf-8

import subprocess
import xml.etree.ElementTree as ET
import datetime as dt
import glob
import sys
import re
import os
import csv
from collections import defaultdict
from tqdm import tqdm
import pickle
import queue

# 自作クラスのインポート
from classes.meeting import Meeting
from classes.dialogue_turn import DialogueTurn

# ファイルのパス
dir_path = os.path.dirname(os.path.abspath(__file__))
ami_corpus_path = os.path.join(dir_path, 'ami_public_manual_1.6.2')
manifest_path = os.path.join(ami_corpus_path, 'MANIFEST_MANUAL.txt')
ae_dir_path = os.path.join(ami_corpus_path, 'argumentation', 'ae')
ar_dir_path = os.path.join(ami_corpus_path, 'argumentation', 'ar')
dis_dir_path = os.path.join(ami_corpus_path, 'argumentation', 'dis')
words_dir_path = os.path.join(ami_corpus_path, 'words')
segments_dir_path = os.path.join(ami_corpus_path, 'segments')
csv_path = os.path.join(dir_path, 'CSV')

def get_index_of_word_id(text):
    # 正規表現で末尾の数字を抽出
    match = re.search(r'(\d+)$', text)
    if match:
        return int(match.group(1))
    else:
        raise ValueError(f"'{text}' does not contain a trailing number.")

def remove_words_suffix(text):
    # 正規表現で末尾の数字を削除
    if re.search(r'\d+$', text):
        return re.sub(r'\d+$', '', text)
    else:
        raise ValueError(f"No trailing number found in '{text}'")

def extract_speaker_info(text):
    # 正規表現で . と . の間の大文字のアルファベットを抽出
    match = re.search(r'\.(\b[A-Z]\b)\.', text)
    if match:
        return match.group(1)
    else:
        raise ValueError(f"No speaker information found in '{text}'")

def remove_spaces_before_punctuation(text):
    # カンマとピリオドの前にある空白を削除
    cleaned_text = re.sub(r'\s+([,.])', r'\1', text)
    return cleaned_text

def get_participants_list_from_meeting_id(meeting_id):
    # ae_dir_path内のファイル名を取得
    ae_files = glob.glob(os.path.join(ae_dir_path, f"{meeting_id}.*.argumentstructs.xml"))
    participants = [os.path.basename(file).split('.')[1] for file in ae_files]
    return participants

def get_meeting_ids_with_topics_and_argumentation():
    with open(manifest_path, 'r') as f:
        records = f.readlines()
    del records[0:18]
    meetings = [Meeting(record) for record in records]
    meetings_to_use = [meeting for meeting in meetings if meeting.has_topics_and_argumentation()]
    meeting_ids = [meeting.name for meeting in meetings_to_use]
    return meeting_ids

# ae_dir_path以下のファイルを全て参照し、ae_idをキー、そのaeを構成する最初の単語のword_idを値とする辞書を返す
def get_ae_id_to_word_id_dict():
    # ae_dir_path以下のファイルを全て参照
    ae_files = glob.glob(os.path.join(ae_dir_path, '*.argumentstructs.xml'))
    ae_id_to_word_id = {}
    id_pattern = r'id\(([^)]+)\)'
    
    for ae_file in ae_files:
        # XMLファイルのパース
        tree = ET.parse(ae_file)
        root = tree.getroot()
        
        # すべての "ae" タグを走査
        for child in root:
            ae_id = child.attrib['{http://nite.sourceforge.net/}id']
            
            # 各 "child" タグを走査して、word_id をリストに追加
            for grandson in child:
                if grandson.tag == '{http://nite.sourceforge.net/}child':
                    # 'href' 属性から id() 内の文字列を抽出
                    matches = re.findall(id_pattern, grandson.attrib['href'])
                    if len(matches) >= 1:
                        start = matches[0]
                        end = matches[-1]
                        ae_id_to_word_id[ae_id] = {'start': start, 'end': end}
                        
    # print(ae_id_to_word_id)
    return ae_id_to_word_id



# segments_dir_path以下のファイルを全て参照し、segment_idをキー、そのセグメントを構成する最初の単語のword_idを値とする辞書を返す
def get_segment_id_to_word_id_dict():
    # segments_dir_path以下のファイルを全て参照
    meeting_ids = get_meeting_ids_with_topics_and_argumentation()
    
    segment_files = []
    for meeting_id in meeting_ids:
        segment_files += glob.glob(os.path.join(segments_dir_path, f"{meeting_id}.[A-Z].segments.xml"))
    segment_id_to_word_id = {}
    id_pattern = r'id\(([^)]+)\)'
    
    for segment_file in segment_files:
        # XMLファイルのパース
        tree = ET.parse(segment_file)
        root = tree.getroot()
        
        # すべての "segment" タグを走査
        for child in root:
            segment_id = child.attrib['{http://nite.sourceforge.net/}id']
            
            # 各 "child" タグを走査して、word_id をリストに追加
            for grandson in child:
                if grandson.tag == '{http://nite.sourceforge.net/}child':
                    # 'href' 属性から id() 内の文字列を抽出
                    matches = re.findall(id_pattern, grandson.attrib['href'])
                    if len(matches) >= 1:
                        start = matches[0]
                        end = matches[-1]
                        segment_id_to_word_id[segment_id] = {'start': start, 'end': end}
                        
    # print(segment_id_to_word_id)
    return segment_id_to_word_id


#######################################
###########ここまでヘルパー関数##########
######################################
######################################

# meeting_idからトピックとそのトピックに対応するae_idを取得
def get_discussion_topics_from_meeting_id(meeting_id,segment_id_to_word_id_dict,word_dict):
    

    
    # ファイルパスの設定
    xml_file = os.path.join(dis_dir_path, f"{meeting_id}.discussions.xml")
    # XMLファイルのパース
    tree = ET.parse(xml_file)
    root = tree.getroot()
    id_pattern = r'id\(([^)]+)\)'
    
    # すべての "topic" タグを走査
    topics_dict = {}
    for child in root:
        topic = child.attrib['name']
        segment_list = []
        for grandson in child:
            if grandson.tag == '{http://nite.sourceforge.net/}child':
                match = re.search(id_pattern, grandson.attrib['href'])
                if match:
                    segment = match.group(1)
                    segment_list.append(segment)
        
        # セグメントリストが空でない場合、最初と最後の要素を辞書に保持
        if segment_list:
            start_segment = segment_list[0]
            end_segment = segment_list[-1]
            start_word = segment_id_to_word_id_dict[start_segment]['start']
            end_word = segment_id_to_word_id_dict[end_segment]['end']
            start_time = word_dict[start_word]['start_time']
            end_time = word_dict[end_word]['end_time']
            topics_dict[topic] = {'start_time': start_time, 'end_time': end_time}
            
    
    return topics_dict

def get_words_all():
    # ファイルパスの設定
    xml_files = glob.glob(os.path.join(words_dir_path, '*.words.xml'))

    # 結果を格納する辞書
    result_dict = {}

    # 正規表現でid()の中の部分を抽出
    id_pattern = r'id\(([^)]+)\)'

    for xml_file in xml_files:
        # XMLファイルのパース
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # すべての "w" タグを走査
        for child in root:
            word_id = child.attrib.get('{http://nite.sourceforge.net/}id')
            # 言い淀みの場合はwordがないので空文字を入れる
            if child.tag == 'w':
                word = child.text if child.text else ''
            else:
                word = ''
            # starttimeとendtimeがない場合はスキップ
            try:
                start = child.attrib['starttime']
                end = child.attrib['endtime']
                result_dict[word_id] = {'word': word, 'start_time': start, 'end_time': end}
            except KeyError:
                continue

    return result_dict



def main():
    meeting_ids = get_meeting_ids_with_topics_and_argumentation()
    segment_id_to_word_id_dict = get_segment_id_to_word_id_dict()
    word_dict = get_words_all()
    
    for meeting_id in meeting_ids:

        topics = get_discussion_topics_from_meeting_id(meeting_id, segment_id_to_word_id_dict, word_dict)
        
        # topicsをstart_timeでソート
        sorted_topics = dict(sorted(topics.items(), key=lambda x: float(x[1]['start_time'])))
        
        # トピックをリストとして保持
        topic_list = list(sorted_topics.items())
        
        # CSVファイルのパス
        csv_file = os.path.join(csv_path, f"{meeting_id}.csv")
        dialogue_turns = DialogueTurn.from_csv(csv_file)
        
        # CSV_topicsディレクトリを作成（存在しない場合）
        csv_topics_path = os.path.join(dir_path, 'CSV_topics')
        os.makedirs(csv_topics_path, exist_ok=True)
        
        # CSVのヘッダーを定義
        csv_headers = ['ae_id', 'speaker', 'start_time', 'end_time', 'sentence', 'source', 'targets']
        
        for i in range(len(topic_list)):
            # 現在のトピックの情報を取得
            current_topic, current_times = topic_list[i]
            current_start_time = float(current_times['start_time'])
            
            # 次のトピックのstart_timeを取得 (最後のトピックなら無限大として扱う)
            if i + 1 < len(topic_list):
                next_start_time = float(topic_list[i + 1][1]['start_time'])
            else:
                next_start_time = float('inf')  # 最後のトピックでは終端の時間制限なし
            
            # 現在のトピックに対応するレコードを格納
            topic_records = []
            
            # 各ダイアログターンを確認し、トピックに対応するかをチェック
            for record in dialogue_turns:
                if current_start_time <= float(record.start_time) < next_start_time:
                    topic_records.append(record)
            
            # 現在のトピックに対応するレコードをファイルに出力
            output_csv_file = os.path.join(csv_topics_path, f"{meeting_id}-{current_topic}.csv")
            with open(output_csv_file, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(csv_headers)  # CSVのヘッダーを書き込む
                for topic_record in topic_records:
                    writer.writerow([
                        topic_record.ae_id,
                        topic_record.speaker,
                        topic_record.start_time,
                        topic_record.end_time,
                        topic_record.sentence,
                        topic_record.source,
                        ', '.join(topic_record.targets)  # ターゲットリストを文字列に変換
                    ])

if __name__ == "__main__":
    main()
