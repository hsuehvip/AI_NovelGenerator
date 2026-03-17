# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules
import os

datas = []
binaries = []
hiddenimports = [
    'typing_extensions',
    'langchain_openai',
    'langchain',
    'langgraph',
    'openai',
    'google',
    'google.generativeai',
    'google.api_core',
    'google.api_core.exceptions',
    'nltk',
    'sentence_transformers',
    'scikit_learn',
    'langchain_community',
    'langchain_chroma',
    'pydantic',
    'pydantic_core',
    'tiktoken_ext',
    'tiktoken_ext.openai_public',
    'chromadb',
    'chromadb.utils.embedding_functions',
    'chromadb.config',
    'onnxruntime',
    'numpy',
    'PIL',
    'PIL._imagingtk',
    'customtkinter',
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
]

hiddenimports += collect_submodules('google')
hiddenimports += collect_submodules('google.api_core')
hiddenimports += collect_submodules('google.api_core.exceptions')

tmp_ret = collect_all('chromadb')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

tmp_ret = collect_all('langchain')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

tmp_ret = collect_all('langchain_chroma')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

customtkinter_paths = [
    r'c:\Users\xieli\Desktop\AI_NovelGenerator\.venv\Lib\site-packages\customtkinter',
    r'C:\Python311\Lib\site-packages\customtkinter',
    r'C:\Program Files\Python311\Lib\site-packages\customtkinter',
]

for path in customtkinter_paths:
    if os.path.exists(path):
        datas.append((path, 'customtkinter'))
        break

icon_path = 'icon.ico' if os.path.exists('icon.ico') else None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI_NovelGenerator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AI_NovelGenerator'
)
