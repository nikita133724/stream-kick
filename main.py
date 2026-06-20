from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from curl_cffi import requests
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "accept": "application/json",
}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Исправленный синтаксис передачи контекста в шаблон
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"playback_url": None, "error_msg": None, "username": ""}
    )

@app.post("/", response_class=HTMLResponse)
async def get_stream(request: Request, username: str = Form(...)):
    username = username.strip().lower()
    playback_url = None
    error_msg = None

    if username:
        try:
            url = f"https://kick.com/api/v2/channels/{username}"
            response = requests.get(url, headers=HEADERS, impersonate="chrome", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("livestream") is not None and data.get("playback_url"):
                    playback_url = data.get("playback_url")
                else:
                    error_msg = f"Стример {username} сейчас оффлайн."
            elif response.status_code == 404:
                error_msg = f"Канал {username} не найден."
            else:
                error_msg = f"Ошибка Kick API (Код: {response.status_code})"
        except Exception as e:
            error_msg = f"Ошибка сервера: {str(e)}"

    # Здесь синтаксис тоже исправлен
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={
            "playback_url": playback_url, 
            "error_msg": error_msg, 
            "username": username
        }
    )

@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main.py:app", host="0.0.0.0", port=port, reload=False)
