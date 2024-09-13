#coding:utf-8

import subprocess
import xml.etree.ElementTree as ET
import datetime as dt
import glob
import sys
import re
import os
import csv  # 追加：CSVモジュールのインポート
from collections import defaultdict

#　自作クラスのインポート
from classes.meeting import Meeting

# ファイルのパス
dir_path = os.path.dirname(os.path.abspath(__file__))
ami_corpus_path = dir_path + '/ami_public_manual_1.6.2/'
manifest_path = ami_corpus_path + 'MANIFEST_MANUAL.txt'
ae_dir_path = ami_corpus_path + 'argumentation/ae/'
ar_dir_path = ami_corpus_path + 'argumentation/ar/'
words_dir_path = ami_corpus_path + 'words/'

def get_index_of_word_id(text):
    # 正規表現で末尾の数字を抽出
    match = re.search(r'(\d+)$', text)
    if match:
        return int(match.group(1))
    else:
        # 適切な例外を発生させる
        raise ValueError(f"'{text}' does not contain a trailing number.")

def remove_words_suffix(text):
    # 正規表現で末尾の数字を探す
    if re.search(r'\d+$', text):
        # 数字が見つかったら削除
        return re.sub(r'\d+$', '', text)
    else:
        # 数字が見つからなければ例外を発生
        raise ValueError(f"No trailing number found in '{text}'")

def extract_speaker_info(text):
    # 正規表現で . と . の間の大文字のアルファベットを抽出
    match = re.search(r'\.(\b[A-Z]\b)\.', text)
    if match:
        return match.group(1)
    else:
        # マッチしない場合は例外を発生させる
        raise ValueError(f"No speaker information found in '{text}'")

def remove_spaces_before_punctuation(text):
    # カンマとピリオドの前にある空白を削除
    cleaned_text = re.sub(r'\s+([,.])', r'\1', text)
    return cleaned_text

def get_participants_list_from_meeting_id(meeting_id):
    # ae_dir_path内のファイル名を取得
    ae_files = glob.glob(f"{ae_dir_path}{meeting_id}*.xml")
    # ae_files内のファイル名からmeeting_idが含まれるものファイル名を取得
    participants = [os.path.basename(file).split('.')[1] for file in ae_files]
    return participants

#######################################
###########ここまでヘルパー関数##########
######################################

def get_meeting_ids_with_topics_and_argumentation():
    with open(manifest_path, 'r') as f:
        records = f.readlines()
    del records[0:18]
    meetings = [Meeting(record) for record in records]
    meetings_to_use = [meeting for meeting in meetings if meeting.has_topics_and_argumentation()]
    meeting_ids = [meeting.name for meeting in meetings_to_use]
    return meeting_ids

def get_ae_list_from_meeting_id(meeting_id, person):
    # ファイルパスの設定
    xml_file = f"{ae_dir_path}{meeting_id}.{person}.argumentstructs.xml"

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
                # 抽出されたidの数が2つの場合のみ処理
                if len(matches) == 2:
                    start = matches[0]  # 最初のid
                    end = matches[1]    # 2番目のid
                    # 結果を辞書に追加
                    result_dict[ae_id] = {'start_word_id': start, 'end_word_id': end}
                    
    return result_dict

def get_words_from_meeting_id(meeting_id, person):
    xml_file = f"{words_dir_path}{meeting_id}.{person}.words.xml"
    # XMLファイルのパース
    tree = ET.parse(xml_file)
    root = tree.getroot()
    result_dict = {}
    # すべての "w" タグを走査
    for child in root:
        word_id = child.attrib.get('{http://nite.sourceforge.net/}id')
        #　言い淀みの場合はwordがないので空文字を入れる
        if child.tag == 'w':
            word = child.text
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

def build_sentences_with_speaker_and_timestamps(ae_dict, words_dict, participant):
    keys = list(ae_dict.keys())
    sentence_dict = {}

    for key in keys:
        start_word_id = ae_dict[key]['start_word_id']
        end_word_id = ae_dict[key]['end_word_id']
        meeting_id = remove_words_suffix(start_word_id)

        sentence = ''

        for i in range(get_index_of_word_id(start_word_id), get_index_of_word_id(end_word_id) + 1):
            word_index = meeting_id + str(i)
            sentence += words_dict[word_index]['word'] + ' '
            start_time = words_dict[start_word_id]['start_time']
            end_time = words_dict[end_word_id]['end_time']
            speaker = participant

        sentence = remove_spaces_before_punctuation(sentence)
        
        sentence_dict[key] = {'sentence': sentence.strip(), 'start_time': start_time, 'end_time': end_time, 'speaker': speaker}

    return sentence_dict

def main():
    meeting_ids = get_meeting_ids_with_topics_and_argumentation()

    for meeting_id in meeting_ids:

        participants = get_participants_list_from_meeting_id(meeting_id)
        participants.sort()
        sentence_dict = []

        for participant in participants:
            ae_dict = get_ae_list_from_meeting_id(meeting_id, participant)
            words_dict = get_words_from_meeting_id(meeting_id, participant)
            sentence_dict.append(build_sentences_with_speaker_and_timestamps(ae_dict, words_dict, participant))

        # ここにソート処理を入れる

        # sentence_dict のリストをフラットなリストに変換
        all_sentences = []
        for participant_dict in sentence_dict:
            for ae_id, ae_info in participant_dict.items():
                # 'ae_id' を情報に追加
                ae_info['ae_id'] = ae_id
                all_sentences.append(ae_info)

        # 'start_time' を基準にソート（float に変換して正確に比較）
        sorted_sentences = sorted(all_sentences, key=lambda x: float(x['start_time']))

        # ここでファイルに書き出す処理を追加

        # ファイル名を設定（例: meeting_id.csv）
        output_file = f"{meeting_id}.csv"

        # ファイルのパスを設定（スクリプトのあるディレクトリ）
        output_path = os.path.join(dir_path + '/CSV', output_file)

        # ファイルに書き出す
        with open(output_path, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for sentence in sorted_sentences:
                # 各発言をリストとして書き出し
                writer.writerow([
                    sentence['ae_id'],
                    sentence['speaker'],
                    sentence['start_time'],
                    sentence['end_time'],
                    sentence['sentence']
                ])

if __name__ == "__main__":
    main()
