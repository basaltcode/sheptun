"""Build script for packaging the backend with PyInstaller."""
import PyInstaller.__main__
import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))

args = [
    os.path.join(backend_dir, 'main.py'),
    '--name', 'sheptun-backend',
    '--onedir',
    '--noconfirm',
    '--clean',
    '--distpath', os.path.join(backend_dir, 'dist'),
    '--workpath', os.path.join(backend_dir, 'build'),
    '--hidden-import', 'uvicorn.logging',
    '--hidden-import', 'uvicorn.protocols.http',
    '--hidden-import', 'uvicorn.protocols.http.auto',
    '--hidden-import', 'uvicorn.protocols.http.h11_impl',
    '--hidden-import', 'uvicorn.protocols.http.httptools_impl',
    '--hidden-import', 'uvicorn.protocols.websockets',
    '--hidden-import', 'uvicorn.protocols.websockets.auto',
    '--hidden-import', 'uvicorn.protocols.websockets.websockets_impl',
    '--hidden-import', 'uvicorn.protocols.websockets.wsproto_impl',
    '--hidden-import', 'uvicorn.lifespan',
    '--hidden-import', 'uvicorn.lifespan.on',
    '--hidden-import', 'uvicorn.lifespan.off',
    '--hidden-import', 'uvicorn.loops',
    '--hidden-import', 'uvicorn.loops.auto',
    '--hidden-import', 'uvicorn.loops.asyncio',
    '--hidden-import', 'multipart',
    '--hidden-import', 'mutagen',
    '--hidden-import', 'mutagen.ogg',
    '--hidden-import', 'mutagen.oggvorbis',
    '--hidden-import', 'mutagen.mp3',
    '--hidden-import', 'mutagen.mp4',
    '--hidden-import', 'mutagen.flac',
    '--hidden-import', 'mutagen.wave',
    '--collect-submodules', 'mutagen',
]

PyInstaller.__main__.run(args)
