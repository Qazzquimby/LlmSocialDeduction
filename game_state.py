class GameState:
    def __init__(self):
        self.center_cards = []
        self.night_actions = []
        self.day_actions = []

    def add_center_cards(self, cards):
        self.center_cards = cards

    def record_night_action(self, player, action):
        self.night_actions.append((player, action))

    def record_day_action(self, player, action):
        self.day_actions.append((player, action))

    def get_player_role(self, player):
        # This method might be used to get a player's current role,
        # considering any role switches that happened during the night
        return player.role
