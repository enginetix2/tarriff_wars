import pandas as pd
from src.models.tariff_game_model import TariffGameModel

def run_sweep(agent_pairs, seeds=range(5), steps=50):
    results = []

    for (type1, type2) in agent_pairs:
        for seed in seeds:
            model = TariffGameModel(seed=seed, agent_types=(type1, type2))
            for _ in range(steps):
                model.step()

            results.append({
                "Seed": seed,
                "Agent1_Type": type1,
                "Agent2_Type": type2,
                "Final_Payoff": model.total_payoff
            })

    return pd.DataFrame(results)


if __name__ == "__main__":
    agent_pairs = [
        ("cooperate", "cooperate"),
        ("cooperate", "defect"),
        ("cooperate", "tit_for_tat"),
        ("defect", "tit_for_tat"),
        ("tit_for_tat", "tit_for_tat"),
        ("random", "tit_for_tat"),
        ("random", "random")
    ]

    df = run_sweep(agent_pairs, seeds=range(5), steps=50)
    print(df)

    print("\n📊 Average Final Payoff by Agent Pair:")
    print(df.groupby(["Agent1_Type", "Agent2_Type"])["Final_Payoff"].mean())

    df.to_csv("data/strategy_sweep.csv", index=False)
