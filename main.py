from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# ==============================
# COOKIES (session expire hone par update karna)
# ==============================
COOKIES = {
    'region': 'ME',
    'language': 'ar',
    'mspid2': '1ce8d36295b60f00bc2e0ca345f097b0',
    'datadome': 'cLh_OAsqsjV2cV~CNAjieggs77D~QoBHU~mFLpmwMOgFCjPOFgUCkiVeL4Fvn26c1ATYDIczOTOsyzmpiZBXYbMV8lfrOe3wIGbY2kSCrdOoQPr4gDeWoNkrKaPRCe3e',
    '_ga': 'GA1.1.796930145.1789732102',
    '_fbp': 'fb.1.1789732108797.884114406992409680',
    'source': 'pc',
    'GOP': 'f160859b812a54e9bcef25cba26c66af',
    'session_key': 'ilclab9ubo8ugqprlr231ofsp239ya8d',
}

# ==============================
# HEADERS
# ==============================
HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Content-Type': 'application/json',
    'Origin': 'https://shop2game.com',
    'Referer': 'https://shop2game.com/?channel=230199&item=26781',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0',
    'x-datadome-clientid': COOKIES['datadome'],
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
}


# ==============================
# PLAYER INFO FETCH FUNCTION
# ==============================
def get_player_info(uid: str):
    url = 'https://shop2game.com/api/auth/player_id_login'
    payload = {"app_id": 100067, "login_id": uid}

    try:
        res = requests.post(
            url,
            json=payload,
            headers=HEADERS,
            cookies=COOKIES,
            timeout=15
        )
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


# ==============================
# MAIN ROUTE: /FRUXREGIONCHECKER
# ==============================
@app.route('/FRUXREGIONCHECKER', methods=['GET'])
def player():
    uid = request.args.get('uid', '').strip()

    if not uid.isdigit():
        return jsonify({"error": "Valid numeric UID required"}), 400

    result = get_player_info(uid)
    status = 200 if "error" not in result else 404
    return jsonify(result), status


# ==============================
# HOME ROUTE (health check)
# ==============================
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "API is live ✅",
        "endpoint": "/FRUXREGIONCHECKER?uid=YOUR_UID",
        "example": "/FRUXREGIONCHECKER?uid=7021709939"
    })


# ==============================
# RUN APP
# ==============================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)