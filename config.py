from helper import configlib

class Config(configlib.Config):
    """The config for Asciiditor"""
    __config_path__ = 'assets/config.json'

    retina = False
    __retina_hint__ = "Enable retina mode ?"
    __retina_type__ = bool

    debugger_command = 'python path/to/debugger.py {file}'
    __debugger_command_hint__ = "Command to run Asciidots debugger"
    __debugger_command_type__ = configlib.path

    console_log_level = 10
    __console_log_level_type__ = int
    __console_log_level_hint__ = "Debug level in the console between 10 and 50"

if __name__ == '__main__':
    configlib.update_config(Config)
