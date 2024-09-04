class Meeting:
    def __init__(self, record):
        self.name = self.extract_name(record)
        self.attributes = self.extract_attributes(record)

    def extract_name(self, record):
        # record の最初の7文字が名前とされている
        return record[0:7]

    def extract_attributes(self, record):
        attribute_names = [
            "abstractive", "headGesture", "focus", "segments", "words",
            "youUsages", "participantRoles", "disfluency", "movement",
            "handGesture", "participantSummaries", "decision", "topics",
            "argumentation", "dialogueActs", "namedEntities", "extractive"
        ]

        attributes = {}
        for i, attribute in enumerate(attribute_names):
            # 各属性の範囲は 4 文字ずつずれているので、範囲を計算
            start = 8 + i * 4
            end = start + 4
            attributes[attribute] = 'X' in record[start:end]
        
        return attributes

      
    def has_topics_and_argumentation(self):
        return self.attributes["topics"] and self.attributes["argumentation"]
