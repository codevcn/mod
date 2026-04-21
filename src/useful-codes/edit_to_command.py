import subprocess


def main():
    profile_path = subprocess.check_output(
        ["powershell", "-NoProfile", "-Command", "$PROFILE"], text=True
    ).strip()
    subprocess.Popen(["notepad.exe", profile_path])


if __name__ == "__main__":
    main()
