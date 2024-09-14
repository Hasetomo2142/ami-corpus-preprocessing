import csv

class DialogueTurn:
    def __init__(self, ae_id, speaker, start_time, end_time, sentence, source, targets):
        self.ae_id = ae_id
        self.speaker = speaker
        self.start_time = float(start_time)
        self.end_time = float(end_time)
        self.sentence = sentence
        self.source = source
        self.targets = self.parse_targets(targets)
        
    # CSVから情報を取得し、DialogueTurnのリストを返す。
    @staticmethod
    def from_csv(csv_path):
        dialogue_turns = []
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # ヘッダー行をスキップ
            for row in reader:
                if len(row) >= 7:
                    # コンストラクタの順番で変数を格納
                    ae_id = row[0]
                    speaker = row[1]
                    start_time = row[2]
                    end_time = row[3]
                    sentence = row[4]
                    source = row[5]
                    targets = row[6]
                    dialogue_turns.append(DialogueTurn(ae_id, speaker, start_time, end_time, sentence, source, targets))
                else:
                    print(f"行のフォーマットが正しくありません: {row}")
        return dialogue_turns 
      
    def parse_targets(self, targets_str):
        if targets_str == 'None' or not targets_str:
            return []
        else:
            return [t.strip() for t in targets_str.strip('{}').split(',')]
