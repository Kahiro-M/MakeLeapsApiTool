# -------------------------------------------------- # 
# MakeLeaps REST API モジュール 
# -------------------------------------------------- #   

# iniファイルから設定を読み込む
def readConfigIni(filePath='MakeLeaps.ini'):
    import configparser

    #ConfigParserオブジェクトを生成
    config = configparser.ConfigParser()

    #設定ファイル読み込み
    config.read(filePath,encoding='utf8')

    #設定情報取得
    if(config.has_option('MakeLeaps','USER_MAKELEAPS_ID')
        and config.has_option('MakeLeaps','CLIENT_ID')
        and config.has_option('MakeLeaps','CLIENT_SECRET')
    ):
        ConfigData = {
            'user_makeleaps_id'   : config.get('MakeLeaps','USER_MAKELEAPS_ID'),
            'client_id'           : config.get('MakeLeaps','CLIENT_ID'),
            'client_secret'       : config.get('MakeLeaps','CLIENT_SECRET'),
        }
        return ConfigData
    else:
        return {'type':'error','hasOptions':config.options(str(appId))}



# アクセスtokenを新規に取得
def getToken(config):
    import requests
    import json

    userMakeleapsId = config['user_makeleaps_id']
    clientId        = config['client_id']
    clientSecret    = config['client_secret']

    # URLを指定してcurl経由でAPIを叩く
    url = 'https://api.makeleaps.com/user/oauth2/token/'

    data = {
        'grant_type': 'client_credentials',
    }

    response = requests.post(url,data=data,auth=(clientId,clientSecret)).json()
    return response['access_token']



# アクセスtokenを新規に取得
def revokeToken(token,config):
    import requests

    clientId        = config['client_id']
    clientSecret    = config['client_secret']

    # URLを指定してcurl経由でAPIを叩く
    url = 'https://api.makeleaps.com/user/oauth2/revoke-token/'

    data = {
        'token': token,
    }

    response = requests.post(url,data=data,auth=(clientId,clientSecret))
    return response.status_code


# アーカイブされた取引先情報を取得
def getArchivedClient(config):
    import requests
    import json

    # token取得
    token = getToken(config)

    userMakeleapsId = config['user_makeleaps_id']

    headers = {
        'Authorization': 'Bearer '+token,
        'Content-Type': 'application/json',
    }

    # 検索条件はアーカイブしているもの
    params = {
        'archived': 'true',
    }

    # URLを指定してcurl経由でAPIを叩く
    url = 'https://api.makeleaps.com/api/partner/'+userMakeleapsId+'/client/?archived=true'
    response = requests.get(url, params=params, headers=headers).json()

    # token破棄
    revokeToken(token,config)

    return response['response']

# Retry-Afterに対応した再試行処理
def getWithRetry(url, params={}, headers={}, maxRetries=5):
    import requests
    import time
    for attempt in range(maxRetries):
        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 200:
            return response.json()  # 成功したらデータを返す

        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            waitTime = int(retry_after) if retry_after and retry_after.isdigit() else 60
            print(f"[{attempt+1}/{maxRetries}] 回試行. {waitTime} 秒後に再試行...")
            time.sleep(waitTime)

        else:
            print(f"[{attempt+1}/{maxRetries}] 回試行が失敗。status {response.status_code}")
            break  # その他のエラーは中断

    raise Exception("Request失敗")

# YYYYMMDD形式の日付文字列から['YYYY-MM-DD']を作成
def getDateList(dateBegin,dateEnd):
    from datetime import datetime, timedelta

    # 文字列を datetime オブジェクトに変換
    startDate = datetime.strptime(dateBegin, "%Y%m%d")
    endDate = datetime.strptime(dateEnd, "%Y%m%d")

    # 日付のリストを作成
    dateList = []
    currentDate = startDate
    while currentDate <= endDate:
        dateList.append(currentDate.strftime("%Y-%m-%d"))
        currentDate += timedelta(days=1)

    return dateList

def getDatetimeJST(utcStr):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    # 複数の可能な形式を順に試す
    parse_formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",  # 小数秒あり
        "%Y-%m-%dT%H:%M:%SZ"      # 小数秒なし
    ]

    for fmt in parse_formats:
        try:
            dtUtc = datetime.strptime(utcStr, fmt)
            dtUtc = dtUtc.replace(tzinfo=ZoneInfo("UTC"))
            break
        except ValueError:
            continue
    else:
        raise ValueError(f"Unsupported datetime format: {utcStr}")

    # 日本時間に変換し、整形
    dtJst = dtUtc.astimezone(ZoneInfo("Asia/Tokyo"))
    return dtJst.strftime("%Y-%m-%d %H:%M:%S")


