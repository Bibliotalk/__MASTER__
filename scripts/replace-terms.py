import re
from fnmatch import fnmatch
from pathlib import Path


def replace_preserve_case(text, old, new):
    def repl(match):
        word = match.group()
        if word.isupper():
            return new.upper()
        if word.islower():
            return new.lower()
        if word[0].isupper() and word[1:].islower():
            return new.capitalize()
        return new

    return re.sub(old, repl, text, flags=re.IGNORECASE)


def should_exclude(path, exclude_dirs, exclude_files):
    # Exclude directories
    for part in path.parts:
        if any(fnmatch(part, pat) for pat in exclude_dirs):
            return True

    # Exclude files
    if path.is_file():
        if any(fnmatch(path.name, pat) for pat in exclude_files):
            return True

    return False


def process_directory(
    root_dir,
    old,
    new,
    exclude_dirs=None,
    exclude_files=None,
    encoding="utf-8"
):
    exclude_dirs = exclude_dirs or []
    exclude_files = exclude_files or []

    root = Path(root_dir)

    for path in root.rglob("*"):
        if should_exclude(path, exclude_dirs, exclude_files):
            continue

        if path.is_file():
            try:
                text = path.read_text(encoding=encoding)
            except (UnicodeDecodeError, OSError):
                continue  # skip binary or unreadable files

            new_text = replace_preserve_case(text, old, new)

            if new_text != text:
                path.write_text(new_text, encoding=encoding)
                print(f"Updated: {path}")


if __name__ == "__main__":
    process_directory(
        root_dir=".",
        old="submolt",
        new="subforum",
        exclude_dirs=[".git", "node_modules", "scripts", ".history"],
        exclude_files=["*.pyc", "*.png", "*.jpg"]
    )