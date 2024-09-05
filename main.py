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

class CorenlpSentiment:
    def __init__(self, dirname, outputoption='ROOT'):
        self.dirname = dirname
        self.outputoption = outputoption
    def parse(self, text):
        res = subprocess.check_output('echo "' + text + '" | java -cp "' + self.dirname + '*" -mx5g edu.stanford.nlp.sentiment.SentimentPipeline -stdin -output ' + self.outputoption + ' ', shell=True)
        return res

def conv_to_timedelta(time):
    #秒以下の時間形成

    add_list = [0, 100000, 10000, 1000, 100, 10, 1]

    time = time.split('.')
    return dt.timedelta(seconds = int(time[0]), microseconds = int(time[1]) * add_list[len(time[1])])

def file_id():
    # Argument,topicがアノテーションされた対話IDの取得
    f_id = []
    is_data = []

    # text dataの取得
    f = open(manifest_path)
    data = f.read().splitlines()
    f.close()

    # 不必要な情報は削除
    for i in range(0,19):
        del data[0]

    #アノテーション対話データを扱いやすい形へ
    for word in data:
        file_name = ""
        is_list = []
        for i in range(len(word)):
            if i < 7:
                file_name += word[i]
            elif i == 7:
                is_list.append(file_name)
            elif i > 7 and i % 4 == 2:
                is_list.append(word[i])
        is_data.append(is_list)

    #13: topic, 14: argumentation
    for file_info in is_data:
        if file_info[13] == "X" and file_info[14] == "X":
            f_id.append(file_info[0])
    return f_id

def get_meeting_ids_with_topics_and_argumentation():
  
  with open(manifest_path, 'r') as f: 
    records = f.readlines()
    
  del records[0:18]

  meetings = [Meeting(record) for record in records]
  meetings_to_use = [meeting for meeting in meetings if meeting.has_topics_and_argumentation()]
  meeting_ids = [meeting.name for meeting in meetings_to_use]
  
  return meeting_ids

def get_discourse_act():
    # 談話行為タグのリスト
    da_types_list = []
    # da-types.xmlの情報を取得
    da_types_tree = ET.parse(ami_corpus_path + 'ontologies/da-types.xml')
    da_types_root = da_types_tree.getroot()

    for child in da_types_root:
        for grandson in child:
            da_types_list.append({'ID': grandson.attrib['{http://nite.sourceforge.net/}id'], 'name': grandson.attrib['name'], 'gloss': grandson.attrib['gloss']})

    return da_types_list

def get_adjancecy_pair():
    # 隣接ペアのリスト
    ap_types_list = []
    # ap_type.xmlの情報取得
    ap_types_tree = ET.parse(ami_corpus_path + 'ontologies/ap-types.xml')
    ap_types_root = ap_types_tree.getroot()

    for child in ap_types_root:
        ap_types_list.append({'ID': child.attrib['{http://nite.sourceforge.net/}id'], 'name': child.attrib['name'], 'gloss': child.attrib['gloss']})

    return ap_types_list

def get_argument_elements():
    # 議論要素タグのリスト
    ae_types_list = []
    # ae_types.xmlの情報を取得
    ae_types_tree = ET.parse(ami_corpus_path + 'ontologies/ae-types.xml')
    ae_types_root = ae_types_tree.getroot()

    for child in ae_types_root:
        ae_types_list.append({'ID': child.attrib['{http://nite.sourceforge.net/}id'], 'name': child.attrib['name'], 'gloss': child.attrib['gloss']})

    return ae_types_list

def get_argument_relations():
    # 議論関係タグのリスト
    ar_types_list = []

    # ar-types.xmlの情報を取得
    da_types_tree = ET.parse(ami_corpus_path + 'ontologies/ar-types.xml')
    da_types_root = da_types_tree.getroot()

    for child in da_types_root:
        ar_types_list.append({'ID': child.attrib['{http://nite.sourceforge.net/}id'], 'name': child.attrib['name'], 'gloss': child.attrib['gloss']})

    return ar_types_list

