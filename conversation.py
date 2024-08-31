import random

def handle_conversations(players):
    num_rounds = 3  # You can adjust this
    for round in range(num_rounds):
        print(f"\nConversation Round {round + 1}")
        for player in players:
            message = player.speak()
            print(f"{player.name}: {message}")
            
            # Randomly select 1-2 other players to reply
            num_replies = random.randint(1, 2)
            replying_players = random.sample([p for p in players if p != player], num_replies)
            
            for replying_player in replying_players:
                reply = replying_player.speak()
                print(f"{replying_player.name} (in response): {reply}")
