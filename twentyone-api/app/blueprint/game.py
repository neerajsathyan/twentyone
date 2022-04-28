import json
import math
import uuid

from flask import (
    abort, Blueprint, request, Response, make_response, jsonify, current_app
)

from app import Players
from app.setup import update_bet
from app.utils.constants import MINIMUM_BET_VALUE, MINIMUM_BET_PLAYER_STRING, ACTION_HIT, ACTION_STAND, ACTION_SPLIT, \
    PLAYER_STATUS_STAND, PLAYER_STATUS_BUST
from app.utils.util import find_player, active_player_exists, give_card_to_all_players, active_player_minimum_bet_check, \
    perform_hit, check_bust, perform_stand, check_if_bank_can_play, perform_bank_actions, retrieve_winner, \
    update_value_for_ace, create_cards, shuffle_deck, continue_next_round, reset_status_active_players

bp = Blueprint('game', __name__, url_prefix='/game')


@bp.route('/status', methods=('GET',))
def get_status():
    """Retrieve status of all the players and bank
    for now also show status of the deck also

    Returns:
        response: flask.Response object with the application/json mimetype.
    """

    player_id = request.args.get("id", None)
    if player_id is None:
        data = current_app.players
        deck = current_app.decks
        return make_response(jsonify({
            'status': 'success',
            'uuid': str(uuid.uuid4()),
            'data': [json.loads(dat.toJSON()) for dat in data],
            'deck': [json.loads(dec.toJSON()) for dec in deck]
        }), 200)
    else:
        status, player, message = find_player(player_id)
        if status:
            return make_response(jsonify({
                'status': 'success',
                'uuid': str(uuid.uuid4()),
                'data': [json.loads(player.toJSON())],
                'deck': [json.loads(dec.toJSON()) for dec in current_app.decks],
                'message': message
            }), 200)
        else:
            return make_response(jsonify({
                'status': 'failure',
                'uuid': str(uuid.uuid4()),
                'data': [],
                'deck': [json.loads(dec.toJSON()) for dec in current_app.decks],
                'message': message
            }))


@bp.route('/enter_game', methods=('POST',))
def enter_game():
    """
    Players choose to enter or not to enter a round
    """
    data = request.get_json()
    player_id = data["id"]
    enter = data["enter"]
    status, player, message = find_player(player_id)
    if status:
        # player found
        if message == MINIMUM_BET_PLAYER_STRING:
            # Player does not have credit to continue.
            player.active = False
            return make_response(jsonify({
                'status': 'failure',
                'message': 'Player does not have enough credit to continue.'
            }), 400)
        else:
            # Player can make bet now.
            player.active = enter
            return make_response(jsonify({
                'status': 'success',
                'message': 'Player status updated!'
            }), 200)
    else:
        # player not found..
        return make_response(jsonify({
            'status': 'failure',
            'message': 'Player not found!'
        }), 400)


@bp.route('/start_round', methods=('GET',))
def start_round():
    """
    this api starts the round and provides a card from
    the deck to each active players.
    """
    round_no = request.args.get("round", None)
    # check if there are at least one active player for the round..
    if round_no is None:
        if active_player_exists():
            # provide a card from the deck to each active player
            status, players_list, message = give_card_to_all_players(1)
            if status:
                return make_response(jsonify({
                    'status': 'success',
                    'uuid': str(uuid.uuid4()),
                    'data': [json.loads(player.toJSON()) for player in players_list],
                    'deck': [json.loads(dec.toJSON()) for dec in current_app.decks],
                    'message': message
                }), 200)
            else:
                return make_response(jsonify({
                    'status': 'failure',
                    'uuid': str(uuid.uuid4()),
                    'message': message
                }), 400)
        else:
            return make_response(jsonify({
                'status': 'failure',
                'message': 'No Active Player to start round!'
            }), 400)
    elif round_no == "2":
        if active_player_minimum_bet_check():
            # provide a card from the deck to each active player
            status, players_list, message = give_card_to_all_players(round_no)
            if status:
                return make_response(jsonify({
                    'status': 'success',
                    'uuid': str(uuid.uuid4()),
                    'data': [json.loads(player.toJSON()) for player in players_list],
                    'deck': [json.loads(dec.toJSON()) for dec in current_app.decks],
                    'message': message
                }), 200)
            else:
                return make_response(jsonify({
                    'status': 'failure',
                    'uuid': str(uuid.uuid4()),
                    'message': message
                }), 400)
        else:
            return make_response(jsonify({
                'status': 'failure',
                'message': 'No Active Player to start round!'
            }), 400)
    else:
        return make_response(jsonify({
            'status': 'failure',
            'message': 'Bad request given'
        }), 400)