def get_topics():
    # トピックタグのリスト
    default_topics_list = []

    # default-topics.xmlの情報を取得
    default_topics_tree = ET.parse(ami_corpus_path + 'ontologies/default-topics.xml')
    default_topics_root = default_topics_tree.getroot()

    default_topics_list.append({'ID': default_topics_root.attrib['{http://nite.sourceforge.net/}id'], 'name': default_topics_root.attrib['name']})
    for child in default_topics_root:
        default_topics_list.append({'ID': child.attrib['{http://nite.sourceforge.net/}id'], 'name': child.attrib['name']})
        for grandson in child:
            default_topics_list.append({'ID': grandson.attrib['{http://nite.sourceforge.net/}id'], 'name': grandson.attrib['name']})

    return default_topics_list

def extract_topic(dialogue_id):
    # 対応したトピックファイルの情報を抽出
    topic_tree = ET.parse(ami_corpus_path + 'topics/' + dialogue_id + '.topic.xml')
    topic_root = topic_tree.getroot()

    # word_idとtopの対応関係を作成
    speaker_id2index = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
    word_id2top = [[] for i in range(4)]

    for child in topic_root:
        main_topic_id = ''
        sub_topic_id = ''
        sp_id = ''
        word_id_list = []
        for grandson in child:
            # トピックのidならばidを取得
            if grandson.tag == '{http://nite.sourceforge.net/}pointer':
                main_topic_id = re.search('top.[0-9][0-9]?[0-9]?', grandson.attrib['href']).group(0)
            # 単語の範囲を取得
            elif grandson.tag == '{http://nite.sourceforge.net/}child':
                word_id_list = re.findall(dialogue_id + '.[A-D].words[0-9][0-9]?[0-9]?[0-9]?', grandson.attrib['href'])
                sp_id = word_id_list[0].split('.')[1]
                if len(word_id_list) == 1:
                    word_id2top[speaker_id2index[sp_id]].append({'word_id_num': int(word_id_list[0].split('.')[2].replace('words', '')), 'main_topic_id':  main_topic_id, 'sub_topic_id': sub_topic_id})
                elif len(word_id_list) == 2:
                    start_num = int(word_id_list[0].split('.')[2].replace('words', ''))
                    end_num = int(word_id_list[1].split('.')[2].replace('words', ''))
                    for i in range(end_num - start_num + 1):
                        word_id2top[speaker_id2index[sp_id]].append({'word_id_num': start_num + i, 'main_topic_id': main_topic_id, 'sub_topic_id': sub_topic_id})

            # サブトピックがあればそれを含めて処理
            elif grandson.tag == 'topic':
                for g_grandson in grandson:
                    if g_grandson.tag == '{http://nite.sourceforge.net/}pointer':
                        sub_topic_id = re.search('top.[0-9][0-9]?[0-9]?', g_grandson.attrib['href']).group(0)
                    elif g_grandson.tag == '{http://nite.sourceforge.net/}child':
                        word_id_list = re.findall(dialogue_id + '.[A-D].words[0-9][0-9]?[0-9]?[0-9]?', g_grandson.attrib['href'])
                        sp_id = word_id_list[0].split('.')[1]
                        if len(word_id_list) == 1:
                            word_id2top[speaker_id2index[sp_id]].append({'word_id_num': int(word_id_list[0].split('.')[2].replace('words', '')), 'main_topic_id': main_topic_id, 'sub_topic_id': sub_topic_id})
                        elif len(word_id_list) == 2:
                            start_num = int(word_id_list[0].split('.')[2].replace('words', ''))
                            end_num = int(word_id_list[1].split('.')[2].replace('words', ''))
                            for i in range(end_num - start_num + 1):
                                word_id2top[speaker_id2index[sp_id]].append({'word_id_num': start_num + i, 'main_topic_id': main_topic_id, 'sub_topic_id': sub_topic_id})
                sub_topic_id = ''


    return word_id2top

