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

# 自作クラスのインポート
from classes.meeting import Meeting

# ファイルのパス
dir_path = os.path.dirname(os.path.abspath(__file__))
ami_corpus_path = os.path.join(dir_path, 'ami_public_manual_1.6.2')
manifest_path = os.path.join(ami_corpus_path, 'MANIFEST_MANUAL.txt')
ae_dir_path = os.path.join(ami_corpus_path, 'argumentation', 'ae')
ar_dir_path = os.path.join(ami_corpus_path, 'argumentation', 'ar')
dis_dir_path = os.path.join(ami_corpus_path, 'argumentation', 'dis')
words_dir_path = os.path.join(ami_corpus_path, 'words')
segments_dir_path = os.path.join(ami_corpus_path, 'segments')

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
    for ae_file in ae_files:
        # XMLファイルのパース
        tree = ET.parse(ae_file)
        root = tree.getroot()
        # すべての "ae" タグを走査
        for child in root:
            ae_id = child.attrib['{http://nite.sourceforge.net/}id']
            for grandson in child:
                if grandson.tag == '{http://nite.sourceforge.net/}child':
                    # 'href' 属性から id() 内の文字列を抽出
                    match = re.search(r'id\(([^)]+)\)', grandson.attrib['href'])
                    if match:
                        word_id = match.group(1)
                        ae_id_to_word_id[ae_id] = word_id
                        break
    return ae_id_to_word_id


# segments_dir_path以下のファイルを全て参照し、segment_idをキー、そのセグメントを構成する最初の単語のword_idを値とする辞書を返す
def get_segment_id_to_word_id_dict():
    # segments_dir_path以下のファイルを全て参照
    segment_files = glob.glob(os.path.join(segments_dir_path, '*.segments.xml'))
    segment_id_to_word_id = {}
    for segment_file in segment_files:
        # XMLファイルのパース
        tree = ET.parse(segment_file)
        root = tree.getroot()
        # すべての "segment" タグを走査
        for child in root:
            segment_id = child.attrib['{http://nite.sourceforge.net/}id']
            for grandson in child:
                if grandson.tag == '{http://nite.sourceforge.net/}child':
                    # 'href' 属性から id() 内の文字列を抽出
                    match = re.search(r'id\(([^)]+)\)', grandson.attrib['href'])
                    if match:
                        word_id = match.group(1)
                        segment_id_to_word_id[segment_id] = word_id
                        break
    return segment_id_to_word_id

#######################################
###########ここまでヘルパー関数##########
######################################

# ae_id_to_word_idとsegment_id_to_word_idを組み合わせて、
def create_segment_to_ae_mapping():
    
    ae_id_to_word_id = get_ae_id_to_word_id_dict()
    segment_id_to_word_id = get_segment_id_to_word_id_dict()
    
    print(len(ae_id_to_word_id))
    print(len(segment_id_to_word_id))

    # word_id をキーとして、対応する ae_id のリストを作成
    word_id_to_ae_ids = defaultdict(list)
    for ae_id, word_id in ae_id_to_word_id.items():
        word_id_to_ae_ids[word_id].append(ae_id)
    
    # word_id をキーとして、対応する segment_id のリストを作成
    word_id_to_segment_ids = defaultdict(list)
    for segment_id, word_id in segment_id_to_word_id.items():
        word_id_to_segment_ids[word_id].append(segment_id)
    
    # 新しい辞書を作成
    segment_to_ae_mapping = defaultdict(list)
    
    # 共通の word_id に対して、対応する ae_id と segment_id をマッピング
    common_word_ids = set(word_id_to_ae_ids.keys()) & set(word_id_to_segment_ids.keys())
    for word_id in common_word_ids:
        ae_ids = word_id_to_ae_ids[word_id]
        segment_ids = word_id_to_segment_ids[word_id]
        for segment_id in segment_ids:
            for ae_id in ae_ids:
                segment_to_ae_mapping[segment_id].append(ae_id)
    
    # 必要に応じて、defaultdict を通常の辞書に変換
    segment_to_ae_mapping = dict(segment_to_ae_mapping)
    
    print(len(segment_to_ae_mapping))
    return segment_to_ae_mapping


# meeting_idからトピックとそのトピックに対応するae_idを取得
def get_discussion_topics_from_meeting_id(meeting_id):
    # ファイルパスの設定
    xml_file = os.path.join(dis_dir_path, f"{meeting_id}.discussions.xml")
    # XMLファイルのパース
    tree = ET.parse(xml_file)
    root = tree.getroot()
    id_pattern = r'id\(([^)]+)\)'
    
    # すべての "topic" タグを走査
    topics_dict = defaultdict(list)
    for child in root:
        topic = child.attrib['name']
        for grandson in child:
            if grandson.tag == '{http://nite.sourceforge.net/}child':
                match = re.search(id_pattern, grandson.attrib['href'])
                if match:
                    segment = match.group(1)
                    topics_dict[topic].append(segment)
            
    return topics_dict


def get_ae_list_from_meeting_id(meeting_id, person):
    # ファイルパスの設定
    xml_file = os.path.join(ae_dir_path, f"{meeting_id}.{person}.argumentstructs.xml")

    # XMLファイルのパース
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # 結果を格納する辞書
    result_dict = {}

    # 正規表現でid()の中の部分を抽出
    id_pattern = r'id\(([^)]+)\)'

    # すべての "ae" タグを走査
    for child in root:
        ae_id = child.attrib.get('{http://nite.sourceforge.net/}id')
        for grandson in child:
            if grandson.tag == '{http://nite.sourceforge.net/}child':
                # 'href' 属性から id() 内の文字列を抽出
                matches = re.findall(id_pattern, grandson.attrib['href'])
                if len(matches) >= 1:
                    start = matches[0]
                    end = matches[-1]
                    result_dict[ae_id] = {'start_word_id': start, 'end_word_id': end}

    return result_dict