# 書類参照リンクのクリックされた情報を取得
def getDocumentClickedDate(config,dateBegin,dateEnd,mode='simple'):
    import math
    # csvデータ準備
    csvHeader = [
        '会員番号',
        '取引先名',
        '案件名',
        '文書送信先',
        '文書作成日時',
        '文書送信日時',
        '文書参照日時',
        '文書有効期限',
    ]
    csvData = [csvHeader]

    # mode判定
    modeList = ['0','simple','1','detail']
    if mode.lower() in (m.lower() for m in modeList):
        if(mode == '0'):
            mode = 'simple'
        elif(mode == '1'):
            mode = 'detail'
        else:
            mode = mode.lower()
    else:
        # 合致が無い場合は'simple'固定
        mode = 'simple'

    # token取得
    token = getToken(config)
    userMakeleapsId = config['user_makeleaps_id']
    headers = {
        'Authorization': 'Bearer '+token,
        'Content-Type': 'application/json',
        'X-Api-Version': 'v2023.06.26'
    }

    # 文書検索条件の初期化
    nullParams = {}

    # 件数カウント
    docCount = 0

    # 指定の日付2つから日付リストを取得
    dateList = getDateList(dateBegin,dateEnd)
    for targetDate in dateList:
        # 文書検索条件は指定の作成日、請求書、有効、1ページ100件まで
        docParams = {
            'date': targetDate,
            'document_type': 'invoice',
            'cancelled': False,
            'per_page':100,
        }
        print(f'請求書作成日:{targetDate}')

        # 請求書一覧　URLを指定してcurl経由でAPIを叩く
        dockListUrl = 'https://api.makeleaps.com/api/partner/'+userMakeleapsId+'/document/'
        nextUrl = dockListUrl
        
        printProgressFlg = True
        firstGetDocListFlg = True
        
        # 請求書一覧の{'meta':{'next':'https://api.makeleaps.com/api.....'}}がNoneになるまで
        while nextUrl:
            # 請求書一覧取得
            if(firstGetDocListFlg):
                docListRes = getWithRetry(nextUrl, docParams, headers)
                firstGetDocListFlg = False
            else:
                docListRes = getWithRetry(nextUrl, nullParams, headers)
            nextUrl = docListRes['meta']['next']

            if(printProgressFlg):
                print(f"    対象件数:{docListRes['meta']['count']}")
                print(f"    対象ページ数:{math.ceil(docListRes['meta']['count']/100)}")
                printProgressFlg = False

            if(docCount%100 == 0):
                print(f"        進捗:{docCount}件 取得済み")

            # 請求書一覧の現在のページ
            for docInfo in docListRes['response']:
                # 書き込み用データ初期化
                clinetCode = ''
                clinetName = ''
                docName = ''
                docSendTo = ''
                docCreated = ''
                docSent = ''
                docCliced = ''
                docExpiration = ''

                # 文書情報
                docMid = docInfo['mid']
                docCreated = docInfo['date']
                docSent = getDatetimeJST(docInfo['date_sent'])
                docName = docInfo['project_name']
                clinetName = docInfo['recipient_name']
                
                if(mode == 'detail'):
                    # 取引先情報
                    clientInfoUrl = docInfo['client']
                    clientInfoRes = getWithRetry(clientInfoUrl, nullParams, headers)
                    clinetCode = clientInfoRes['response']['client_external_id']
                    clinetName = clientInfoRes['response']['display_name']

                    # 請求書リンク情報 
                    docLinkInfoUrl = 'https://api.makeleaps.com/api/partner/'+userMakeleapsId+'/document/'+docMid+'/pickup-link/'
                    try:
                        docLinkInfoRes = getWithRetry(docLinkInfoUrl, nullParams, headers)
                    except Exception as e:
                        print("Error:", e)

                    docLinkInfo = docLinkInfoRes['response'][0]

                    docSendTo = docLinkInfo['email']
                    if(docLinkInfo['date_clicked'] == None):
                        docCliced = ''
                    else:
                        docCliced = getDatetimeJST(docLinkInfo['date_clicked'])
                    docExpiration = getDatetimeJST(docLinkInfo['expiration_date'])

                # データ書き込み
                appendData = [
                    clinetCode,
                    clinetName,
                    docName,
                    docSendTo,
                    docCreated,
                    docSent,
                    docCliced,
                    docExpiration,
                ]
                docCount += 1
                csvData.append(appendData)

    # token破棄
    revokeToken(token,config)

    return csvData