def extract_words_argument(dialogue_id, not_ae_list):
    """
    各ダイアログデータの抽出

    word_ae_info: 単語情報と議論要素の辞書の組み合わせのリスト

    word_ar_info: 単語情報と議論関係の辞書の組み合わせリスト

    wood_root: word.xmlの情報

    dialogue_id: 対話の名前

    speaker_id: 話者の情報
    """

    # 各対話の議論構造の情報リスト
    word_id2ae_id = []

    # 対応した議論関係の情報を取得
    word_ar_id = []
    # 対応した隣接ペアの情報を取得
    word_ap_id = []

    # 各話者のwordsファイル
    file_list = sorted(glob.glob(ami_corpus_path + 'words/' + dialogue_id + '.*.words.xml'))

    for filename in file_list:
        # word.xmlの情報を取得
        word_tree = ET.parse(filename)
        word_root = word_tree.getroot()

        # 話者IDの取得
        speaker_id = word_root.attrib['{http://nite.sourceforge.net/}id'].split('.')[1]

        # 発話と時間を蓄える一時変数 #
        utterance = {'ID': '', 'start': dt.timedelta(seconds = -1), 'end': dt.timedelta(seconds = -1), 'da_list': [], 'da_link': [], 'ae_list': [], 'ar_link': [], 'segment': '', 'top_list': [], 'utterance': '', 'sentiment':[]}

        # 対応した談話行為タグを取得
        word_da_id = []
        # 対応した議論要素の情報を取得
        word_ae_id = []
        # 対応したセグメントの情報を取得
        word_se_id = []
        # 議論要素と議論関係の情報を結合
        word_st_id = []
        if [dialogue_id,speaker_id] not in not_ae_list:
            # 対応した談話行為ファイルの情報を取得
            da_tree = ET.parse(ami_corpus_path + 'dialogueActs/' + dialogue_id + '.' + speaker_id + '.dialog-act.xml')
            da_root = da_tree.getroot()

            # 対応した隣接ペアファイルの情報を取得
            ap_tree = ET.parse(ami_corpus_path + 'dialogueActs/' + dialogue_id + '.adjacency-pairs.xml')
            ap_root = ap_tree.getroot()
            
            # 対応した議論要素ファイルの情報を取得
            ae_tree = ET.parse(ami_corpus_path + 'argumentation/ae/' + dialogue_id + '.' + speaker_id + '.argumentstructs.xml')
            ae_root = ae_tree.getroot()

            # 対応した議論関係ファイルの情報を取得
            ar_tree = ET.parse(ami_corpus_path + 'argumentation/ar/' + dialogue_id + '.' + 'argumentationrels.xml')
            ar_root = ar_tree.getroot()

            # 対応したセグメントの情報を取得
            se_tree = ET.parse(ami_corpus_path + 'segments/' + dialogue_id + '.' + speaker_id + '.segments.xml')
            se_root = se_tree.getroot()

            # word_id抽出のためのフィルター
            word_id_filter = dialogue_id + '.' + speaker_id + '.words[0-9][0-9]?[0-9]?[0-9]?'

            # word_idとda_idの対応関係を作成
            for child in da_root:
                da_id = ''
                word_id_list = []
                da_link = child.attrib['{http://nite.sourceforge.net/}id']
                for grandson in child:
                    # 談話行為のidならばidを取得
                    if grandson.tag == '{http://nite.sourceforge.net/}pointer':
                        da_id = re.search('ami_da_[0-9][0-9]?', grandson.attrib['href']).group(0)
                    # 単語の範囲を取得
                    elif grandson.tag == '{http://nite.sourceforge.net/}child':
                        word_id_list = re.findall(word_id_filter, grandson.attrib['href'])
                        if len(word_id_list) == 1:
                            word_da_id.append({'word_id_num': int(word_id_list[0].split('.')[2].replace('words', '')), 'da_link': da_link, 'da_id': da_id})
                        elif len(word_id_list) == 2:
                            start_num = int(word_id_list[0].split('.')[2].replace('words', ''))
                            end_num = int(word_id_list[1].split('.')[2].replace('words', ''))
                            for i in range(end_num - start_num + 1):
                                word_da_id.append({'word_id_num': start_num + i, 'da_link': da_link, 'da_id': da_id})

            # word_idとae_idの対応関係を作成
            for child in ae_root:
                ae_id = ''
                word_id_list = []
                ar_link = child.attrib['{http://nite.sourceforge.net/}id']
                for grandson in child:
                    # 議論要素のidならばidを取得
                    if grandson.tag == '{http://nite.sourceforge.net/}pointer':
                        ae_id = re.search('ae_[0-9]', grandson.attrib['href']).group(0)
                    # 単語の範囲を取得
                    elif grandson.tag == '{http://nite.sourceforge.net/}child':
                        word_id_list = re.findall(word_id_filter, grandson.attrib['href'])
                        if len(word_id_list) == 1:
                            word_ae_id.append({'word_id_num': int(word_id_list[0].split('.')[2].replace('words', '')), 'ae_id': ae_id, 'ar_link': ar_link}\
)
                        elif len(word_id_list) == 2:
                            start_num = int(word_id_list[0].split('.')[2].replace('words', ''))
                            end_num = int(word_id_list[1].split('.')[2].replace('words', ''))
                            for i in range(end_num - start_num + 1):
                              word_ae_id.append({'word_id_num': start_num + i, 'ae_id': ae_id, 'ar_link': ar_link})

            # word_idとse_idの対応関係を作成
            for child in se_root:
                se_id = child.attrib['{http://nite.sourceforge.net/}id']
                word_id_list = []
                for grandson in child:
                    if grandson.tag == '{http://nite.sourceforge.net/}child':
                        word_id_list = re.findall(word_id_filter, grandson.attrib['href'])
                        if len(word_id_list) == 1:
                            word_se_id.append({'word_id_num': int(word_id_list[0].split('.')[2].replace('words','')), 'se_id': se_id})
                        elif len(word_id_list) == 2:
                            start_num = int(word_id_list[0].split('.')[2].replace('words', ''))
                            end_num = int(word_id_list[1].split('.')[2].replace('words', ''))
                            for i in range(end_num - start_num + 1):
                              word_se_id.append({'word_id_num': start_num + i, 'se_id': se_id})

            # word_idとar_idの対応関係を作成
            if speaker_id == 'A':
                for child in ar_root:
                    ar_id = ''
                    source_st = ''
                    target_st = ''
                    tag = child.attrib['{http://nite.sourceforge.net/}id'].split(".")
                    ar_tag = child.attrib['{http://nite.sourceforge.net/}id']
                    for grandson in child:
                        # 議論関係のidならばidを取得
                        if re.search('art_[0-9]', grandson.attrib['href']) != None:
                            ar_id = re.search('art_[0-9]', grandson.attrib['href']).group(0)
                        # sourceのsegment_idの取得
                        if grandson.attrib['role'] == 'source':
                            source_st = dialogue_id + re.search('.[A-D]', grandson.attrib['href']).group(0) + '.argumentstructs.' + re.search(tag[2] + '.[0-9][0-9]?[0-9]?', grandson.attrib['href']).group(0)
                        # targetのsegment_idの取得
                        elif grandson.attrib['role'] == 'target':
                            target_st = dialogue_id + re.search('.[A-D]', grandson.attrib['href']).group(0) + '.argumentstructs.' + re.search(tag[2] + '.[0-9][0-9]?[0-9]?', grandson.attrib['href']).group(0)
                    #print(source_st, target_st)
                    word_ar_id.append({'source': source_st, 'target': target_st, 'ar_id': ar_id, 'ar_tag': ar_tag})

                #print(word_ar_id)

                
                for child in ap_root:
                    ap_id = ''
                    source_ap = ''
                    target_ap = ''
                    tag = child.attrib['{http://nite.sourceforge.net/}id'].split('.')
                    ap_tag = child.attrib['{http://nite.sourceforge.net/}id']
                    for grandson in child:
                        # 隣接ペアのidならばidの取得
                        if grandson.attrib['role'] == 'type':
                            ap_id = re.search('apt_[0-9]', grandson.attrib['href']).group(0)
                        # sourceのidの取得
                        if grandson.attrib['role'] == 'source':
                            source_ap = dialogue_id + re.search('.[A-D]', grandson.attrib['href']).group(0) + '.dialog-act.' + re.search(tag[2] + '.[0-9][0-9]?[0-9]?[0-9]?', grandson.attrib['href']).group(0)
                        # targetのidの取得
                        if grandson.attrib['role'] == 'target':
                            target_ap = dialogue_id + re.search('.[A-D]', grandson.attrib['href']).group(0) + '.dialog-act.' + re.search(tag[2] + '.[0-9][0-9]?[0-9]?[0-9]?', grandson.attrib['href']).group(0)
                    word_ap_id.append({'source': source_ap, 'target': target_ap, 'ap_id': ap_id, 'ap_tag': ap_tag})

                #print(word_ap_id)
                    
                # エラーチェック
                for dic in word_ar_id:
                    if dic['target'] == '':
                        print(dic)
                    if dic['source'] == '':
                        print(dic)
            word_id2ae_id.append({'word_da_info':word_da_id, 'word_ae_info':word_ae_id, 'word_se_info':word_se_id, 'word_root':word_root, 'speaker_id': speaker_id, 'utterance':utterance})
    return word_id2ae_id, word_ar_id, word_ap_id

