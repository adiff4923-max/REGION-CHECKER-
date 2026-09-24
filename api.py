from flask import Flask, request, jsonify
import requests
import os
import time
import random

app = Flask(__name__)

# ==========================================
# SCRAPERAPI KEY (optional — https://scraperapi.com se free lo)
# ==========================================
SCRAPERAPI_KEY = os.environ.get("SCRAPERAPI_KEY", "")  # Render env var me daalo

HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Content-Type': 'application/json',
    'Origin': 'https://shop2game.com',
    'Referer': 'https://shop2game.com/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
}

# ==========================================
# FREE PROXY LIST
# ==========================================
PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
]

_proxy_cache = {"list": [], "last_updated": 0}
PROXY_TTL = 300


def load_proxies():
    now = time.time()
    if _proxy_cache["list"] and (now - _proxy_cache["last_updated"]) < PROXY_TTL:
        return _proxy_cache["list"]

    proxies = []
    for url in PROXY_SOURCES:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                for line in r.text.strip().split('\n'):
                    line = line.strip()
                    if line and ':' in line and not line.startswith('#'):
                        proxies.append(f"http://{line}")
        except Exception:
            continue

    # dedupe
    proxies = list(set(proxies))
    _proxy_cache["list"] = proxies
    _proxy_cache["last_updated"] = now
    return proxies


# ==========================================
# SCRAPERAPI METHOD
# ==========================================
def try_scraperapi(uid: str, region: str):
    if not SCRAPERAPI_KEY:
        return None

    target = "https://shop2game.com/api/auth/player_id_login"
    try:
        res = requests.post(
            "https://api.scraperapi.com/",
            params={
                "api_key": SCRAPERAPI_KEY,
                "url": target,
                "method": "POST",
                "keep_headers": "true",
            },
            json={"app_id": 100067, "login_id": uid},
            headers={
                **HEADERS,
                "x-datadome-clientid": "",
                "Cookie": f"region={region}; language=ar; source=pc",
            },
            timeout=60
        )
        if res.status_code != 200:
            return None
        data = res.json()
        if not data.get('nickname'):
            return {"error": "ID NOT FOUND"}
        return {
            "uid": uid,
            "open_id": data.get("open_id"),
            "nickname": data.get("nickname"),
            "region": region,
        }
    except Exception:
        return None


# ==========================================
# DIRECT + PROXY METHOD
# ==========================================
def try_direct_or_proxy(uid: str, region: str, proxy=None):
    session = requests.Session()
    session.headers.update({
        'User-Agent': HEADERS['User-Agent'],
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })

    proxy_dict = {"http": proxy, "https": proxy} if proxy else None

    try:
        session.get('https://shop2game.com/', timeout=10, proxies=proxy_dict)
    except Exception:
        return None

    cookies = {'region': region, 'language': 'ar', 'source': 'pc'}
    for c in session.cookies:
        cookies[c.name] = c.value

    headers = HEADERS.copy()
    if 'datadome' in cookies:
        headers['x-datadome-clientid'] = cookies['datadome']

    try:
        res = requests.post(
            'https://shop2game.com/api/auth/player_id_login',
            json={"app_id": 100067, "login_id": uid},
            headers=headers, cookies=cookies, timeout=15,
            proxies=proxy_dict
        )
    except Exception:
        return None

    if res.status_code != 200:
        return None

    try:
        data = res.json()
    except ValueError:
        return None

    if not data.get('nickname'):
        return {"error": "ID NOT FOUND"}

    return {
        "uid": uid,
        "open_id": data.get("open_id"),
        "nickname": data.get("nickname"),
        "region": region,
    }


# ==========================================
# MAIN LOGIC
# ==========================================
def get_player_info(uid: str, region: str):
    # 1. ScraperAPI try karo (agar key hai)
    if SCRAPERAPI_KEY:
        result = try_scraperapi(uid, region)
        if result and "error" not in result:
            return result

    # 2. Direct try
    result = try_direct_or_proxy(uid, region, proxy=None)
    if result and "error" not in result:
        return result

    # 3. Proxies try karo
    proxies = load_proxies()
    random.shuffle(proxies)
    for proxy in proxies[:15]:  # top 15 proxies
        result = try_direct_or_proxy(uid, region, proxy=proxy)
        if result and "error" not in result:
            return result

    return {"error": "HTTP 403 - All attempts blocked (DataDome). Add SCRAPERAPI_KEY env var for 100% success."}


# ==========================================
# ROUTES
# ==========================================
@app.route('/FRUXREGIONCHECKER', methods=['GET'])
def player():
    uid = request.args.get('uid', '').strip()
    region = request.args.get('region', 'ME').strip().upper()

    if not uid.isdigit():
        return jsonify({"error": "Valid numeric UID required"}), 400

    result = get_player_info(uid, region)
    status = 200 if "error" not in result else 404
    return jsonify(result), status


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "API is live",
        "endpoint": "/FRUXREGIONCHECKER?uid=YOUR_UID&region=ME",
        "scraperapi": "enabled" if SCRAPERAPI_KEY else "disabled (add SCRAPERAPI_KEY env var)"
    })


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)