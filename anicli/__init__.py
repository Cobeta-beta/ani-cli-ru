import importlib

import pkg_resources

from anicli.cli import APP

__version__ = "5.0.10"


def _get_version():
    return f"""anicli-ru {__version__}; anicli-api {pkg_resources.get_distribution("anicli-api").version}"""


def get_modules(package_name='anicli_api.source'):
    # dynamically get available source extractors
    import os
    import importlib.util
    package_path = importlib.util.find_spec(package_name).submodule_search_locations[0]
    files = os.listdir(package_path)
    return [f[:-3] for f in files if f.endswith('.py') and not f.startswith('__') and not f.endswith('__')]


def run_cli():
    import argparse

    parser = argparse.ArgumentParser(description=_get_version(), usage="anicli-ru [ФЛАГИ]")
    parser.add_argument(
        "-s",
        "--source",
        default="animego",
        choices=get_modules(),
        help="Источника аниме (По умолчанию `animego`)",
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        default=1080,
        choices=[0, 144, 240, 360, 480, 720, 1080],
        help="Выбор минимального качества выводимого видео в /video. "
        "Если нету такого разрешения, будет выбранно ближайшее к нему"
        "Например: если -q 1080 но нету 1080 - будет выбрано 720, 480...0 "
        "(По умолчанию 1080)",
    )
    parser.add_argument(
        "-p",
        "--player",
        type=str,
        default="mpv",
        choices=["mpv", "vlc", "cvlc"],
        help="Выбор видеоплеера. (По умолчанию 'mpv')",
    )
    parser.add_argument(
        "--ffmpeg",
        action="store_true",
        default=False,
        help="Использует бэкэнд ffmpeg для перенаправления буфера видео в плеер. "
        "Включите, если ваш плеер не принимает params headers (например, vlc).",
    )
    parser.add_argument(
        "--m3u",
        action="store_true",
        default=False,
        help="Создание m3u плейлиста для режима воспроизведения фрагментов. "
             "(По умолчанию выключенно)",
    )
    parser.add_argument(
        "--m3u-size",
        type=int,
        default=12,
        help="Создание m3u плейлиста для режима воспроизведения фрагментов. "
             "(По умолчанию 12)",
    )
    parser.add_argument(
        "--proxy",
        type=str,
        default=None,
        help="Выполните запрос к экстрактору через прокси, например socks5://127.0.0.1:1080, http://user:passwd@127.0.0.1:443",
    )
    parser.add_argument("--timeout", type=float, default=None, help="Таймаут запроса на установку")
    parser.add_argument("-v", "--version", action="store_true", default=False, help="Вывод версии, и выход")

    namespaces = parser.parse_args()
    if namespaces.version:
        print(_get_version())
        exit(0)
    # setup eggella app
    module = importlib.import_module(f"anicli_api.source.{namespaces.source}")
    APP.CFG.EXTRACTOR = getattr(module, "Extractor")()
    APP.CFG.USE_FFMPEG_ROUTE = namespaces.ffmpeg
    APP.CFG.PLAYER = namespaces.player
    APP.CFG.MIN_QUALITY = namespaces.quality
    APP.CFG.TIMEOUT = namespaces.timeout
    APP.CFG.PROXY = namespaces.proxy
    APP.CFG.M3U_MAKE = namespaces.m3u
    APP.CFG.M3U_MAX_SIZE = namespaces.m3u_size
    APP.loop()


if __name__ == '__main__':
    run_cli()