def info_utterance(ae_types_list, da_types_list, default_topics_list, word_id2top, word_id2ae_id):
    # segmentの処理きもいから、あとでプログラム変更したい
    
    # 単語情報をutteranceに変更する
    speaker_id2index = {'A': 0, 'B': 1, 'C': 2, 'D': 3}

    #議論要素のidのリスト
    argument_list = []
    
    # セグメントIDのlist
    segmentid_dict = defaultdict(list)
    
    #時間情報を表すもの
    start_time, end_time = {}, {}
    
    # 議論要素の要素,関係を示すもの
    ae_list, ar_link = defaultdict(list), defaultdict(list)

    # 談話行為のタグ,adjancecy pairを表すもの
    da_list, da_link = defaultdict(list), defaultdict(list)

    # トピックタグを表すもの
    top_list = defaultdict(list)
    
    # 対話の発話リスト
    dialogue_list = []

    # セグメントの保管庫
    segment = defaultdict(list)

    # flagを用意
    flag = True
    

    for speaker_word in word_id2ae_id:
        # 出力する発話文の作成
        speaker_id = speaker_word['speaker_id']
        for idx, child in enumerate(speaker_word['word_root']):
            # 単語IDの取得
            word_id = child.attrib['{http://nite.sourceforge.net/}id']
            word_id_num = int(word_id.split('.')[2].replace('words', ''))
            # 談話行為IDと談話行為
            da_id = ''
            da_tag = ''
            da = ''
            # 議論要素IDと議論要素
            ae_id = ''
            ae = ''
            ar_id = ''
            # セグメントID
            se = ''
            # トピックIDとトピック
            main_top_id = ''
            sub_top_id = ''
            main_top = ''
            sub_top = ''
            
            # 対応するae_idがあれば取得
            for el in speaker_word['word_ae_info']:
                if el['word_id_num'] == word_id_num:
                    ae_id = el['ae_id']
                    ar_id = el['ar_link']
                    if el['ar_link'] != '' and el['ar_link'] not in ar_link[ar_id]:
                        ar_link[ar_id].append(el['ar_link'])
                        if (el['ar_link'], speaker_id) not in argument_list:
                            argument_list.append((el['ar_link'], speaker_id))
                            start_time[el['ar_link']] = conv_to_timedelta(child.attrib['starttime'])
                        break

            # ae_listの中にない議論要素なら追加
            if ae_id != '':
                for el in ae_types_list:
                    if el['ID'] == ae_id:
                        ae = el['gloss']
                        break
                if not ae in ae_list[ar_id]:
                    ae_list[ar_id].append(ae)

            #print(ae_list, ae)
            # 対応するsegmentがあれば取得
            for el in speaker_word['word_se_info']:
                if el['word_id_num'] == word_id_num:
                    se = el['se_id']
                if not se in segmentid_dict[ar_id] and el['se_id'] != '':
                    segmentid_dict[ar_id].append(se)
                    break
                
            # 対応するda_idがあれば取得
            for el in speaker_word['word_da_info']:
                if el['word_id_num'] == word_id_num:
                    da_id = el['da_id']
                    if el['da_link'] != '' and el['da_link'] not in da_link[ar_id]:
                        da_link[ar_id].append(el['da_link'])
                    break

                
            # da_listの中にない談話行為なら追加
            if da_id != '':
                for el in da_types_list:
                    if el['ID'] == da_id:
                        da = el['gloss']
                        break
                if not da in da_list[ar_id]:
                    da_list[ar_id].append(da)

            #print(da_list, da)
                    
            # 対応するtopがあれば取得
            for el in word_id2top[speaker_id2index[speaker_word['speaker_id']]]:
                if el['word_id_num'] == word_id_num:
                    main_top_id = el['main_topic_id']
                    sub_top_id = el['sub_topic_id']
                    break

            # top_listの中にないメイントピックなら追加
            if main_top_id != '':
                for el in default_topics_list:
                    if el['ID'] == main_top_id:
                        main_top = el['name']
                        break
                if not main_top in top_list[ar_id]:
                    top_list[ar_id].append(main_top)

            # top_listの中にないサブトピックなら追加
            if sub_top_id != '':
                for el in default_topics_list:
                    if el['ID'] == sub_top_id:
                        sub_top = el['name']
                        break
                if not sub_top in top_list[ar_id]:
                    top_list[ar_id].append(sub_top)

            # 時間情報の取得
            if ar_id != '':
                end_time[ar_id] = conv_to_timedelta(child.attrib['endtime'])

            if child.tag == 'w':
                #print(segment)
                if ar_id != '':
                    if child.text in ['.', ',', '?'] and len(segment[ar_id]) != 0:
                        segment[ar_id][-1] += child.text
                    else:
                        segment[ar_id].append(child.text)

    #print(argument_list)
    for speaker_word in word_id2ae_id:
        # words_id2ae_idのutteranceを抽出
        speaker_id = speaker_word['speaker_id']
        utterance = speaker_word['utterance']
        for ar,si in argument_list:
            if si == speaker_id:
                tmp_utterance = " ".join(segment[ar])
                utterance['ID'] = speaker_id
                utterance['start'] = start_time[ar]
                utterance['end'] = end_time[ar]
                utterance['utterance'] = tmp_utterance
                utterance['ae_list'] = ae_list[ar]
                utterance['ar_link'] = ar_link[ar]
                utterance['da_list'] = da_list[ar]
                utterance['da_link'] = da_link[ar]
                utterance['top_list'] = top_list[ar]
                utterance['segment'] = [se.replace(',', '') for se in segmentid_dict[ar] if se != '']
                dialogue_list.append(utterance)
                utterance = {'ID': speaker_id, 'start': dt.timedelta(seconds = -1), 'end': dt.timedelta(seconds = -1), 'da_list': [], 'da_link': [], 'ae_list': [], 'ar_link': [], 'segment': '', 'top_list': [], 'utterance': '','sentiment':[]}        

                    
    # utteranceの順を時間系列に
    dialogue_list.sort(key = lambda x: x['start'])

    #print(dialogue_list)
    
    return dialogue_list

