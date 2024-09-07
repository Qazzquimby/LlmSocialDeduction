import json
from pathlib import Path

from player import AIPlayer


class ModelPerformanceTracker:
    def __init__(self):
        self.performance_file = Path("model_performance.json")
        self.performance_data = self.load_performance_data()

    def load_performance_data(self):
        if self.performance_file.exists():
            with open(self.performance_file, "r") as f:
                return json.load(f)
        return {}

    def update_performance(self, player: "AIPlayer", did_win: bool):
        if player.model not in self.performance_data:
            self.performance_data[player.model] = {"games_played": 0, "games_won": 0, "total_cost": []}
        if player.name not in self.performance_data:
            self.performance_data[player.name] = {"games_played": 0, "games_won": 0, "total_cost": []}
        
        self.performance_data[player.model]["games_played"] += 1
        self.performance_data[player.name]["games_played"] += 1

        self.performance_data[player.model]["total_cost"].append( player.total_cost)
        self.performance_data[player.name]["total_cost"].append( player.total_cost)

        if did_win:
            self.performance_data[player.model]["games_won"] += 1
            self.performance_data[player.name]["games_won"] += 1

    def save_performance_data(self):
        with open(self.performance_file, "w") as f:
            json.dump(self.performance_data, f, indent=2)

    def get_performance_summary(self):
        summary = []
        for model, data in self.performance_data.items():
            win_rate = data["games_won"] / data["games_played"] if data["games_played"] > 0 else 0
            avg_cost = sum(data["total_cost"]) / data["games_played"] if data["games_played"] > 0 else 0
            summary.append(f"{model}: Win Rate: {win_rate:.2%}, Avg Cost: ${avg_cost:.4f}, Games Played: {data['games_played']}")
        return "\n".join(summary)

performance_tracker = ModelPerformanceTracker()
