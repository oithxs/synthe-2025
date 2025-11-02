# synthe-2025
2025年度の北山祭の作品です。
波形編集をメインの機能としていて、MML(簡易的な楽譜データ)を用意すれば編集した波形で音楽を鳴らすことが出来ます。
なお、MMLの編集機能はありません。

## 前提ライブラリ
`libasound2-dev`のインストールが必要です
```
 sudo apt install libasound2-dev
```

## 実行方法
`synthe-2025`ディレクトリ直下で以下のコマンドを実行
```
python3 synthe_ui.py
```