def add_argument_struct(dialogue_list, ar_types_list, ap_types_list, sentence_ar_id, sentence_ap_id):
    # utteranceに議論関係の情報を加える

    ar = ''
    ap = ''
    re_dialogue_list = []
    
    # 対応するar_idを取得
    for i in range(len(sentence_ar_id)):
        for el in ar_types_list:
            if el['ID'] == sentence_ar_id[i]['ar_id']:
                sentence_ar_id[i]['ar_id'] = el['gloss']

    # 対応するap_idを取得
    for idx in range(len(sentence_ap_id)):
        for el in ap_types_list:
            if el['ID'] == sentence_ap_id[idx]['ap_id']:
                sentence_ap_id[idx]['ap_id'] = el['gloss']
                
    # utteranceにar_idの情報を付与
    for utterance in dialogue_list:
        source_st_tag, target_st_tag = [],[]
        source_ap_tag, target_ap_tag = [],[]
        tmp_ar_id = []
        tmp_ap_id = []
        for el in sentence_ar_id:
            # word_ae_infoで取得した議論関係情報を取得
            tag = el['ar_tag'].split(".")
            # sourceとの比較
            #if utterance['segment'] == 'ES2014c.sync.912':
            #    print(el, utterance['ar_link'])
            if el['source'] in utterance['ar_link']:
                source_st_tag.append('S/' + tag[-1])
                tmp_ar_id.append(el['ar_id'])
            # targetとの比較
            elif el['target'] in utterance['ar_link']:
                target_st_tag.append('T/' + tag[-1] + '/' + el['ar_id'])

        for el in sentence_ap_id:
            # word_da_infoで取得した隣接ペア情報を取得
            tag = el['ap_tag'].split('.')
            # sourceとの比較
            #print(utterance['da_link'])
            if el['source'] in utterance['da_link']:
                source_ap_tag.append('S/'+ tag[-1])
                tmp_ap_id.append(el['ap_id'])
            # targetとの比較
            elif el['target'] in utterance['da_link']:
                target_ap_tag.append('T/' + tag[-1] + '/' + el['ap_id'])
        utterance['source_st_tag'] = source_st_tag
        utterance['target_st_tag'] = target_st_tag
        utterance['source_ap_tag'] = source_ap_tag
        utterance['target_ap_tag'] = target_ap_tag
        re_dialogue_list.append(utterance)
        #print(utterance)
    #print(re_dialogue_list)
    return re_dialogue_list

