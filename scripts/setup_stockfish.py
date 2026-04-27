from __future__ import annotations

import platform
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
ENGINES_DIR = PROJECT_ROOT / "engines"

STOCKFISH_RELEASE_URL = "https://stockfishchess.org/download/"


def detect_os() -> str:
    system = platform.system().lower()
    if "windows" in system:
        return "windows"
    if "darwin" in system:
        return "macos"
    if "linux" in system:
        return "linux"
    return "unknown"


def default_binary_relative_path(os_name: str) -> str:
    if os_name == "windows":
        return "engines/stockfish/stockfish-windows-x86-64-avx2.exe"
    if os_name == "macos":
        return "engines/stockfish/stockfish-macos-m1-apple-silicon"
    if os_name == "linux":
        return "engines/stockfish/stockfish-ubuntu-x86-64-avx2"
    return "engines/stockfish"


def find_existing_binary_path() -> str | None:
    if not ENGINES_DIR.exists():
        return None

    candidates = sorted(ENGINES_DIR.rglob("stockfish*"))
    for path in candidates:
        if not path.is_file():
            continue
        if path.suffix.lower() == ".exe" or path.name.startswith("stockfish"):
            return path.relative_to(PROJECT_ROOT).as_posix()
    return None


def upsert_env_var(key: str, value: str, env_path: Path) -> None:
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    else:
        lines = []

    updated = False
    output_lines: list[str] = []
    for line in lines:
        if line.startswith(f"{key}="):
            output_lines.append(f"{key}={value}")
            updated = True
        else:
            output_lines.append(line)

    if not updated:
        output_lines.append(f"{key}={value}")

    env_path.write_text("\n".join(output_lines).rstrip() + "\n", encoding="utf-8")


def print_instructions(os_name: str, suggested_path: str) -> None:
    print("Stockfish setup helper")
    print("-" * 24)
    print(f"Detected OS: {os_name}")
    print("Download Stockfish 16.1 from:")
    print(f"  {STOCKFISH_RELEASE_URL}")
    print("")
    print("Recommended steps:")
    print("1) Download the correct archive for your OS.")
    print("2) Extract the binary into the project's engines folder.")
    print(f"3) Ensure the binary lives at: {suggested_path}")
    print("")
    if os_name == "windows":
        print("Windows hint: choose the x64 AVX2 build when available.")
    elif os_name == "macos":
        print("macOS hint: choose Apple Silicon build for M1/M2/M3, otherwise x64.")
    elif os_name == "linux":
        print("Linux hint: choose the x64 AVX2 build unless your CPU lacks AVX2.")


def main() -> None:
    os_name = detect_os()
    ENGINES_DIR.mkdir(parents=True, exist_ok=True)

    existing_path = find_existing_binary_path()
    suggested_path = existing_path or default_binary_relative_path(os_name)

    print_instructions(os_name, suggested_path)
    upsert_env_var("STOCKFISH_PATH", suggested_path, ENV_FILE)

    print("")
    print(f"Updated {ENV_FILE.name}: STOCKFISH_PATH={suggested_path}")


if __name__ == "__main__":
    main()
