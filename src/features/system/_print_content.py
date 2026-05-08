import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from configs.paths import CONTENTS_FOLDER

content_filename = sys.argv[1]
if not content_filename:
    print(">>> Error: No content filename provided.")
    sys.exit(1)

help_file = f"{CONTENTS_FOLDER}/{content_filename}"

if __name__ == "__main__":
    try:
        with open(help_file, "r", encoding="utf-8") as f:
            print(f.read())
    except Exception as e:
        print(">>> Error reading help file:", e)