def info_discussion(dialogue_id, re_dialogue_list):
    # discussion単位で議論要素をまとめる

    discussion = []
    all_discussion_list = []
    # 対応した談話行為ファイルの情報を取得
    dis_tree = ET.parse(ami_corpus_path + 'argumentation/dis/' + dialogue_id + '.discussions.xml')
    dis_root = dis_tree.getroot()

    # segment_id抽出のためのフィルター
    segment_id_filter = dialogue_id + '.sync.[0-9],?[0-9]?[0-9]?[0-9]?'

    # discussion単位でsegmentに分ける
    for child in dis_root:
        ac = []
        segment_id_list = []
        name = child.attrib['name'].replace(' - ','_').replace(' ','_')
        for grandson in child:
            segment_id_list = re.findall(segment_id_filter, grandson.attrib['href'])
            if len(segment_id_list) == 1:
                ac.append(segment_id_list[0].replace(',',''))
            elif len(segment_id_list) == 2:
                start_num = int(segment_id_list[0].split('.')[-1].replace(',',''))
                end_num = int(segment_id_list[1].split('.')[-1].replace(',',''))
                for i in range(start_num, end_num + 1):
                    ac.append(dialogue_id + '.sync.' + str(i))
        discussion.append({'name': name, 'ac': ac})
        #print(ac)

    # discussion単位でutteranceをまとめる
    for dis in discussion:
        discussion_list = []
        for utterance in re_dialogue_list:
            for se in utterance['segment']:
                if se in dis['ac']:
                    #いじったばじょ
                    #if utterance['source_st_tag'] != [] or utterance['target_st_tag'] != []:
                    discussion_list.append(utterance)
                    break
        all_discussion_list.append({'name': dis['name'], 'discussion': discussion_list})
        #for dis in discussion_list:
        #    print(dis['segment'])

    # utteranceの順を時間系列に
    for discussion_list in all_discussion_list:
        discussion_list['discussion'].sort(key = lambda x: x['start'])
    #print(all_discussion_list)

    #for i in all_discussion_list:
    #    for j in i['discussion']:
    #        for l in j['ae_list']:
    #            print(l)

    return all_discussion_list

