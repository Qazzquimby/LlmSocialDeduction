def handle_conversations(players):
    num_rounds = 2  # You can adjust this
    for round_i in range(num_rounds):
        conversation_round_message =f"\nConversation Round {round_i + 1} / {num_rounds}"
        print(conversation_round_message)
        for player in players:
            player.observations.append(conversation_round_message)

        for player in players:
            message = player.speak()
            for listening_player in players:
                listening_player.observations.append(message)