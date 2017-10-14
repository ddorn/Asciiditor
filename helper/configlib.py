"""
Utility to manage a configuration fileand provide an easy way to modify it.

To use the configlib in your project, just create a file name `conf.py` awith the following code

    import configlib

    class Config(configlib.Config):
        __config_path__ = 'my/path/to/th/config/file.json

        # you can define all class attributes as you want
        # as long as they don't start and end with a bouble underscore
        foot_size = 52
        bald  = True
        __bald_hint__ = "Are you bald ?"
        name = "Archibald"
        # and you can not define any function (except super methods)

        # if a name starts with 'path_' or ends with '_path' there will be autocompletion
        # when the user wants to update it
        path_to_install = ''

        All types will be preserved even after save and loading them
        favourite_color = (230, 120, 32)

    if __name__ == '__main__':
        # with that the user will be able to easily edit the config by running `python config.py`
        configlib.update_config(Config)

    Then in your main code you can get the config with

    import config
    myconfig = config.Config()


Make with love by ddorn (https://github.com/ddorn/)
"""

import os

import click
import glob
import json
import readline


def is_config_field(attr: str):
    """Every string which doesn't start and end with '--' is considered to be a valid configuration field."""
    return not (attr.startswith('__') and attr.endswith('__'))


def represent_path(field: str):
    """A path field starts or and its name with path and an underscore"""
    return field.lower().startswith('path_') or field.lower().endswith('_path')


def get_field_type(config: 'Config', field: str):
    """Get the type given by __field_type__ or str if not defined"""
    return getattr(config, '__' + field + '_type__', str)


def prompt_file(prompt, default=None):
    """Prompt a file name with autocompletion"""

    def complete(text, state):
        sugg = (glob.glob(text + '*'))[state]

        if sugg is None:
            return

        sugg = sugg.replace('\\', '/')

        if os.path.isdir(sugg) and not sugg.endswith('/'):
            sugg += '/'

        return sugg

    readline.set_completer_delims(' \t\n;')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(complete)

    if default is not None:
        r = input('%s [%r]: ' % (prompt, default))
    else:
        r = input('%s: ' % prompt)

    r = r or default

    # remove the autocompletionbe before quitting for future input()
    readline.parse_and_bind('tab: self-insert')

    return r


class Config(object):
    __config_path__ = 'config.json'

    def __init__(self, raise_on_fail=True):
        self.__load__(raise_on_fail)

    def __iter__(self):
        """Iterate over the fields"""
        for attr in type(self).__dict__:
            if is_config_field(attr):
                yield attr

    def __load__(self, raise_on_fail=True):
        try:
            with open(self.__config_path__) as f:
                file = f.read()

        except FileNotFoundError:
            file = '{}'

        conf = json.loads(file)  # type: dict

        # we update only the fields in the conf #NoPolution
        for field in self:
            # so we set the field to the field if there is one in the conf (.get)
            new_value = conf.get(field, getattr(self, field))
            supposed_type = get_field_type(self, field)
            if not isinstance(new_value, supposed_type):
                import inspect
                print("The field {} is a {} but should be {}.".format(field, type(new_value).__name__, supposed_type.__name__), end=' ')
                print("You can run `python {}` to update the configuration".format(inspect.getfile(self.__class__)))
                if raise_on_fail:
                    raise TypeError

            setattr(self, field, conf.get(field, getattr(self, field)))

    def __save__(self):

        attr_dict = {attr: self[attr] for attr in self if is_config_field(attr)}

        jsonstr = json.dumps(attr_dict, indent=4, sort_keys=True)
        with open(self.__config_path__, 'w') as f:
            f.write(jsonstr)

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __getitem__(self, item):
        return self.__getattribute__(item)


def update_config(config):
    config = config(raise_on_fail=False)  # type: Config

    print()
    print('Welcome !')
    print('Press enter to keep the defaults or enter a new value to update the configuration.')
    print('Press Ctrl+C at any time to quit and save')

    print("The following fields are available: ")
    i = 0
    for i, field in enumerate(list(config)):
        click.echo(" - {:-3} ".format(i + 1), nl=0)
        click.echo(field + ' (', nl=0)
        click.secho(get_field_type(config, field).__name__, fg='yellow', nl=0)
        click.echo(')')
    click.echo()

    skip = click.prompt("Do you want to skip to a given number ?", 1, type=click.IntRange(1, i + 1))
    click.echo()

    try:
        for i, field in enumerate(list(config)):
            if i + 1 < skip:
                continue
            type_ = getattr(config, '__' + field + '_type__', type(config[field]))
            hint = getattr(config, '__' + field + '_hint__', field) + ' ({})'.format(type_.__name__)

            if represent_path(field):
                config[field] = prompt_file(hint, default=config[field])
            else:
                while True:
                    config[field] = click.prompt(hint, default=config[field], type=type_)

                    supposed_type = get_field_type(config, field)
                    if isinstance(config[field], supposed_type):
                        break

                    click.echo('The field ', nl=False)
                    click.secho(field, nl=False, fg='yellow')
                    click.echo(' is a ', nl=False)
                    click.secho(type(config[field]).__name__, nl=False, fg='red')
                    click.echo(' but should be ', nl=False)
                    click.secho(supposed_type.__name__, nl=False, fg='green')
                    click.echo('.')
    except click.exceptions.Abort:
        config.__save__()
        print('\nSaved !')
    else:
        config.__save__()
        print('Saved !')