def add_sentiment(discussion_list):
    corenlp = CorenlpSentiment(dir_path + "/stanford-corenlp-4.5.7/")
    for idx, dialogue_list in enumerate(discussion_list):
        for idx_i, el in enumerate(dialogue_list['discussion']):
            discussion_list[idx]['discussion'][idx_i]['sentiment'] += corenlp.parse(el['utterance']).strip().decode(encoding='utf-8').replace('\n  ',',').split(',')
            
    return discussion_list

def make_corpus(discussion_list,dialogue_name):
    
    for dialogue_list in discussion_list:
        with open( dir_path + '/tmp/' + dialogue_name + '_' + dialogue_list['name'] + '.txt', 'w') as f:

            # マイクロ秒を整形して出力
            for el in dialogue_list['discussion']:
                if el['start'].microseconds == 0 and el['end'].microseconds == 0:
                    f.write('{0};{1}'.format(el['ID'], el['start']) + '.000000' + ';{0}'.format(el['end']) + '.000000' + ';{0};{1};{2};{3};{4};{5};{6}\n'.format(el['utterance'], ','.join(sorted(el['top_list'])), ','.join(sorted(el['da_list'])), ','.join(el['sentiment']), ','.join(el['ae_list']), ','.join(el['source_st_tag']), ','.join(el['target_st_tag'])))
                elif el['start'].microseconds == 0:
                    f.write('{0};{1}'.format(el['ID'], el['start']) + '.000000' + ';{0};{1};{2};{3};{4};{5};{6};{7}\n'.format(el['end'], el['utterance'], ','.join(sorted(el['top_list'])), ','.join(sorted(el['da_list'])), ','.join(el['sentiment']), ','.join(el['ae_list']), ','.join(el['source_st_tag']), ','.join(el['target_st_tag'])))
                elif el['end'].microseconds == 0:
                    f.write('{0};{1};{2}'.format(el['ID'], el['start'], el['end']) + '.000000' + ';{0};{1};{2};{3};{4};{5};{6}\n'.format(el['utterance'], ','.join(sorted(el['top_list'])), ','.join(el['da_list']), ','. join(el['sentiment']), ','.join(el['ae_list']), ','.join(el['source_st_tag']), ','.join(el['target_st_tag'])))
                else:
                    f.write('{0};{1};{2};{3};{4};{5};{6};{7};{8};{9}\n'.format(el['ID'], el['start'], el['end'], el['utterance'], ','.join(sorted(el['top_list'])), ','.join(sorted(el['da_list'])), ','.join(el['sentiment']), ','.join(el['ae_list']), ','.join(el['source_st_tag']), ','.join(el['target_st_tag'])))

