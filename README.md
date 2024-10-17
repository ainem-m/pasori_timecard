# 勤怠管理システム
非接触型ICカードリーダー[PaSoRi](https://www.sony.co.jp/Products/felica/business/products/reader/comparison.html)を使用して登録した従業員の出勤・退勤を記録し、データベースに保存するアプリです。



## 目次

- [勤怠管理システム](#勤怠管理システム)
  - [目次](#目次)
  - [機能](#機能)
  - [動作環境](#動作環境)
  - [インストール手順](#インストール手順)
    - [使用方法](#使用方法)

## 機能

- ICカードによる出勤・退勤管理
- 出勤・退勤データのCSVファイルへのエクスポート
- （給料計算を実装したい気持ちがあるけれども予定は未定！）
- GUIインターフェースによる簡単な操作
- エラーログの記録機能

## 動作環境
Python: 3.6 以上
**動作確認済OS**:
Windows 11
macOS Sonoma 14.2
Raspberry Pi OS (Bullseye)

## インストール手順
アプリ化して簡単に誰でも使える！ところまで開発するスキルが無く、今のところ自力で環境を構築できる人が対象のプログラムです…。
1. このリポジトリをクローンします。

```bash
   git clone https://github.com/ainem-m/pasori_timecard
   cd pasori_timecard
```

2. 仮想環境を構築し、パッケージをインストールします。
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. PythonからPaSoRiを使えるようにします
[PaSoRiとnfcpyでNFCの中身を覗いてみる #Python - Qiita](https://qiita.com/h_tyokinuhata/items/2733d3c5bc126d5d4445)を参考に、`nfcpy`からPaSoRiを認識させます。
`python -m nfc`を実行して、指示通りのコマンドを入力するのみです。


### 使用方法

1.	(**初回起動時**)従業員リストを作成します。employee_list.txtというファイルをプロジェクトフォルダ内に作成し、以下のように従業員名を記入します。

employee_list.txt:
```
田中 太郎
鈴木 花子
```

2.	仮想環境を立ち上げます。
```bash
source venv/bin/activate
```

3.	初回起動時にデータベースを初期化します。employee_list.txtに書かれた従業員が自動的にデータベースに登録されます。

```bash
python db_alchemy.py
```

4.	ICカードを登録します（任意のステップです）。未登録のICカードをかざした場合、GUI上で従業員に紐付けることも可能です。
```bash
python register_ic_card.py
```
5.	アプリケーションを起動します。
```bash
python main.py
```

6.	ICカードをリーダーにかざすと、出勤または退勤の処理が行われます。自動的に出勤か退勤かが判定されますが、間違っている場合は「状態を変更」ボタンを押して修正してください。

7.	勤怠データをCSV形式で出力するには、以下のコマンドを実行します。現在は2024年10月分が出力されるようになっていますが、今後は自動的に出力できるように改善予定です。
```bash
python to_csv.py
```



ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細はLICENSEファイルをご覧ください。
