import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs.paths import CONTENTS_FOLDER

curl_file = f"{CONTENTS_FOLDER}/cURL.txt"

if __name__ == "__main__":
    try:
        with open(curl_file, "r", encoding="utf-8") as f:
            print(f.read())
    except Exception as e:
        print(">>> Error reading cURL file:", e)
