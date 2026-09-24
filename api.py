from flask import Flask, request, jsonify
import requests
import os
import re
import time

app = Flask(__name__)

# ==========================================
# BASE COOKIES (fallback)
# ==========================================
BASE_COOKIES = {
    'region': 'ME',
    'language': 'ar',
    'source': 'pc',
}

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
# COOKIE CACHE (auto refresh)
# ==========================================
_cookie_cache = {
    "cookies": None,
    "last_updated": 0
}

COOKIE_TTL = 600  # 10 minutes


def fetch_fresh_cookies():
    """
    Shop2Game homepage hit karke fresh cookies + datadome token nikalta hai
    """
    session = requests.Session()
    session.headers.update({
        'User-Agent': HEADERS['User-Agent'],
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Upgrade-Insecure-Requests': '1',
    })

    try:
        # Step 1: Homepage visit -> cookies set
        r = session.get('https://shop2game.com/', timeout=15)
        if r.status_code != 200:
            return None

        # Step 2: Datadome token nikalo
        datadome = session.cookies.get('datadome', '')

        cookies = {
            'region': 'ME',
            'language': 'ar',
            'source': 'pc',
        }

        # Session se jo bhi cookies mili, sab add karo
        for c in session.cookies:
            cookies[c.name] = c.value

        if datadome:
            cookies['datadome'] = datadome

        return cookies

    except Exception:
        return None


def get_cookies():
    """
    Cached cookies return karta hai, expire hone par refresh
    """
    now = time.time()
    if _cookie_cache["cookies"] is None or (now - _cookie_cache["last_updated"]) > COOKIE_TTL:
        fresh = fetch_fresh_cookies()
        if fresh:
            _cookie_cache["cookies"] = fresh
            _cookie_cache["last_updated"] = now
    return _cookie_cache["cookies"] or BASE_COOKIES


# ==========================================
# PLAYER INFO
# ==========================================
def get_player_info(uid: str):
    url = 'https://shop2game.com/api/auth/player_id_login'
    payload = {"app_id": 100067, "login_id": uid}

    # 2 attempts: pehle cached, phir fresh cookies
    for attempt in range(2):
        cookies = get_cookies()

        headers = HEADERS.copy()
        if 'datadome' in cookies:
            headers['x-datadome-clientid'] = cookies['datadome']

        try:
            res = requests.post(
                url, json=payload, headers=headers,
                cookies=cookies, timeout=15
            )
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {e}"}

        # 403 aaya -> cookies refresh karo aur retry
        if res.status_code == 403 and attempt == 0:
            _cookie_cache["last_updated"] = 0  # force refresh
            continue

        if res.status_code != 200:
            return {"error": f"HTTP {res.status_code}"}

        try:
            data = res.json()
        except ValueError:
            return {"error": "Invalid JSON response"}

        if not data.get('nickname'):
            return {"error": "ID NOT FOUND"}

        return {
            "uid": uid,
            "open_id": data.get("open_id"),
            "nickname": data.get("nickname"),
            "region": data.get("region"),
        }

    return {"error": "HTTP 403 (cookies blocked)"}


# ==========================================
# ROUTES
# ==========================================
@app.route('/FRUXREGIONCHECKER', methods=['GET'])
def player():
    uid = request.args.get('uid', '').strip()
    if not uid.isdigit():
        return jsonify({"error": "Valid numeric UID required"}), 400

    result = get_player_info(uid)
    status = 200 if "error" not in result else 404
    return jsonify(result), status


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "API is live ✅",
        "endpoint": "/FRUXREGIONCHECKER?uid=YOUR_UID",
        "example": "/FRUXREGIONCHECKER?uid=7021709939"
    })


# ==========================================
# RUN
# ==========================================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)    try:
        res = requests.post(url, json=payload, headers=HEADERS,
                            cookies=COOKIES, timeout=15)
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {e}"}

    if res.status_code != 200:
        return {"error": f"HTTP {res.status_code}"}

    try:
        data = res.json()
    except ValueError:
        return {"error": "Invalid JSON response"}

    if not data.get('nickname'):
        return {"error": "ID NOT FOUND"}

    return {
        "uid": uid,
        "open_id": data.get("open_id"),
        "nickname": data.get("nickname"),
        "region": data.get("region"),
    }


@app.route('/FRUXREGIONCHECKER', methods=['GET'])
def player():
    uid = request.args.get('uid', '').strip()
    if not uid.isdigit():
        return jsonify({"error": "Valid numeric UID required"}), 400

    result = get_player_info(uid)
    status = 200 if "error" not in result else 404
    return jsonify(result), status


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "API is live",
        "endpoint": "/FRUXREGIONCHECKER?uid=YOUR_UID"
    })


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
