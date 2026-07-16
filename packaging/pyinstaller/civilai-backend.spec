# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_dynamic_libs, collect_data_files

ROOT = Path(SPECPATH).resolve().parents[1]

block_cipher = None


def safe_collect(package):
    try:
        return collect_submodules(package)
    except Exception:
        return []


llama_binaries = collect_dynamic_libs('llama_cpp')
llama_datas = collect_data_files('llama_cpp')

a = Analysis(
    [str(ROOT / 'desktop_runtime' / 'backend_launcher.py')],
    pathex=[str(ROOT)],
    binaries=llama_binaries,
    datas=[
        (str(ROOT / 'rag_docs'), 'rag_docs'),
    ] + llama_datas,
    hiddenimports=[
        'construction_ai.settings',
        'construction_ai.urls',
        'construction_ai.wsgi',
        'construction_ai.asgi',
        'corsheaders',
        'rest_framework',
        'rest_framework_simplejwt',
        'rest_framework_simplejwt.authentication',
        'rest_framework_simplejwt.token_blacklist',
        'users',
        'users.apps',
        'users.models',
        'users.views',
        'db',
        'db.apps',
        'db.models',
        'db.permissions',
        'projects',
        'projects.apps',
        'projects.models',
        'projects.views',
        'projects.local_meeting_views',
        'ollama_api',
        'ollama_api.apps',
        'ollama_api.views',
        'rag_engine',
        'soundcard',
        'faster_whisper',
        'llama_cpp',
        'pywhispercpp',
    ] + safe_collect('construction_ai')
      + safe_collect('corsheaders')
      + safe_collect('rest_framework')
      + safe_collect('rest_framework_simplejwt')
      + safe_collect('users')
      + safe_collect('db')
      + safe_collect('projects')
      + safe_collect('ollama_api')
      + safe_collect('notification')
      + safe_collect('utils')
      + safe_collect('rag_engine')
      + safe_collect('soundcard')
      + safe_collect('faster_whisper')
      + safe_collect('llama_cpp')
      + safe_collect('pywhispercpp'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'pytest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    exclude_binaries=False,
    name='civilai-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
