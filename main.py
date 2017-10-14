import click

from data_structures.sparsemap import Map
from visual import gui


@click.command()
@click.argument('file')
def main(file: str):
    editor = gui.Asciiditor(file)
    editor.run()


if __name__ == '__main__':
    main()
