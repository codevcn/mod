import os
import sys
from pathlib import Path
import argparse

# Cấu hình UTF-8 cho Windows Console
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

MAX_DEPTH: int = 5
THRESHOLD: int = 50  # max
PREVIEW_COUNT: int = 3


def safe_iterdir(path: Path):
    try:
        return list(path.iterdir())
    except PermissionError:
        return None
    except OSError:
        return None


def print_tree(
    folder_path: Path,
    prefix: str = "",
    max_depth: int = MAX_DEPTH,
    current_depth: int = 0,
    threshold: int = THRESHOLD,
    preview_count: int = PREVIEW_COUNT,
):
    if current_depth >= max_depth:
        return

    children = safe_iterdir(folder_path)

    if children is None:
        print(prefix + "└── [Cannot access]")
        return

    folders = sorted(
        [item for item in children if item.is_dir()], key=lambda item: item.name.lower()
    )

    files = sorted(
        [item for item in children if item.is_file()],
        key=lambda item: item.name.lower(),
    )

    visible_items = []

    if len(folders) > threshold:
        visible_items.extend(folders[:preview_count])
        visible_items.append(
            {
                "type": "message",
                "text": f"{len(folders) - preview_count}+ folders more...",
            }
        )
    else:
        visible_items.extend(folders)

    if len(files) > threshold:
        visible_items.extend(files[:preview_count])
        visible_items.append(
            {"type": "message", "text": f"{len(files) - preview_count}+ files more..."}
        )
    else:
        visible_items.extend(files)

    for index, item in enumerate(visible_items):
        is_last = index == len(visible_items) - 1
        connector = "└── " if is_last else "├── "

        if isinstance(item, dict):
            print(prefix + connector + item["text"])
            continue

        print(prefix + connector + item.name)

        if item.is_dir():
            extension = "    " if is_last else "│   "
            print_tree(
                item,
                prefix=prefix + extension,
                max_depth=max_depth,
                current_depth=current_depth + 1,
                threshold=threshold,
                preview_count=preview_count,
            )


def main():
    parser = argparse.ArgumentParser(
        description="Print folder tree with auto-collapse for large folders and level depth control."
    )

    parser.add_argument(
        "folder_path",
        nargs="?",
        default=".",
        help="Folder path. Can be relative or absolute. Default: current terminal folder.",
    )

    parser.add_argument(
        "--level",
        "-l",
        type=str,
        default="deep",
        help="Folder tree depth level (1, 2, 3... or 'deep'). Default: 'deep'.",
    )

    parser.add_argument(
        "--max",
        type=int,
        default=50,
        help="Collapse files/folders if count is greater than this. Default: 50.",
    )

    args = parser.parse_args()

    # Xử lý cờ --level
    level_raw = str(args.level).strip().lower()
    if level_raw == "deep":
        max_depth = MAX_DEPTH
    else:
        try:
            max_depth = int(level_raw)
            if max_depth < 1:
                print("Error: --level must be a positive integer (>= 1) or 'deep'")
                sys.exit(1)
        except ValueError:
            print(f"Error: Invalid --level value '{args.level}'. Must be a positive integer or 'deep'")
            sys.exit(1)

    folder_path = Path(args.folder_path).expanduser().resolve()

    if args.max < 1:
        print("Error: --max must be greater than or equal to 1")
        sys.exit(1)

    if not folder_path.exists():
        print(f"Error: path does not exist: {folder_path}")
        sys.exit(1)

    if not folder_path.is_dir():
        print(f"Error: path is not a folder: {folder_path}")
        sys.exit(1)

    print(str(folder_path))
    print_tree(
        folder_path,
        max_depth=max_depth,
        threshold=args.max,
    )


if __name__ == "__main__":
    main()
