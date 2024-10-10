# raspberry pi と PaSoRiで勤怠管理

## 動機
毎月タイムカードをみてエクセルに手打ちして計算、電卓で検算して…というのが非常に非効率的だと思った

### 代案
[パソコンでタイムレコーダー](http://irtnet.jp/bussiness/timerecorder/)  
3980円　やすい　恐るべし…！

## やりたいこと
- 出勤したときにタイムレコーダーになにかしらをピッとタッチ→打刻できる
- 月末に各従業員の勤務時間を自動計算する


### raspberry pi どれ買う問題

| 項目                             | Raspberry Pi Zero 2 W               | Raspberry Pi 3 Model B+                     | Raspberry Pi Pico W                     |
| -------------------------------- | ----------------------------------- | ------------------------------------------- | --------------------------------------- |
| **プロセッサ**                   | クアッドコア ARM Cortex-A53 @ 1GHz  | クアッドコア ARM Cortex-A53 @ 1.4GHz        | デュアルコア ARM Cortex-M0+ @ 133MHz    |
| **RAM**                          | 512MB LPDDR2                        | 1GB LPDDR2                                  | 264KB SRAM                              |
| **ストレージ**                   | microSD                             | microSD                                     | 2MB オンボード QSPI フラッシュ          |
| **無線接続**                     | 2.4GHz 802.11n Wi-Fi, Bluetooth 4.2 | 2.4/5GHz 802.11ac Wi-Fi, Bluetooth 4.2, BLE | 2.4GHz 802.11n Wi-Fi, Bluetooth 5.2     |
| **イーサネット**                 | なし                                | あり（USB 2.0経由のギガビットイーサネット） | なし                                    |
| **USBポート**                    | 1 x USB 2.0 OTG                     | 4 x USB 2.0                                 | 1 x USB 1.1（ホストとデバイスサポート） |
| **HDMIポート**                   | ミニHDMI                            | フルサイズHDMI                              | なし                                    |
| **GPIOピン**                     | 40                                  | 40                                          | 26                                      |
| **カメラインターフェース**       | CSI-2                               | CSI-2                                       | なし                                    |
| **ディスプレイインターフェース** | DSI                                 | DSI                                         | なし                                    |
| **オーディオ出力**               | HDMI、PWM                           | HDMI、3.5mmジャック                         | なし                                    |
| **サイズ**                       | 65mm x 30mm                         | 85mm x 56mm                                 | 51mm x 21mm                             |
| **価格**                         | 約15ドル                            | 約35ドル                                    | 約6ドル                                 |

### 参考ソース
- [Raspberry Pi Zero 2 W プロダクトページ](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/)
- [Raspberry Pi 3 Model B+ プロダクトページ](https://www.raspberrypi.com/products/raspberry-pi-3-model-b-plus/)
- [Raspberry Pi Pico W ドキュメント](https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html) [oai_citation:1,Raspberry Pi Documentation - Raspberry Pi Pico and Pico W](https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html) [oai_citation:2,Buy a Raspberry Pi Pico – Raspberry Pi](https://www.raspberrypi.com/products/raspberry-pi-pico/) [oai_citation:3,New functionality: Bluetooth for Pico W - Raspberry Pi](https://www.raspberrypi.com/news/new-functionality-bluetooth-for-pico-w/)

picoだとCPUが不安
zero 2がちょうどいいかも

### 値段
micro SD 
PaSoRi 1670円（中古　駿河屋）
zero wh 2970円 + 550円
スクリーン 1843円 https://ja.aliexpress.com/item/1005005926386748.html?spm=a2g0o.order_list.order_list_main.5.21ef585ajaJJdI&gatewayAdapt=glo2jpn
ピンヘッダ 293 + 290円
USBmini to micro ケーブル597円
USB C to micro ケーブル 635円

合計


## はんだ付けした
http://www.lcdwiki.com/3.5inch_RPi_Display#Step_3:_Open_terminal.28SSH.29_and_install_the_driver_on_RaspberryPi
これをみながらディスプレイとの接続を何度も試すものの、うまくいかず…
bookwormという最新のOSではうまくいかないようなので、
bullseyeという型落ちのOSを入れることに

### 起動した
やっと写った
pythonのvenvで仮想環境を立ち上げて
tkinter, kivyあたりのスクリプトを書いて…
あれ映らねぇ！

`export DISPLAY=:0`
したら写った！タッチも反応するしこれで勝つる！！！！


### iphoneへの対応
http://hara-jp.com/_default/ja/Topics/RaspPiCardReader.html
ここをみるとできそう、ここを後で差し替えたいので待ち受けのメソッドはちゃんと切り分ける

## 要件定義


### ユーザー要件
- **従業員**: 出勤・退勤時にICカードをタッチして、システムが自動で時間を記録する。
- **管理者**: ログインが必要。従業員の勤務時間レポートを出力することができる。

### 機能要件
- **ICカードのタッチによる記録**: 時間帯により、画面に出勤か退勤かを設定し、記録したいものが異なる場合、画面をタッチして選択できるようにする。記録後、画面表示で結果のフィードバックを行う。
- **管理機能**: ログインが必要な管理者が勤務時間レポートをCSVで出力することができる。

### 非機能要件
- **セキュリティ**: ICカードデータと出勤退勤記録は暗号化して保存される。
- **パフォーマンス**: タッチした際の処理は0.1秒以内に完了する。
- **可用性**: システムは平日8:00-20:00の間、常に稼働している。１日毎に再起動したい。
- **スケーラビリティ**: ICカードリーダーは一つしか用意できないので、同時にタッチするのは1人のみ。


1.	従業員 (Employee)
	•	employee_id (主キー)
	•	name (氏名)
	•	created_at (従業員登録日)
	•	updated_at (最終更新日)
2.	ICカード (ICCard)
	•	ic_card_id (主キー)
	•	employee_id (外部キー、従業員テーブルへの参照)
	•	ic_card_number (ICカード番号)
	•	created_at (カード登録日)
	•	updated_at (最終更新日)
3.	出勤・退勤記録 (AttendanceRecord)
	•	record_id (主キー)
	•	ic_card_id (外部キー、ICカードテーブルへの参照)
	•	record_type (出勤か退勤かを示す、ENUM: “IN”, “OUT”)
	•	record_time (記録された時刻)
	•	created_at (レコード作成日)
	•	updated_at (レコード更新日)
4.	管理者 (Admin)
	•	admin_id (主キー)
	•	username (ユーザー名)
	•	password_hash (パスワードのハッシュ)
	•	created_at (管理者登録日)
	•	updated_at (最終更新日)
概念データモデル (ER 図)
以下のようなER図を考えます。
[Employee]
-----------------------
| employee_id (PK)    |
| name                |
| created_at          |
| updated_at          |
-----------------------

   |
   | 1:N
   |
   
[ICCard]
-----------------------
| ic_card_id (PK)     |
| employee_id (FK)    |
| ic_card_number      |
| created_at          |
| updated_at          |
-----------------------

   |
   | 1:N
   |
   
[AttendanceRecord]
-----------------------
| record_id (PK)      |
| ic_card_id (FK)    |
| record_type         |
| record_time         |
| created_at          |
| updated_at          |
-----------------------

[Admin]
-----------------------
| admin_id (PK)       |
| username            |
| password_hash       |
| created_at          |
| updated_at          |
-----------------------

### ユースケース

**ユースケース名:** 出勤記録  
**アクター:** 従業員

**基本フロー:**
1. 従業員は、オフィス入り口にあるICカードリーダーにICカードをタッチする。システムは、設定された出勤時刻と退勤時刻に基づき、画面に現在時刻のタッチが出勤と退勤のどちらに該当するかを画面に表示している。
2. システムは、ICカードを読み取り、該当する従業員情報をデータベースから取得する。
3. システムは、設定された出勤時刻と退勤時刻に基づき、タッチされた時刻がどちらに該当するかを自動で判断し、画面に「出勤」または「退勤」を表示する。
4. 従業員は、表示された内容を確認し、必要に応じて画面操作により記録種別を変更する。
   - **改訂:** このステップで、従業員が出勤・退勤の確認を行う際、時間が経過すると自動でデフォルトの選択肢（出勤/退勤）が記録されるようにすることも考慮できます。
5. システムは、従業員が選択した（または自動で判断された）記録種別をデータベースに保存し、「処理が完了しました」と表示する。
   - **追加:** 「処理が完了しました」メッセージとともに、確認番号やタイムスタンプを表示して、従業員が記録を確認できるようにする。

**代替フロー:**
1. もし、ICカードが不正な場合、システムは、「ICカードが不正です。管理者にご連絡ください。」と表示する。
   - **改訂:** この場合、システムは不正ICカードの使用をログに記録し、管理者に自動で通知を送る機能を考慮することもできます。
2. もし、システムに接続できない場合、システムは、「システムエラーが発生しました。ネットワーク接続を確認し、しばらくしてから再度お試しください。」と表示する。
   - **追加:** システムが復旧した際に、バックアップデータやオフラインでのICカードの読み取りを再試行する機能を検討すると良いでしょう。
3. もし、ICカードリーダーに不具合が発生した場合、システムは、「ICカードリーダーに不具合が発生しました。管理者にご連絡ください。」と表示する。
   - **追加:** 代替の入力手段（例：マニュアル入力）の提供を検討することで、出勤・退勤の記録が途絶えないようにすることが可能です。
4. もし、既に当該従業員の記録が存在する場合、システムは、「既に記録済みです」と表示する。
   - **改訂:** この場合、記録済みの内容とタイムスタンプを表示し、従業員が再確認できるようにすると良いです。

### その他

- **事前条件:** 従業員は事前に登録したICカードかiphoneを所持している。従業員とICカードまたはiphoneは1対多の関係で紐づけられている。
- **後条件:** 従業員の出勤/退勤情報がデータベースに記録される。
- **システム応答:** システムは、各ステップにおいて、明確なメッセージを従業員に表示する。

https://touch-sp.hatenablog.com/entry/2024/01/19/185126


```qt.qpa.xcb: could not connect to display 
qt.qpa.plugin: From 6.5.0, xcb-cursor0 or libxcb-cursor0 is needed to load the Qt xcb platform plugin.
qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found.
This application failed to start because no Qt platform plugin could be initialized. Reinstalling the application may fix this problem.

Available platform plugins are: vnc, offscreen, xcb, wayland, minimal, minimalegl, wayland-egl, eglfs, vkkhrdisplay, linuxfb.

Aborted```
これにこまった
```sudo apt install libxcb-cursor0```
しただけでは解決しない
```export DISPLAY:=0```
したら解決
これをvenv/bin/activateに追記すると毎回打たなくてもOK

次は```Traceback (most recent call last):
  File "/home/pi/pasori/nfc_reader_QThread.py", line 33, in run
    with nfc.ContactlessFrontend("usb") as clf:
  File "/home/pi/pasori/venv/lib/python3.9/site-packages/nfc/clf/__init__.py", line 76, in __init__
    raise IOError(errno.ENODEV, os.strerror(errno.ENODEV))
OSError: [Errno 19] No such device```
pasoriを認識できてなかった

```python -m nfc
This is the 1.0.4 version of nfcpy run in Python 3.9.2
on Linux-6.1.21-v8+-aarch64-with-glibc2.31
I'm now searching your system for contactless devices
** found usb:054c:06c3 at usb:001:002 but access is denied
-- the device is owned by 'root' but you are 'pi'
-- also members of the 'root' group would be permitted
-- you could use 'sudo' but this is not recommended
-- better assign the device to the 'plugdev' group
   sudo sh -c 'echo SUBSYSTEM==\"usb\", ACTION==\"add\", ATTRS{idVendor}==\"054c\", ATTRS{idProduct}==\"06c3\", GROUP=\"plugdev\" >> /etc/udev/rules.d/nfcdev.rules'
   sudo udevadm control -R # then re-attach device
I'm not trying serial devices because you haven't told me
-- add the option '--search-tty' to have me looking
-- but beware that this may break other serial devs
Sorry, but I couldn't find any contactless device```

https://cozycozy.xii.jp/rasberry_pi_first_action/