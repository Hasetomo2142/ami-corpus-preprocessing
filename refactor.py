#coding:utf-8

import subprocess
import xml.etree.ElementTree as ET
import datetime as dt
import glob
import sys
import re
import os
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
		if child.tag == 'w':
			word_id = child.attrib.get('{http://nite.sourceforge.net/}id')
			word = child.text
			start = child.attrib['starttime']
			end = child.attrib['endtime']
			result_dict[word_id] = {'word': word, 'start_time': start, 'end_time': end}

	return result_dict

def build_sentences_with_speaker_and_timestamps(ae_dict, words_dict):
	keys = list(ae_dict.keys())

	for key in keys:
		start_word_id = ae_dict[key]['start_word_id']
		end_word_id = ae_dict[key]['end_word_id']
		meeting_id = remove_words_suffix(start_word_id)

		sentence = ''

		for i in range(get_index_of_word_id(start_word_id), get_index_of_word_id(end_word_id) + 1):
			word_index = meeting_id + str(i)
			try:
				sentence += words_dict[word_index]['word'] + ' '
				start_time = words_dict[start_word_id]['start_time']
				end_time = words_dict[end_word_id]['end_time']
				speaker = extract_speaker_info(start_word_id)
			except KeyError:
				print('-' * 150)
				print(f"Word with index {word_index} not found in words_dict")
				break
		
		sentence = remove_spaces_before_punctuation(sentence)

		print('-' * 150)
		print(sentence)
		print(f"Start time: {start_time}")
		print(f"End time: {end_time}")
		print(f"Speaker: {speaker}")
		print(f"key: {key}")



def main():
	meeting_ids = get_meeting_ids_with_topics_and_argumentation()
	ae_dict = get_ae_list_from_meeting_id(meeting_ids[0], 'D')
	words_dict = get_words_from_meeting_id(meeting_ids[0], 'D')
	build_sentences_with_speaker_and_timestamps(ae_dict, words_dict)
	# print(ae_dict)
	# print('-' * 150)
	# print(words_dict)


if __name__ == "__main__":
	main()