def main():

    # argument_fileがないもの
    not_ae_list = [['ES2005b','B'],['ES2016a','D'],['TS3007a','C'],['IS1001a','D']]

    # 対話ID
    f_id = file_id()

    # 談話行為,隣接ペア,議論要素,議論関係、Topicのタグ情報の取得
    da_types_list = get_discourse_act()
    ap_types_list = get_adjancecy_pair()
    ae_types_list = get_argument_elements()
    ar_types_list = get_argument_relations()
    defalut_topics_list = get_topics()

    # 発話時間と発話文の抽出
    # 対話一つずつに対応
    for dialogue_id in f_id:
        word_id2top = extract_topic(dialogue_id)
        word_id2ae_id, word_ar_id, word_ap_id = extract_words_argument(dialogue_id, not_ae_list)
        
        dialogue_list = info_utterance(ae_types_list,da_types_list,defalut_topics_list,word_id2top,word_id2ae_id)
        
        discussion_list = add_argument_struct(dialogue_list,ar_types_list,ap_types_list,word_ar_id,word_ap_id)

        discussion_list = info_discussion(dialogue_id, discussion_list)
            
        # discussion_list = add_sentiment(discussion_list)
        
        for dis in discussion_list:
            print(len(dis['discussion']))
            
        make_corpus(discussion_list,dialogue_id.split('/')[-1])
        print(dialogue_id.split('/')[-1] + " finish")

if __name__ == "__main__":
    main()
