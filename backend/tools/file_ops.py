import os

def get_logs_dir():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    logs_dir = os.path.join(base_dir, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir

def write_log(scan_id, content):
    logs_dir = get_logs_dir()
    with open(os.path.join(logs_dir, f"{scan_id}.txt"), "w", encoding="utf-8") as f:
        f.write(content)

def write_patch(filename, content):
    logs_dir = get_logs_dir()
    patches_dir = os.path.join(logs_dir, "patches")
    os.makedirs(patches_dir, exist_ok=True)
    with open(os.path.join(patches_dir, filename), "w", encoding="utf-8") as f:
        f.write(content)
