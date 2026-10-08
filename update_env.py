import requests
import sys
import re

def get_ngrok_url():
    """Ask Ngrok's local API for the current public URL."""
    try:
        response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=5)
        data = response.json()
        for tunnel in data["tunnels"]:
            if tunnel["proto"] == "https":
                return tunnel["public_url"]
        return None
    except Exception as e:
        print(f"[!] Could not reach Ngrok API: {e}")
        return None

def update_env_file(url):
    """Rewrite the CALLBACK_URL line in .env."""
    try:
        with open(".env", "r") as f:
            content = f.read()
    except FileNotFoundError:
        print("[!] .env file not found.")
        return False

    new_line = f"CALLBACK_URL={url}/callback"
    if re.search(r"^CALLBACK_URL=.*$", content, flags=re.MULTILINE):
        content = re.sub(r"^CALLBACK_URL=.*$", new_line, content, flags=re.MULTILINE)
    else:
        content += f"\n{new_line}\n"

    with open(".env", "w") as f:
        f.write(content)

    return True

def main():
    url = get_ngrok_url()
    if not url:
        print("[!] No HTTPS tunnel found. Is Ngrok running and authenticated?")
        sys.exit(1)

    print(f"[+] Ngrok URL: {url}")
    if not update_env_file(url):
        sys.exit(1)

    print("[+] .env updated successfully.")

if __name__ == "__main__":
    main()
