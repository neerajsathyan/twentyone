"""Tests for the Card and Player class"""
from flask import current_app

from app import init_game


def test_init_game(app):
    init_game()
    assert isinstance(current_app.players, list)
    assert len(current_app.players) == current_app.player_size
    assert isinstance(current_app.decks, list)