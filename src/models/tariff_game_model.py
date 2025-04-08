from mesa import Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from src.agents.country_agent import CountryAgent

class TariffGameModel(Model):
    def __init__(self, seed=None, agent_types=("cooperate", "defect")):
        super().__init__(seed=seed)

        self.schedule = RandomActivation(self)

        self.country1 = CountryAgent(unique_id=1, model=self, agent_type=agent_types[0])
        self.country2 = CountryAgent(unique_id=2, model=self, agent_type=agent_types[1])

        self.schedule.add(self.country1)
        self.schedule.add(self.country2)

        self.datacollector = DataCollector(
            model_reporters={"Total_Payoff": lambda m: m.total_payoff},
            agent_reporters={"Strategy": "strategy", "Payoff": "payoff", "Agent_Type": "agent_type"}
        )

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)

    def get_opponent(self, agent):
        return self.country2 if agent == self.country1 else self.country1

    @property
    def total_payoff(self):
        return self.country1.payoff + self.country2.payoff
