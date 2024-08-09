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
