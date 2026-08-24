import subprocess

def request_permissions():
    result = subprocess.run(
        ["osascript", "-e", 'tell application "Notes" to get name of every note'],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print("Permission denied. Please allow access to Notes in System Settings → Privacy & Security → Automation")
        raise SystemExit(1)