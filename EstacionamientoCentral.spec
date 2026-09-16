# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import re

from PyInstaller.utils.hooks import collect_submodules


def _read_app_version():
    source = Path("app_version.py").read_text(encoding="utf-8")
    match = re.search(r'^APP_VERSION\s*=\s*["\']([^"\']+)["\']', source, re.MULTILINE)
    if not match:
        raise ValueError("app_version.py must define APP_VERSION")
    return match.group(1)


APP_VERSION = _read_app_version()


def _version_tuple(version):
    parts = version.split(".")
    if len(parts) > 4 or any(not part.isdigit() for part in parts):
        raise ValueError(f"APP_VERSION must be numeric dotted version, got {version!r}")
    return tuple(int(part) for part in parts + ["0"] * (4 - len(parts)))


def _write_version_info():
    file_version = _version_tuple(APP_VERSION)
    version_path = Path("build") / "EstacionamientoCentral.version_info.txt"
    version_path.parent.mkdir(parents=True, exist_ok=True)
    version_path.write_text(
        f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={file_version},
    prodvers={file_version},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [StringStruct('CompanyName', 'Estacionamiento Central'),
         StringStruct('FileDescription', 'Estacionamiento Central Desktop'),
         StringStruct('FileVersion', '{APP_VERSION}'),
         StringStruct('InternalName', 'EstacionamientoCentral'),
         StringStruct('OriginalFilename', 'EstacionamientoCentral.exe'),
         StringStruct('ProductName', 'Estacionamiento Central'),
         StringStruct('ProductVersion', '{APP_VERSION}')]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
""",
        encoding="utf-8",
    )
    return str(version_path)


version_info = _write_version_info()

hiddenimports = collect_submodules("PySide6")

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("config.ini", "."),
        ("schema.sql", "."),
        ("assets", "assets"),
    ],
    hiddenimports=hiddenimports + [
        "views.login",
        "views.setup_window",
        "controllers.login_controller",
        "controllers.usuarios_controller",
        "utils.db",
        "styles",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="EstacionamientoCentral",
    icon="assets/icons/logo-estc-central.ico",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    version=version_info,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="EstacionamientoCentral",
)
