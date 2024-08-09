# モジュール読み込み
import MakeLeapsApiMod as mlmod
from datetime import datetime, timezone, timedelta

# 設定ファイルから設定情報を読み込み
configData = mlmod.readConfigIni('MakeLeaps.ini')

# アーカイブした取引先の表示
archivedClientList = mlmod.getArchivedClient(configData)
for archivedClient in archivedClientList:
    print('外部ID : ' + archivedClient['client_external_id'])
    print('表示名 : ' + archivedClient['display_name'])
    datetimeStr = archivedClient['date_archived']
    jst = timezone(timedelta(hours=9), 'JST')
    dt = datetime.strptime(datetimeStr,'%Y-%m-%dT%H:%M:%S.%f%z')
    jstDatetimeStr = dt.astimezone(jst).strftime('%Y-%m-%d %H:%M:%S')
    print('アーカイブ日 : ' + jstDatetimeStr)
