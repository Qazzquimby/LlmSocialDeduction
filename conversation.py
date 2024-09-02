def handle_conversations(players):
    num_rounds = 2  # You can adjust this
    for round_i in range(num_rounds):
        print(f"\nConversation Round {round_i + 1} / {num_rounds}")
        for player in players:
            message = player.speak()
            for listening_player in players:
                listening_player.observations.append(f"{player.name}: {message}")