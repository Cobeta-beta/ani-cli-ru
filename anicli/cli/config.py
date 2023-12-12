from typing import TYPE_CHECKING, Optional
from pathlib import Path
# import tomli


from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts.prompt import CompleteStyle
from eggella import Eggella

from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

if TYPE_CHECKING:
    from anicli_api.base import BaseExtractor


class Config:
    EXTRACTOR: "BaseExtractor" = NotImplemented
    PLAYER: str = "mpv"
    PLAYER_EXTRA_ARGS: str = ""
    MIN_QUALITY: int = 1080
    USE_FFMPEG_ROUTE: bool = False
    _CONFIG_PATH: str = "~/.config/ruanicli"
    _CONFIG_NAME: str = "config.toml"
    _DB_NAME: str = "anicli.db"
    # httpx params
    PROXY: Optional[str] = None
    TIMEOUT: Optional[float] = None

    @classmethod
    def httpx_kwargs(cls):
        return {"proxies": cls.PROXY, "timeout": cls.TIMEOUT}

    @classmethod
    def exists_config(cls) -> bool:
        cfg_path = Path(cls._CONFIG_PATH) / cls._CONFIG_NAME
        return Path(cls._CONFIG_PATH).exists() and cfg_path.exists()

    # @classmethod
    # def set_up_config(cls):
    #     if not cls.exists_config():
    #         folder = Path(cls._CONFIG_PATH)
    #         if not folder.exists():
    #             folder.mkdir()
    #         cfg_path = folder / cls._CONFIG_NAME
    #         if not cfg_path.exists():
    #             cfg_path.touch()
    #             for k,v in cls.__dict__.items():



class AnicliApp(Eggella):
    CFG = Config()


app = AnicliApp("anicli", "~ ")
app.session = PromptSession("~ ",
                            history=FileHistory(".anicli_history"),
                            auto_suggest=AutoSuggestFromHistory(),
                            complete_style=CompleteStyle.MULTI_COLUMN)

app.documentation = """Anicli

This is a simple a TUI client for watching anime.
"""
