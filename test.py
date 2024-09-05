import stanza

# モデルのダウンロード（初回のみ必要）
stanza.download('en')  # 英語の場合

# パイプラインの初期化
nlp = stanza.Pipeline('en')

# テキストを処理
doc = nlp("Stanford CoreNLP is a great tool!")

# 解析結果の表示
for sentence in doc.sentences:
    for word in sentence.words:
        print(f'{word.text}\t{word.lemma}\t{word.pos}')
