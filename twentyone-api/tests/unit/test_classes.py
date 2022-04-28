"""Tests for the Card and Player class"""


def test_create_new_players_class(app):
    from app import Players

    player1 = Players("Neeraj", [], True, 10, False)
    player2 = Players("Player 2", ["23", "34"], False, 4, True)
    assert isinstance(player1, Players)
    assert isinstance(player2, Players)

    assert isinstance(player2.cards, list)