@bp.route('/place_bet', methods=('POST',))
def place_bet():
    if not request.is_json:
        abort(400)
    data = request.get_json()
    # get id and bet value.
    player_id = data["id"]
    bet_value = data["value"]
    if bet_value < MINIMUM_BET_VALUE:
        return make_response(jsonify({
            'status': 'failure',
            'uuid': str(uuid.uuid4()),
            'message': 'Place minimum bet value or higher'
        }), 400)
    status, msg = update_bet(player_id, bet_value)
    if status:
        return make_response(jsonify({
            'status': 'success',
            'uuid': str(uuid.uuid4())
        }), 200)
    else:
        return make_response(jsonify({
            'status': 'failure',
            'uuid': str(uuid.uuid4()),
            'message': msg
        }), 400)


@bp.route('/action', methods=('POST',))
def perform_action():
    if not request.is_json:
        abort(400)
    data = request.get_json()
    player_id = data["id"]
    action = data["action"]
    # check if it's a bank or a player.
    if player_id == current_app.bank.id:
        # actions performed on bank
        # First check if all other active players are either stand or bust..
        status, msg = check_if_bank_can_play()
        if status:
            # Bank starts doing actions..
            perform_bank_actions()

            # check who won the game now
            winning_players = retrieve_winner()
            return make_response(jsonify({
                'status': 'success',
                'uuid': str(uuid.uuid4()),
                'message': 'Winning Players',
                'data': winning_players
            }), 200)
        else:
            return make_response(jsonify({
                'status': 'failure',
                'uuid': str(uuid.uuid4()),
                'message': msg
            }), 400)
    # check if player_id valid
    status, player, message = find_player(player_id)
    if status and player.active and player.on_hold >= MINIMUM_BET_VALUE and player.status not in [PLAYER_STATUS_STAND,
                                                                                                  PLAYER_STATUS_BUST]:
        if action == ACTION_HIT:
            # perform hit..
            perform_hit(player)
            update_value_for_ace(player)
            # check if the player is bust.
            bust_cond, message = check_bust(player)
            return make_response(jsonify({
                'status': 'success',
                'uuid': str(uuid.uuid4()),
                'data': [json.loads(player.toJSON()) for player in current_app.players],
                'deck': [json.loads(dec.toJSON()) for dec in current_app.decks],
                'condition': bust_cond,
                'message': message
            }), 200)
        elif action == ACTION_STAND:
            # perform stand..
            perform_stand(player)

            return make_response(jsonify({
                'status': 'success',
                'uuid': str(uuid.uuid4()),
                'data': [json.loads(player.toJSON()) for player in current_app.players],
                'deck': [json.loads(dec.toJSON()) for dec in current_app.decks],
                'message': 'Player ' + player.name + ' stands!'
            }), 200)
        elif action == ACTION_SPLIT:
            # TODO
            pass

    else:
        return make_response(jsonify({
            'status': 'failure',
            'uuid': str(uuid.uuid4()),
            'message': message + "\n Player is " + player.status + "."
        }), 400)


@bp.route('/done_round', methods=('GET',))
def done_round():
    # after a winner is established, update the values to get into the next round.
    status, msg = continue_next_round()
    if status:
        reset_status_active_players()
        return make_response(jsonify({
            'status': 'success',
            'uuid': str(uuid.uuid4()),
            'message': msg
        }), 200)
    else:
        return make_response(jsonify({
            'status': 'failure',
            'uuid': str(uuid.uuid4()),
            'message': msg
        }), 400)


@bp.route('/reset', methods=('POST',))
def reset_game():
    # reset game settings.
    # get a shuffled deck first..
    if not request.is_json:
        abort(400)
    data = request.get_json()
    deck_size = data["deck_size"]

    # initialize each deck with correct cards..
    current_app.decks = []
    for i in range(deck_size):
        current_app.decks.extend(create_cards())

    # Shuffle decks before the game begins
    shuffle_deck(current_app.decks)

    # Initialize the 3 players + bank (for now static) player 0 is bank
    current_app.player_size = data["player_size"]
    current_app.players = []
    current_app.bank = Players("Bank", [], True, math.inf, True)
    current_app.players.append(current_app.bank)
    for i in range(current_app.player_size):
        current_app.players.append(Players("Player " + str(i + 1), [], False, 10, False))

    return make_response(jsonify({
        'status': 'success',
        'uuid': str(uuid.uuid4()),
        'message': 'Game reset with new specs.'
    }), 200)
