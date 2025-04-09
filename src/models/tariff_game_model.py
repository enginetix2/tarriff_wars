from mesa import Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from src.agents.country_agent import CountryAgent

class TariffGameModel(Model):
    def __init__(self, num_agents=4, seed=None):
        super().__init__(seed=seed)
        self.schedule = RandomActivation(self)
        self.my_agents = []

        strategies = ["cooperate", "defect", "tit_for_tat", "random"]
        for i in range(num_agents):
            strategy = strategies[i % len(strategies)]
            agent = CountryAgent(unique_id=i, model=self, agent_type=strategy)
            self.schedule.add(agent)
            self.my_agents.append(agent)

        self.data_collector = DataCollector(
            agent_reporters={
                "Strategy": "strategy",
                "Payoff": "payoff",
                "Agent_Type": "agent_type"
            }
        )

    def step(self):
        # Pairwise interactions (e.g. round-robin)
        for i, a1 in enumerate(self.my_agents):
            for j, a2 in enumerate(self.my_agents):
                if i < j:
                    a1.step_with(a2)  # New method to handle interaction
                    a2.step_with(a1)

    def step(self):
        self.schedule.step()
        self.data_collector.collect(self)

    def get_opponent(self, agent):
        return self.country2 if agent == self.country1 else self.country1

    @property
    def total_payoff(self):
        return self.country1.payoff + self.country2.payoff
    
    
