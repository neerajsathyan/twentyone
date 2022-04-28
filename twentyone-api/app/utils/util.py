import copy
import json
from random import shuffle
from flask import current_app

from app import Card
from app.utils.constants import MINIMUM_BET_VALUE, MINIMUM_BET_PLAYER_STRING, BUST_VALUE, PLAYER_STATUS_BUST, \
    PLAYER_STATUS_STAND, PLAYER_STATUS_READY, BANK_MAXIMUM_HIT_VALUE, PLAYER_STATUS_WIN, CARD_KIND, CARD_FACE_VALUE


def shuffle_deck(ele_list):
    shuffle(ele_list)


def find_player(player_id: str):
    for player in current_app.players:
        if player.id == player_id and not player.is_bank:
            if player.wallet < MINIMUM_BET_VALUE:
                return True, player, MINIMUM_BET_PLAYER_STRING
            else:
                return True, player, "Player Found."
    return False, None, "Player not found!"


def active_player_exists():
    for player in current_app.players:
        if player.active and not player.is_bank:
            return True
    return False


def active_player_minimum_bet_check():
    # check if all the active players have valid minimum bet value on hold
    for player in current_app.players:
        if player.active and not player.is_bank and player.on_hold < MINIMUM_BET_VALUE:
            return False
    return True


def give_card_to_all_players(round_no: int):
    # except for the bank.
    if round_no == 1:
        # check if the card array is empty, else this should not run
        try:
            for player in current_app.players:
                if player.active and not player.is_bank and len(player.cards) == 0:
                    card = current_app.decks.pop()
                    player.cards.append(card)
                    # update the value
                    player.value += card.value
        except Exception as e:
            return False, current_app.players, format(e)

        return True, current_app.players, "Card distributed to all players."
    else:
        try:
            for player in current_app.players:
                if player.active and not player.is_bank and len(player.cards) != 0:
                    card = current_app.decks.pop()
                    player.cards.append(card)
                    # update the value
                    player.value += card.value
        except Exception as e:
            return False, current_app.players, format(e)

        return True, current_app.players, "Card distributed to all players."


def perform_hit(player):
    card = current_app.decks.pop()
    player.cards.append(card)
    player.value += card.value


def check_bust(player):
    if player.value > BUST_VALUE:
        player.status = PLAYER_STATUS_BUST
        player.on_hold = 0
        return True, "Player " + player.name + " is bust."
    else:
        return False, "Player " + player.name + " ready."


def perform_stand(player):
    player.status = PLAYER_STATUS_STAND


def check_if_bank_can_play():
    if current_app.bank.status == PLAYER_STATUS_READY:
        for player in current_app.players:
            if player.active and player.status == PLAYER_STATUS_READY and not player.is_bank:
                return False, "Active players are yet to complete actions."
        # check if active players are standing and not all active players are bust.
        bust_no = 0
        active_no = 0
        for player in current_app.players:
            if player.active and not player.is_bank:
                active_no += 1
                if player.status == PLAYER_STATUS_BUST:
                    bust_no += 1
        if bust_no < active_no:
            return True, "Bank can play."
        else:
            current_app.bank.status = PLAYER_STATUS_WIN
            return False, "All players busted, game over!"
    else:
        return False, "Bank is " + current_app.bank.status


def perform_bank_actions():
    while current_app.bank.value <= BANK_MAXIMUM_HIT_VALUE:
        # perform hit
        perform_hit(current_app.bank)
        update_value_for_ace(current_app.bank)
    # if 17 or more bank must stand
    perform_stand(current_app.bank)


def retrieve_winner():
    bust_cond, msg = check_bust(current_app.bank)

    if bust_cond:
        # when the bank is bust (>21), all standing players wins
        for player in current_app.players:
            if player.status == PLAYER_STATUS_STAND and not player.is_bank:
                player.wallet += 2 * player.on_hold
                player.on_hold = 0
                player.status = PLAYER_STATUS_WIN
    else:
        # When the bank and player have the same number of points, the bank wins.
        max_player = current_app.bank
        for player in current_app.players:
            if player.status == PLAYER_STATUS_STAND and not player.is_bank:
                if player.value > max_player.value:
                    max_player = player
        max_player.wallet += 2 * max_player.on_hold
        max_player.on_hold = 0
        max_player.status = PLAYER_STATUS_WIN

    return [json.loads(player.toJSON()) if player.status == PLAYER_STATUS_WIN else None for player in
            current_app.players]


def update_value_for_ace(player):
    # check with multiple ace value which is closer to 21..
    if player.value > BUST_VALUE:
        # then check if you have ace in the cards of players..
        for card in player.cards:
            if card.face_value == "ace" and card.value == 11:
                card.value = 1
                player.value -= 10
                if player.value <= BUST_VALUE:
                    break


def create_cards():
    card_list = []
    for kind in CARD_KIND:
        if kind != "joker":
            for face_value in CARD_FACE_VALUE:
                if face_value != "joker":
                    card_list.append(Card(kind, face_value))
    return card_list


def continue_next_round():
    # if you find a status: win check for player or bank
    for player in current_app.players:
        if player.status == PLAYER_STATUS_WIN and not player.is_bank:
            reset_status_active_players()
            return True, "Next round continues."
        elif player.status == PLAYER_STATUS_WIN and player.is_bank:
            # check if any player can play.
            for player2 in current_app.players:
                if player2.wallet >= MINIMUM_BET_VALUE and not player2.is_bank:
                    reset_status_active_players()
                    return True, "Next round continues."
            return False, "No player have fund to play next round."
        else:
            return False, "Cannot continue to next round."


def reset_status_active_players():
    # reset status and active variables to run another round..
    for player in current_app.players:
        if player.active:
            for card in player.cards:
                current_app.decks.extend(copy.deepcopy(card))
            player.cards = []
            player.value = 0
            player.status = PLAYER_STATUS_READY
            if not player.is_bank:
                player.active = False
    shuffle_deck(current_app.decks)
