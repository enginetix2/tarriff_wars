import pandas as pd
from src.models.tariff_game_model import TariffGameModel

def run_multiagent_sweep(seeds=range(5), num_agents=4, steps=50):
    results = []

    for seed in seeds:
        model = TariffGameModel(seed=seed, num_agents=num_agents)

        for _ in range(steps):
            model.step()

        for agent in model.my_agents:
            results.append({
                "Seed": seed,
                "Agent_ID": agent.unique_id,
                "Agent_Type": agent.agent_type,
                "Final_Payoff": agent.payoff
            })

    return pd.DataFrame(results)

if __name__ == "__main__":
    df = run_multiagent_sweep(seeds=range(5), num_agents=4, steps=50)
    print(df)

    print("\n📊 Average Payoff by Type:")
    print(df.groupby("Agent_Type")["Final_Payoff"].mean())

    df.to_csv("data/multiagent_results.csv", index=False)
