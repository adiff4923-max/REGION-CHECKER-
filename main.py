from flask import Flask, request, jsonify
import requests
import os
import traceback

app = Flask(__name__)

HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Content-Type': 'application/json',
    'Origin': 'https://shop2game.com',
    'Referer': 'https://shop2game.com/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0',
}

# Ye saare regions try karega (India pehle)
ALL_REGIONS = ['IND', 'ME', 'BR', 'SG', 'ID', 'TH', 'VN', 'RU', 'PK', 'BD']


def try_region(uid: str, region: str):
    """Ek region me try karta hai. Return: dict ya None"""
    try:
        cookies = {
            'region': region,
            'language': 'en',
            'source': 'pc',
        }

        res = requests.post(
            'https://shop2game.com/api/auth/player_id_login',
            json={"app_id": 100067, "login_id": uid},
            headers=HEADERS,
            cookies=cookies,
            timeout=15
        )

        if res.status_code != 200:
            return None

        data = res.json()

        if data.get('nickname'):
            return {
                "uid": uid,
                "open_id": data.get("open_id"),
                "nickname": data.get("nickname"),
                "region": region
            }
        return None

    except Exception:
        return None


@app.route('/FRUXREGIONCHECKER', methods=['GET'])
def player():
    try:
        uid = request.args.get('uid', '').strip()

        if not uid.isdigit():
            return jsonify({"error": "Valid numeric UID required"}), 400

        # Saare regions me try karo, jisme mile wahi return karo
        for region in ALL_REGIONS:
            result = try_region(uid, region)
            if result:
                return jsonify(result), 200

        # Kahin nahi mila
        return jsonify({
            "error": "ID NOT FOUND in any region",
            "uid": uid,
            "regions_tried": ALL_REGIONS
        }), 404

    except Exception as e:
        return jsonify({
            "error": "Server error",
            "details": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "API is live",
        "endpoint": "/FRUXREGIONCHECKER?uid=YOUR_UID",
        "example": "/FRUXREGIONCHECKER?uid=7021709939"
    })


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)