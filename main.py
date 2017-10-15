# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from logging.handlers import RotatingFileHandler

import click

import config
from visual import gui

FILE_LOG_LEVEL = logging.DEBUG


def setup_logging(console_level):
    # Thanks to  http://sametmax.com/ecrire-des-logs-en-python/
    # création de l'objet logger qui va nous servir à écrire dans les logs
    logger = logging.getLogger()
    # on met le niveau du logger à DEBUG, comme ça il écrit tout
    logger.setLevel(logging.DEBUG)

    # création d'un formateur qui va ajouter le temps, le niveau
    # de chaque message quand on écrira un message dans le log
    formatter = logging.Formatter('%(asctime)s :: %(levelname)-8s :: %(message)s')
    # création d'un handler qui va rediriger une écriture du log vers
    # un fichier en mode 'append', avec 1 backup et une taille max de 1Mo
    file_handler = RotatingFileHandler('assets/activity.log', 'a', 1000000, 1)
    # on lui met le niveau sur DEBUG, on lui dit qu'il doit utiliser le formateur
    # créé précédement et on ajoute ce handler au logger
    file_handler.setLevel(FILE_LOG_LEVEL)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # création d'un second handler qui va rediriger chaque écriture de log
    # sur la console
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(console_level)
    logger.addHandler(stream_handler)


@click.command()
@click.argument('file')
def main(file: str):
    conf = config.Config()
    setup_logging(conf.console_log_level)

    logging.info('Starting editor with %s', file)

    editor = gui.Asciiditor(file, conf)
    editor.run()

    logging.info('Editor closed')


if __name__ == '__main__':
    main()
