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



def get_meeting_ids_with_topics_and_argumentation():
  
  with open(manifest_path, 'r') as f: 
    records = f.readlines()
    
  del records[0:18]

  meetings = [Meeting(record) for record in records]
  meetings_to_use = [meeting for meeting in meetings if meeting.has_topics_and_argumentation()]
  meeting_ids = [meeting.name for meeting in meetings_to_use]
  
  return meeting_ids

if __name__ == "__main__":
  
    # argument_fileがないもの
    not_ae_list = [['ES2005b','B'],['ES2016a','D'],['TS3007a','C'],['IS1001a','D']]
    
    # 対話ID
    meetting_ids = get_meeting_ids_with_topics_and_argumentation()
    print(meetting_ids)
    
