import click

from data_structures.sparsemap import Map
from visual import gui


@click.command()
@click.argument('file')
def main(file: str):
    with open(file, 'r', encoding='utf-8') as f:
        data = f.read()

    m = Map(data)
    editor = gui.Asciiditor(m)
    editor.run()


if __name__ == '__main__':
    main()
