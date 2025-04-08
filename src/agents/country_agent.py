from mesa import Agent
import random

class CountryAgent(Agent):
    def __init__(self, unique_id, model, agent_type="cooperate"):
        super().__init__(model)
        self.unique_id = unique_id
        self.agent_type = agent_type  # determines behavior
        self.strategy = "cooperate"
        self.payoff = 0
        self.last_opponent_strategy = None

    def step(self):
        opponent = self.model.get_opponent(self)

        # Decide current strategy based on agent_type
        if self.agent_type == "cooperate":
            self.strategy = "cooperate"

        elif self.agent_type == "defect":
            self.strategy = "defect"

        elif self.agent_type == "tit_for_tat":
            if self.last_opponent_strategy is None:
                self.strategy = "cooperate"
            else:
                self.strategy = self.last_opponent_strategy

        elif self.agent_type == "random":
            self.strategy = random.choice(["cooperate", "defect"])

        # Calculate payoff
        self.payoff = self.calculate_payoff(self.strategy, opponent.strategy)

        # Store opponent's last strategy for next round
        self.last_opponent_strategy = opponent.strategy

    def calculate_payoff(self, own, opponent):
        payoff_matrix = {
            ("cooperate", "cooperate"): 3,
            ("cooperate", "defect"): 0,
            ("defect", "cooperate"): 5,
            ("defect", "defect"): 1
        }
        return payoff_matrix[(own, opponent)]
