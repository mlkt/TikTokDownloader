from cx_Freeze import Executable, setup

build_exe_options = {
    "packages": [
        "rich",
        "uvicorn",
    ],
    "include_files": [
        ("locale", "locale"),
        ("static", "static"),
        ("encipher.py", "encipher.py"),
        ("douyin_websign", "douyin_websign"),
    ],
    "include_msvcr": True,
}

executables = [
    Executable(
        script="main.py",
        icon="./static/images/DouK-Downloader",
        target_name="DouK-Downloader",
    )
]

setup(
    name="DouK-Downloader",
    options={"build_exe": build_exe_options},
    executables=executables,
)
