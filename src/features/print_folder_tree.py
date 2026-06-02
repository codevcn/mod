from pathlib import Path
import argparse

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
        description="Print folder tree with auto-collapse for large folders."
    )

    parser.add_argument(
        "folder_path",
        nargs="?",
        default=".",
        help="Folder path. Can be relative or absolute. Default: current terminal folder.",
    )

    parser.add_argument(
        "--max",
        type=int,
        default=50,
        help="Collapse files/folders if count is greater than this. Default: 50.",
    )

    args = parser.parse_args()

    folder_path = Path(args.folder_path).expanduser().resolve()

    if args.max < 1:
        print("Error: --max must be greater than or equal to 1")
        return

    if not folder_path.exists():
        print(f"Error: path does not exist: {folder_path}")
        return

    if not folder_path.is_dir():
        print(f"Error: path is not a folder: {folder_path}")
        return

    print(folder_path.name)
    print_tree(
        folder_path,
        threshold=args.max,
    )


if __name__ == "__main__":
    main()
