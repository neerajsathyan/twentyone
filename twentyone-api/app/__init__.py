"""This package is Flask HTTP REST API Template template that already has the database bootstrap
implemented and also all feature related with the user authentications.

Application features:
    Python 3.7
    Flask
    PEP-8 for code style

This module contains the factory function 'create_app' that is
responsible for initializing the application according
to a previous configuration.
"""
import math
import os

from flask import Flask, current_app
from flask_jwt_extended import JWTManager

from app.api.card import Card
from app.api.players import Players
from app.utils import constants, util
from app.utils.util import create_cards


def create_app(test_config: dict = {}) -> Flask:
    """This function is responsible to create a Flask instance according
    a previous setting passed from environment. In that process, it also
    initialise the database source.

    Parameters:
        test_config (dict): settings coming from test environment

    Returns:
        flask.app.Flask: The application instance
    """

    app = Flask(__name__, instance_relative_config=True)

    load_config(app, test_config)

    init_instance_folder(app)
    init_database(app)
    with app.app_context():
        init_game()
    init_blueprints(app)
    init_commands(app)
    init_jwt_manager(app)

    return app


def load_config(app: Flask, test_config) -> None:
    """Load the application's config

    Parameters:
        app (flask.app.Flask): The application instance Flask that'll be running
        test_config (dict):
    """

    if os.environ.get('FLASK_ENV') == 'development' or test_config.get("FLASK_ENV") == 'development':
        app.config.from_object('app.config.Development')

    elif test_config.get('TESTING'):
        app.config.from_mapping(test_config)

    else:
        app.config.from_object('app.config.Production')


def init_instance_folder(app: Flask) -> None:
    """Ensure the instance folder exists.

    Parameters:
        app (flask.app.Flask): The application instance Flask that'll be running
    """

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass


def init_database(app) -> None:
    """Responsible for initializing and connecting to the database
    to be used by the application.

    Parameters:
        app (flask.app.Flask): The application instance Flask that'll be running
    """

    from .database import init
    init(app)


def init_blueprints(app: Flask) -> None:
    """Registes the blueprint to the application.

    Parameters:
        app (flask.app.Flask): The application instance Flask that'll be running
    """

    # error handlers
    from .blueprint.handlers import register_handler
    register_handler(app)

    # error Handlers
    from .blueprint import index, auth, account
    app.register_blueprint(index.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(account.bp)

    # apis for the game..
    from .blueprint import game
    app.register_blueprint(game.bp)


def init_commands(app):
    from app.commands import register_commands
    register_commands(app)


def init_jwt_manager(app):
    from .authentication import init
    jwt = JWTManager(app)
    init(jwt)


def init_game():
    """for now 3 players hardcoded, can be changed later from api.."""
    # get a shuffled deck first..
    deck_size = 1

    # initialize each deck with correct cards..
    current_app.decks = []
    for i in range(deck_size):
        current_app.decks.extend(create_cards())

    # Shuffle decks before the game begins
    util.shuffle(current_app.decks)

    # Initialize the 3 players + bank (for now static) player 0 is bank
    current_app.player_size = 3
    current_app.players = []
    current_app.bank = Players("Bank", [], True, math.inf, True)
    current_app.players.append(current_app.bank)
    current_app.players.append(Players("Player 1", [], False, 10, False))
    current_app.players.append(Players("Player 2", [], False, 10, False))
    current_app.players.append(Players("Player 3", [], False, 10, False))

    # TODO Include the order later..
    # current_app.cur_bet_player = current_app.players[1]
    # current_app.cur_bet_player_index = 1
    # current_app.next_bet_player = current_app.players[2]
    # current_app.next_bet_player_index = 2
