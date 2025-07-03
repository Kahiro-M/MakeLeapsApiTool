# モジュール読み込み
import MakeLeapsApiMod as mlmod
from datetime import datetime, timezone, timedelta
import csv

jst = timezone(timedelta(hours=9), 'JST')

# 設定ファイルから設定情報を読み込み
configData = mlmod.readConfigIni('MakeLeaps.ini')

print('====== MakeLeaps 請求書情報取得 ======')
print('v.1.0.0')

print('------ 請求書発行日 範囲指定 ------')
dateInBegin = input('いつから(YYYYMMDD) :')
dateInEnd = input('いつまで(YYYYMMDD) :')
mode = input('モード(0:simple,1:detail) :')

if(int(dateInEnd)>int(dateInEnd)):
    dateBegin = dateInEnd
    dateEnd = dateInBegin
else:
    dateBegin = dateInBegin
    dateEnd = dateInEnd

print(f'請求書発行日指定:{dateBegin} - {dateEnd}')

# 書類参照リンクのクリックされた情報を取得
print(f'------ 請求書情報取得 開始 {datetime.now()} ------')
documentClickedDateList = mlmod.getDocumentClickedDate(configData,dateBegin,dateEnd,mode)
print(f'------ 請求書情報取得 終了 {datetime.now()} ------')

# 書き出し
with open('invoice_result.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerows(documentClickedDateList)


# # アーカイブした取引先の表示
# archivedClientList = mlmod.getArchivedClient(configData)
# for archivedClient in archivedClientList:
#     print('外部ID : ' + archivedClient['client_external_id'])
#     print('表示名 : ' + archivedClient['display_name'])
#     datetimeStr = archivedClient['date_archived']
#     dt = datetime.strptime(datetimeStr,'%Y-%m-%dT%H:%M:%S.%f%z')
#     jstDatetimeStr = dt.astimezone(jst).strftime('%Y-%m-%d %H:%M:%S')
#     print('アーカイブ日 : ' + jstDatetimeStr)