def get_words_from_meeting_id(meeting_id, person):
    xml_file = os.path.join(words_dir_path, f"{meeting_id}.{person}.words.xml")
    # XMLファイルのパース
    tree = ET.parse(xml_file)
    root = tree.getroot()
    result_dict = {}
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

def get_source_and_target_from_ae(meeting_id):
    # ファイルパスの設定
    xml_file = os.path.join(ar_dir_path, f"{meeting_id}.argumentationrels.xml")

    tree = ET.parse(xml_file)
    root = tree.getroot()

    # sourceをキー、targetsを値（リスト）とする辞書
    source_to_target = defaultdict(list)

    # targetをキー、sourceを値とする辞書
    target_to_source = {}

    id_pattern = r'id\(([^)]+)\)'

    for child in root:
        source = ''
        target = ''
        for grandson in child:
            if grandson.tag == '{http://nite.sourceforge.net/}pointer':
                match = re.search(id_pattern, grandson.attrib['href'])
                if match:
                    ae_ref = match.group(1)
                    role = grandson.attrib.get('role')
                    if role == 'source':
                        source = ae_ref
                    elif role == 'target':
                        target = ae_ref
        if source or target:
            if source:
                source_to_target[source].append(target if target else 'None')
            if target:
                target_to_source[target] = source if source else 'None'
                
    
    return source_to_target, target_to_source

def build_sentences_with_speaker_and_timestamps(ae_dict, words_dict, participant, source_to_target, target_to_source):
    keys = list(ae_dict.keys())
    sentence_dict = {}

    for key in keys:
        start_word_id = ae_dict[key]['start_word_id']
        end_word_id = ae_dict[key]['end_word_id']
        meeting_id = remove_words_suffix(start_word_id)

        sentence = ''

        for i in range(get_index_of_word_id(start_word_id), get_index_of_word_id(end_word_id) + 1):
            word_index = meeting_id + str(i)
            word_info = words_dict.get(word_index)
            if word_info:
                sentence += word_info['word'] + ' '
            else:
                print(f"Word ID {word_index} not found in words_dict")
        start_time = words_dict[start_word_id]['start_time']
        end_time = words_dict[end_word_id]['end_time']
        speaker = participant

        sentence = remove_spaces_before_punctuation(sentence)

        # source と target を取得
        source = target_to_source.get(key, 'NONE')
        targets = source_to_target.get(key, [])
        if targets:
            targets_str = '{' + ','.join(targets) + '}'
        else:
            targets_str = 'NONE'

        sentence_dict[key] = {
            'sentence': sentence.strip(),
            'start_time': start_time,
            'end_time': end_time,
            'speaker': speaker,
            'source': source,
            'targets': targets_str
        }

    return sentence_dict

def main():
    meeting_ids = get_meeting_ids_with_topics_and_argumentation()
    topics = get_discussion_topics_from_meeting_id(meeting_ids[0])
    # print(topics)
    dict = create_segment_to_ae_mapping()
    # print (dict)
    # for meeting_id in meeting_ids:

    #     # source_to_target, target_to_sourceを取得
    #     source_to_target, target_to_source = get_source_and_target_from_ae(meeting_id)

    #     participants = get_participants_list_from_meeting_id(meeting_id)
    #     participants.sort()
    #     sentence_dict_list = []

    #     for participant in participants:
    #         ae_dict = get_ae_list_from_meeting_id(meeting_id, participant)
    #         words_dict = get_words_from_meeting_id(meeting_id, participant)
    #         sentence_dict = build_sentences_with_speaker_and_timestamps(
    #             ae_dict, words_dict, participant, source_to_target, target_to_source)
    #         sentence_dict_list.append(sentence_dict)

    #     # sentence_dict のリストをフラットなリストに変換
    #     all_sentences = []
    #     for participant_dict in sentence_dict_list:
    #         for ae_id, ae_info in participant_dict.items():
    #             ae_info['ae_id'] = ae_id
    #             all_sentences.append(ae_info)

    #     # 'start_time' を基準にソート
    #     sorted_sentences = sorted(all_sentences, key=lambda x: float(x['start_time']))

    #     # 各meeting_idごとに最初のレコードのsourceを'ROOT'に設定
    #     if sorted_sentences:
    #         sorted_sentences[0]['source'] = 'ROOT'

    #     # ファイル名を設定
    #     output_file = f"{meeting_id}.csv"

    #     # ファイルのパスを設定
    #     output_dir = os.path.join(dir_path, 'CSV')
    #     os.makedirs(output_dir, exist_ok=True)
    #     output_path = os.path.join(output_dir, output_file)

    #     # ファイルに書き出す
    #     with open(output_path, 'w', encoding='utf-8', newline='') as csvfile:
    #         writer = csv.writer(csvfile)
    #         # ヘッダーを書き込む
    #         writer.writerow(['ae_id', 'speaker', 'start_time', 'end_time', 'sentence', 'source', 'targets'])
    #         for sentence in sorted_sentences:
    #             writer.writerow([
    #                 sentence['ae_id'],
    #                 sentence['speaker'],
    #                 sentence['start_time'],
    #                 sentence['end_time'],
    #                 sentence['sentence'],
    #                 sentence['source'],
    #                 sentence['targets']
    #             ])


if __name__ == "__main__":
    main()
