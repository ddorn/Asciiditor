import click

from data_structures.sparsemap import Map
from visual import gui


@click.command()
@click.argument('file')
@click.option('--retina', is_flag=True, default=False)
def main(file: str, retina: bool):
    editor = gui.Asciiditor(file, retina)
    editor.run()


if __name__ == '__main__':
    main()
