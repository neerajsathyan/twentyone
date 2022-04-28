from flask import current_app


def update_bet(player_id: str, bet_value: int):
    for player in current_app.players:
        if player.id == player_id and not player.is_bank \
                and player.active:
            # and player_id == current_app.cur_bet_player.id:
            # check if bet_value is higher than the wallet value
            if bet_value > player.wallet:
                return False, "Bet value is higher than wallet value."
            else:
                player.wallet -= bet_value
                player.on_hold = bet_value
                # current_app.cur_bet_player = current_app.players[current_app.next_bet_player_index]
                # if current_app.next_bet_player_index < current_app.player_size:
                #     current_app.next_bet_player_index += 1
                #     current_app.next_bet_player = current_app.players[current_app.next_bet_player_index]
                # else:
                #     current_app.next_bet_player = current_app.players[0]
                #     current_app.next_bet_player_index = 0
                return True, player.name + " bet placed!"
    return False, "Player ID Missing or Bank ID provided or this player is not in order or  inactive player playing " \
                  "which is not allowed. "
