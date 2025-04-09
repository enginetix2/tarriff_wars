from mesa import Agent
import random

class CountryAgent(Agent):
    def __init__(self, unique_id, model, agent_type="cooperate"):
        super().__init__(model)
        self.unique_id = unique_id
        self.agent_type = agent_type
        self.strategy = "cooperate"
        self.payoff = 0
        self.last_opponent_strategy = {}

    def decide_strategy(self, opponent_id):
        if self.agent_type == "cooperate":
            return "cooperate"
        elif self.agent_type == "defect":
            return "defect"
        elif self.agent_type == "random":
            return random.choice(["cooperate", "defect"])
        elif self.agent_type == "tit_for_tat":
            return self.last_opponent_strategy.get(opponent_id, "cooperate")

    def interact_with(self, other):
        my_move = self.decide_strategy(other.unique_id)
        their_move = other.decide_strategy(self.unique_id)

        payoff_matrix = {
            ("cooperate", "cooperate"): (3, 3),
            ("cooperate", "defect"):    (0, 5),
            ("defect", "cooperate"):    (5, 0),
            ("defect", "defect"):       (1, 1)
        }

        my_payoff, their_payoff = payoff_matrix[(my_move, their_move)]
        self.payoff += my_payoff
        other.payoff += their_payoff

        # Store what the opponent did
        self.last_opponent_strategy[other.unique_id] = their_move
        other.last_opponent_strategy[self.unique_id] = my_move
