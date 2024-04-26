import logging
from urllib.parse import urlsplit

from anicli_api.base import HTTPSync

from anicli.cli.config import app


@app.on_startup()
def setup_http_config():
    if app.CFG.PROXY:
        app.cmd.print_ft("Настройка прокси")
    if app.CFG.TIMEOUT:
        app.cmd.print_ft("Таймаут настройки")
    app.CFG.EXTRACTOR.http = HTTPSync(proxies=app.CFG.PROXY, timeout=app.CFG.TIMEOUT)
    # todo video extractor provide config


@app.on_startup()
def loaded_extractor_msg():
    app.cmd.print_ft("{Загружен провайдер}:", urlsplit(app.CFG.EXTRACTOR.BASE_URL).netloc)