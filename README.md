# 勤怠管理システム
非接触型ICカードリーダー[PaSoRi](https://www.sony.co.jp/Products/felica/business/products/reader/comparison.html)を使用して登録した従業員の出勤・退勤を記録し、データベースに保存するアプリです。



## 目次

- [勤怠管理システム](#勤怠管理システム)
  - [目次](#目次)
  - [機能](#機能)
  - [動作環境](#動作環境)
  - [インストール手順](#インストール手順)

## 機能

- ICカードによる出勤・退勤管理
- 出勤・退勤データのCSVファイルへのエクスポート
- （給料計算を実装したい気持ちがあるけれども予定は未定！）
- GUIインターフェースによる簡単な操作
- エラーログの記録機能

## 動作環境

	•	Python: 3.6 以上
	**動作確認済OS**:
	•	Windows 11
	•	macOS Sonoma 14.2
	•	Raspberry Pi OS (Bullseye)

## インストール手順
アプリ化して簡単に誰でも使える！ところまで開発するスキルが無く、今のところ自力で環境を構築できる人が対象のプログラムです…。
1. このリポジトリをクローンします。

```bash
   git clone https://github.com/ainem-m/pasori_timecard
   cd pasori_timecard```

2. 仮想環境を構築し、パッケージをインストールします。
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt```

3. PythonからPaSoRiを使えるようにします
[PaSoRiとnfcpyでNFCの中身を覗いてみる #Python - Qiita](https://qiita.com/h_tyokinuhata/items/2733d3c5bc126d5d4445)を参考に、`nfcpy`からPaSoRiを認識させます。
`python -m nfc`を実行して、指示通りのコマンドを入力するのみです。

使用方法

	1.	仮想環境内でアプリケーションを起動します。
```bash
source venv/bin/activate
python main.py
```

	2.	ICカードをリーダーにかざすと、出勤または退勤の処理が行われます。自動的に出勤か退勤か判定されますが、間違っている場合`状態を変更`ボタンを押して変更してください。
	3.	勤怠データをCSV形式で出力するには、`python to_csv.py`で出力されます、現状2024年10月分が出力されるようになっていますが、今後自動的に出力できるように改良予定です。


ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細はLICENSEファイルをご覧ください。
