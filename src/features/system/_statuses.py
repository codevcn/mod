import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from configs.paths import CONTENTS_FOLDER

statuses_file = rf"{CONTENTS_FOLDER}/statuses.txt"

if __name__ == "__main__":
    try:
        with open(statuses_file, "r", encoding="utf-8") as f:
            print(f.read())
    except Exception as e:
        print(">>> Error reading statuses file:", e)
