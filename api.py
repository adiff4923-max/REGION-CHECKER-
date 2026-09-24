from flask import Flask, request, jsonify
import requests
import os
import traceback

app = Flask(__name__)


@app.route('/FRUXREGIONCHECKER', methods=['GET'])
def player():
    try:
        uid = request.args.get('uid', '').strip()
        region = request.args.get('region', 'IND').strip().upper()

        if not uid.isdigit():
            return jsonify({"error": "Valid numeric UID required", "got": uid}), 400

        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/json',
            'Origin': 'https://shop2game.com',
            'Referer': 'https://shop2game.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0',
        }

        cookies = {
            'region': region,
            'language': 'en',
            'source': 'pc',
        }

        res = requests.post(
            'https://shop2game.com/api/auth/player_id_login',
            json={"app_id": 100067, "login_id": uid},
            headers=headers,
            cookies=cookies,
            timeout=20
        )

        # Status code kya aaya, browser me dikhao
        if res.status_code != 200:
            return jsonify({
                "error": f"HTTP {res.status_code}",
                "body": res.text[:500],
                "region_tried": region
            }), 200

        try:
            data = res.json()
        except Exception:
            return jsonify({
                "error": "Not JSON response",
                "body": res.text[:500]
            }), 200

        if not data.get('nickname'):
            return jsonify({
                "error": "ID NOT FOUND",
                "region_tried": region,
                "raw_response": data
            }), 200

        return jsonify({
            "uid": uid,
            "open_id": data.get("open_id"),
            "nickname": data.get("nickname"),
            "region": region,
        }), 200

    except Exception as e:
        # Agar kuch bhi crash ho, yahan pakda jayega
        return jsonify({
            "error": "Server error",
            "details": str(e),
            "traceback": traceback.format_exc()
        }), 200


@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "API is live"})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)