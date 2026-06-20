from flask import Flask, render_template, request, jsonify
from curl_cffi import requests

app = Flask(__name__)

HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "accept": "application/json",
}

@app.route('/', methods=['GET', 'POST'])
def index():
    playback_url = None
    error_msg = None
    username = ""

    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        if username:
            try:
                # Дергаем API кика через curl_cffi, обходя Cloudflare
                url = f"https://kick.com/api/v2/channels/{username}"
                response = requests.get(url, headers=HEADERS, impersonate="chrome", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    # Проверяем, идет ли livestream прямо сейчас
                    if data.get("livestream") is not None and data.get("playback_url"):
                        playback_url = data.get("playback_url")
                    else:
                        error_msg = f"Стример {username} сейчас оффлайн."
                elif response.status_code == 404:
                    error_msg = f"Канал {username} не найден на Kick."
                else:
                    error_msg = f"Ошибка Kick API (Код: {response.status_code})"
            except Exception as e:
                error_msg = f"Ошибка сервера: {str(e)}"

    return render_template('index.html', playback_url=playback_url, error_msg=error_msg, username=username)

if __name__ == '__main__':
    # Render передает порт через переменную окружения
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
