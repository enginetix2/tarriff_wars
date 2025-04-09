import random
import pandas as pd
import networkx as nx
import requests
from tabulate import tabulate

# ========== Agent Definition ==========

class CountryAgent:
    def __init__(self, unique_id, agent_type="cooperate"):
        self.unique_id = unique_id
        self.agent_type = agent_type
        self.strategy = "cooperate"
        self.payoff = 0
        self.interactions = 0  # NEW
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
        self.interactions += 1  # NEW
        other.interactions += 1

        self.last_opponent_strategy[other.unique_id] = their_move
        other.last_opponent_strategy[self.unique_id] = my_move


# ========== Model Definition ==========

class TariffGameModel:
    def __init__(self, num_agents=6, seed=None, network_type="small_world"):
        random.seed(seed)
        self.agents = []
        self.graph = nx.Graph()

        if network_type == "one_vs_all":
            strategies = ["defect"] + ["cooperate", "tit_for_tat", "random", "cooperate", "defect"]
        else:
            strategies = ["cooperate", "defect", "tit_for_tat", "random"] * (num_agents // 4 + 1)

        for i in range(num_agents):
            agent = CountryAgent(unique_id=i, agent_type=strategies[i % len(strategies)])
            self.agents.append(agent)
            self.graph.add_node(i, agent=agent)

        self._create_network(network_type)

    def _create_network(self, network_type):
        num_agents = len(self.agents)

        if network_type not in ["fully_connected", "ring", "small_world", "one_vs_all"]:
            raise ValueError(f"Unknown network_type '{network_type}'. Choose from fully_connected, ring, small_world, one_vs_all.")

        if network_type == "fully_connected":
            for i in range(num_agents):
                for j in range(i + 1, num_agents):
                    self.graph.add_edge(i, j)

        elif network_type == "ring":
            for i in range(num_agents):
                self.graph.add_edge(i, (i + 1) % num_agents)

        elif network_type == "small_world":
            # Create a small-world network topology
            small_world = nx.watts_strogatz_graph(n=num_agents, k=2, p=0.4, seed=random.randint(0, 9999))
            
            # Clear your current graph and copy over nodes and edges
            self.graph = nx.Graph()
            self.graph.add_nodes_from(small_world.nodes)
            self.graph.add_edges_from(small_world.edges)

            # Assign agents to nodes
            for i, agent in enumerate(self.agents):
                self.graph.nodes[i]["agent"] = agent

        elif network_type == "one_vs_all":
            for i in range(1, num_agents):
                self.graph.add_edge(0, i)

        # Attach agent objects to nodes
        for i, agent in enumerate(self.agents):
            self.graph.nodes[i]["agent"] = agent

    def step(self):
        for a in self.graph.nodes():
            for neighbor in self.graph.neighbors(a):
                if a < neighbor:
                    agent_a = self.graph.nodes[a]["agent"]
                    agent_b = self.graph.nodes[neighbor]["agent"]
                    agent_a.interact_with(agent_b)

# ========== Batch Runner ==========

def run_networked_sim(seeds=range(5), num_agents=6, steps=50, network_type="small_world"):
    results = []

    for seed in seeds:
        model = TariffGameModel(num_agents=num_agents, seed=seed, network_type=network_type)

        for _ in range(steps):
            model.step()

        for agent in model.agents:
            degree = model.graph.degree[agent.unique_id]  # number of connections
            results.append({
                "Seed": seed,
                "Agent_ID": agent.unique_id,
                "Agent_Type": agent.agent_type,
                "Final_Payoff": agent.payoff,
                "Interactions": agent.interactions,
                "Degree": degree
            })

    return pd.DataFrame(results)


# ========== LLM Summary Function ==========

def summarize_with_ollama(df, network_type):
    strategy_stats = df.groupby("Agent_Type")["Final_Payoff"].describe().round(2)
    overall_stats = df["Final_Payoff"].describe().round(2).to_string()
    top_agent = df.loc[df["Final_Payoff"].idxmax()].to_string()
    bottom_agent = df.loc[df["Final_Payoff"].idxmin()].to_string()
    strategy_table = strategy_stats.to_string()

    prompt = f"""
You are an economic analyst reviewing the results of an agent-based simulation of international trade strategies.  
The agents interact within a '{network_type}' network.

Agent strategies include:
- **cooperate** (always cooperative),
- **defect** (always aggressive),
- **tit_for_tat** (retaliates based on opponent's previous action),
- **random** (randomly cooperates or defects).

Network type description:
- **fully_connected**: Every agent interacts with every other agent directly.
- **small_world**: Agents are locally clustered with some random long-range connections.
- **ring**: Agents interact with immediate neighbors in a circular network.
- **one_vs_all**: One aggressive agent (usually defecting) engages directly against all other agents, who have limited connections.

### 📊 **Per-Strategy Statistical Summary:**
{strategy_table}

### 📈 **Overall Performance Statistics:**
{overall_stats}

### 🏆 **Top-Performing Agent:**
{top_agent}

### 🚨 **Lowest-Performing Agent:**
{bottom_agent}

---

Please provide the following analysis clearly and concisely:

1. **Strategy Effectiveness**: Explain which strategies performed best and why, considering the given '{network_type}' network.
2. **Network Influence**: Explain how this specific network type likely influenced the strategies' success or failure.
3. **Real-world Implications**: Suggest practical insights or lessons that real-world countries or businesses could apply from these simulation outcomes.
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "llama3.2", "prompt": prompt, "stream": False}
    )

    try:
        result = response.json()
        print("\n🤖 LLM Summary and Recommendations:\n")
        print(result["response"])
    except Exception as e:
        print("❌ Failed to parse LLM response:", e)
        print(response.text)

# ========== Main ==========

if __name__ == "__main__":
    network_type = "one_vs_all"  # Change as needed: "fully_connected", "small_world", "ring", "one_vs_all"
    df = run_networked_sim(seeds=range(5), num_agents=6, steps=50, network_type=network_type)

    sorted_df = df.sort_values(by="Final_Payoff", ascending=False)

    print("\n🔍 Simulation Results Overview:")
    print("===================================")
    print("Network Type:", network_type)
    print("Average Payoff:", sorted_df["Final_Payoff"].mean())
    print("Minimum Payoff:", sorted_df["Final_Payoff"].min())
    print("Maximum Payoff:", sorted_df["Final_Payoff"].max())
    print("Median Payoff:", sorted_df["Final_Payoff"].median())
    print("Standard Deviation of Payoff:", sorted_df["Final_Payoff"].std())
    print("Number of Agents:", len(df["Agent_ID"].unique()))
    print("Number of Seeds:", len(df["Seed"].unique()))
    print("Number of Steps:", df["Interactions"].max())
    print("Total Interactions:", df["Interactions"].sum())
    
    print("\n✅ Simulation Complete. Top Results:")
    print(tabulate(sorted_df, headers="keys", tablefmt="pretty", showindex=False))

    summary = df.groupby("Agent_Type")["Final_Payoff"].agg(["mean", "std", "min", "max"]).round(2).sort_values(by="mean", ascending=False)
    print("\n📈 Strategy Summary (Sorted by Mean Payoff):")
    print(tabulate(summary, headers="keys", tablefmt="pretty"))

    df.to_csv("networked_results.csv", index=False)

    # Pass network_type explicitly here:
    summarize_with_ollama(df, network_type=network_type)
