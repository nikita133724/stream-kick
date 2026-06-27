import os
import socket
import requests
import traceback
from urllib.parse import urlparse
import sys

# Открываем порт для Render
PORT = int(os.getenv("PORT", 10000))

SUPABASE_URL = os.getenv(
    "SUPABASE_URL",
    "https://qzilosvjftximfduneuz.supabase.co"
).strip()

SUPABASE_SERVICE_ROLE_KEY = os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY", 
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF6aWxvc3ZqZnR4aW1mZHVuZXV6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTc1NTQ5NiwiZXhwIjoyMDk1MzMxNDk2fQ.HhuIEi-gz4GinNKlw5p6d8HaeQHdYUFT3Lf1_XR7-GY"
).strip()

SUPABASE_USERS_TABLE = os.getenv("SUPABASE_USERS_TABLE", "users").strip() or "users"


def log(msg):
    print(f"[DEBUG] {msg}", flush=True)


def step(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def run_checks():
    try:
        step("1. ENV CHECK")
        log(f"SUPABASE_URL={repr(SUPABASE_URL)}")
        log(f"KEY EXISTS={bool(SUPABASE_SERVICE_ROLE_KEY)}")
        log(f"TABLE={SUPABASE_USERS_TABLE}")
        log(f"PORT={PORT}")

        step("2. URL PARSE")
        parsed = urlparse(SUPABASE_URL)
        host = parsed.hostname
        log(f"scheme={parsed.scheme}")
        log(f"netloc={parsed.netloc}")
        log(f"host={repr(host)}")

        if not host:
            raise Exception("Host is empty after urlparse")

        step("3. DNS CHECK")
        dns_result = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        for i, item in enumerate(dns_result):
            log(f"DNS[{i}]={item}")

        step("4. TCP CONNECT CHECK")
        sock = socket.create_connection((host, 443), timeout=10)
        log("TCP connection success")
        sock.close()

        step("5. HTTP CHECK")
        r = requests.get(SUPABASE_URL, timeout=15)
        log(f"status={r.status_code}")
        log(f"body={r.text[:500]}")

        step("6. REST API CHECK")
        headers = {
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        }
        api_url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_USERS_TABLE}?select=*&limit=1"
        log(f"API URL={api_url}")
        r = requests.get(api_url, headers=headers, timeout=15)
        log(f"status={r.status_code}")
        log(f"body={r.text[:1000]}")

        step("DONE")
        log("ALL CHECKS PASSED")
        return True
    except Exception as e:
        step("ERROR")
        log(f"TYPE={type(e).__name__}")
        log(f"ERROR={repr(e)}")
        traceback.print_exc()
        return False


def keep_alive():
    # Сначала запускаем проверки
    checks_passed = run_checks()
    
    # Запускаем сервер
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", PORT))
        sock.listen(1)
        log(f"Server listening on port {PORT}")
        log(f"Service is live at https://parserwebsocket.onrender.com")
        
        while True:
            conn, addr = sock.accept()
            try:
                data = conn.recv(1024)
                if data:
                    if checks_passed:
                        response = b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
                        response += b"<h1>All checks passed</h1><p>Supabase connection successful</p>"
                    else:
                        response = b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
                        response += b"<h1>Some checks failed</h1><p>Check logs for details</p>"
                    conn.send(response)
            except Exception as e:
                log(f"Connection error: {e}")
            finally:
                conn.close()
    except Exception as e:
        log(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    keep_alive()
