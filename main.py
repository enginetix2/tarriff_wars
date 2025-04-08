from src.models.tariff_game_model import TariffGameModel
from src.analysis.results_analysis import plot_total_payoff

def run_simulation(steps=20):
    model = TariffGameModel()
    for _ in range(steps):
        model.step()

    model_data = model.datacollector.get_model_vars_dataframe()
    agent_data = model.datacollector.get_agent_vars_dataframe()

    print("Final Agent Strategies and Payoffs:")
    print(agent_data.tail(2))  # Last strategies

    plot_total_payoff(model_data)

if __name__ == "__main__":
    run_simulation(steps=50)
