"""Build script for packaging the backend with PyInstaller.

Produces a one-dir PyInstaller bundle under
`backend/dist/sheptun-backend-<triple>/` and copies it into
`src-tauri/resources/backend/<triple>/` so Tauri picks it up at bundle time.
"""
import os
import platform
import shutil
import sys

import PyInstaller.__main__


def current_triple() -> str:
    machine = platform.machine().lower()
    system = sys.platform

    if system == "darwin":
        if machine in ("arm64", "aarch64"):
            return "aarch64-apple-darwin"
        return "x86_64-apple-darwin"
    if system == "win32":
        return "x86_64-pc-windows-msvc"
    if system.startswith("linux"):
        if machine in ("aarch64", "arm64"):
            return "aarch64-unknown-linux-gnu"
        return "x86_64-unknown-linux-gnu"
    raise SystemExit(f"unsupported platform: {system}/{machine}")


def main() -> None:
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(backend_dir)
    triple = current_triple()
    exe_suffix = ".exe" if sys.platform == "win32" else ""
    exe_name = f"sheptun-backend-{triple}{exe_suffix}"

    dist_dir = os.path.join(backend_dir, "dist")
    work_dir = os.path.join(backend_dir, "build")

    # Fresh start for this triple's output folder.
    out_folder = os.path.join(dist_dir, f"sheptun-backend-{triple}")
    if os.path.exists(out_folder):
        shutil.rmtree(out_folder)

    args = [
        os.path.join(backend_dir, "main.py"),
        "--name", f"sheptun-backend-{triple}",
        "--onedir",
        "--noconfirm",
        "--clean",
        "--distpath", dist_dir,
        "--workpath", work_dir,
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.http.h11_impl",
        "--hidden-import", "uvicorn.protocols.http.httptools_impl",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.protocols.websockets.websockets_impl",
        "--hidden-import", "uvicorn.protocols.websockets.wsproto_impl",
        "--hidden-import", "uvicorn.lifespan",
        "--hidden-import", "uvicorn.lifespan.on",
        "--hidden-import", "uvicorn.lifespan.off",
        "--hidden-import", "uvicorn.loops",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.loops.asyncio",
        "--hidden-import", "multipart",
        "--hidden-import", "mutagen",
        "--hidden-import", "mutagen.ogg",
        "--hidden-import", "mutagen.oggvorbis",
        "--hidden-import", "mutagen.mp3",
        "--hidden-import", "mutagen.mp4",
        "--hidden-import", "mutagen.flac",
        "--hidden-import", "mutagen.wave",
        "--collect-submodules", "mutagen",
    ]

    PyInstaller.__main__.run(args)

    tauri_resources = os.path.join(
        repo_root, "src-tauri", "resources", "backend", triple
    )
    if os.path.exists(tauri_resources):
        shutil.rmtree(tauri_resources)
    os.makedirs(os.path.dirname(tauri_resources), exist_ok=True)
    shutil.copytree(out_folder, tauri_resources)

    binary = os.path.join(tauri_resources, exe_name)
    if not os.path.exists(binary):
        raise SystemExit(
            f"expected binary missing: {binary}"
        )

    print(f"Backend bundled for {triple}:")
    print(f"  pyinstaller output: {out_folder}")
    print(f"  copied to tauri:    {tauri_resources}")
    print(f"  entry point:        {binary}")


if __name__ == "__main__":
    main()
