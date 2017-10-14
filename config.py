from helper import configlib

class Config(configlib.Config):
    """The config for Asciiditor"""
    __config_path__ = 'assets/config.json'

    retina = False
    __retina_hint__ = "Enable retina mode ?"
    __retina_type__ = bool

    debugger_path = ''
    __debugger_path_hint__ = "Path to your AsciiDotsDebugger"

if __name__ == '__main__':
    configlib.update_config(Config())
