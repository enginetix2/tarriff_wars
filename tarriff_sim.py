import random
import pandas as pd
import networkx as nx
import requests
from tabulate import tabulate
import matplotlib.pyplot as plt # For visualization, if needed
import openai
import os
# ========== Agent Definition ==========

class CountryAgent:
    def __init__(self, unique_id, agent_type="cooperate", deterrence_threshold=2):
        self.unique_id = unique_id
        self.agent_type = agent_type
        self.deterrence_threshold = deterrence_threshold  # NEW
        self.strategy = "cooperate"
        self.payoff = 0
        self.interactions = 0
        self.last_opponent_strategy = {}
        self.betrayal_count = {}  # Track how many times each opponent has defected against this agent

    def decide_strategy(self, opponent_id):
        if self.agent_type == "cooperate":
            return "cooperate"

        elif self.agent_type == "defect":
            return "defect"

        elif self.agent_type == "random":
            return random.choice(["cooperate", "defect"])

        elif self.agent_type == "tit_for_tat":
            return self.last_opponent_strategy.get(opponent_id, "cooperate")

        elif self.agent_type == "cooperate_w_deterrence":
            betrayals = self.betrayal_count.get(opponent_id, 0)
            if betrayals >= self.deterrence_threshold:
                return "defect"
            else:
                return "cooperate"

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
        self.interactions += 1
        other.interactions += 1

        # Track last moves
        self.last_opponent_strategy[other.unique_id] = their_move
        other.last_opponent_strategy[self.unique_id] = my_move

        # Update betrayal count for deterrence-aware agents
        if their_move == "defect":
            self.betrayal_count[other.unique_id] = self.betrayal_count.get(other.unique_id, 0) + 1
        if my_move == "defect":
            other.betrayal_count[self.unique_id] = other.betrayal_count.get(self.unique_id, 0) + 1


# ========== Model Definition ==========

class TariffGameModel:
    def __init__(self, num_agents=6, seed=None, network_type="small_world", deterrence_threshold=2):
        random.seed(seed)
        self.agents = []
        self.graph = nx.Graph()

        if network_type == "one_vs_all":
            strategies = ["defect"] + ["cooperate", "tit_for_tat", "random", "cooperate", "cooperate_w_deterrence"]
        else:
            strategies = ["cooperate", "defect", "tit_for_tat", "random", "cooperate_w_deterrence"] * (num_agents // 5 + 1)

        for i in range(num_agents):
            agent_type = strategies[i % len(strategies)]
            agent = CountryAgent(unique_id=i, agent_type=agent_type, deterrence_threshold=deterrence_threshold)
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

# ========== Visualization Function ==========
def run_and_track_over_time(seed, num_agents=6, steps=50, network_type="small_world", deterrence_threshold=2):
    model = TariffGameModel(num_agents=num_agents, seed=seed, network_type=network_type, deterrence_threshold=deterrence_threshold)
    
    history = []

    for step in range(steps):
        model.step()
        snapshot = {
            "Step": step,
        }

        for agent in model.agents:
            key = f"{agent.agent_type}_{agent.unique_id}"
            snapshot[key] = agent.payoff

        history.append(snapshot)

    return pd.DataFrame(history)

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

def summarize_with_llm(df, network_type, model_name, use_local_ollama=False):
    """
    Summarize simulation results using either a local LLM (Ollama) or OpenAI's API.

    Args:
        df (pd.DataFrame): The simulation results dataframe.
        network_type (str): The type of network used in the simulation.
        model_name (str): The name of the LLM model (e.g., "ollama" or "openai").
        use_local_ollama (bool): Whether to use the local Ollama server or OpenAI API.
    """
    filename = f"networked_simulation_results_{model_name}.md"
    strategy_stats = df.groupby("Agent_Type")["Final_Payoff"].describe().round(2)
    overall_stats = df["Final_Payoff"].describe().round(2).to_string()
    top_agent = df.loc[df["Final_Payoff"].idxmax()].to_string()
    bottom_agent = df.loc[df["Final_Payoff"].idxmin()].to_string()
    strategy_table = strategy_stats.to_markdown()

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

### Per-Strategy Statistical Summary:
{strategy_stats.to_string()}

### Overall Performance Statistics:
{overall_stats}

### Top-Performing Agent:
{top_agent}

### Lowest-Performing Agent:
{bottom_agent}

---

Please provide the following analysis clearly and concisely:

1. **Strategy Effectiveness**: Explain which strategies performed best and why, considering the '{network_type}' network.
2. **Network Influence**: Explain how this specific network type influenced the strategies' success or failure.
3. **Real-world Implications**: Suggest practical insights or lessons that real-world countries or businesses could apply from these simulation outcomes.
"""

    if use_local_ollama:
        # Use local Ollama server
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3.2", "prompt": prompt, "stream": False}
        )
    else:
        # Use OpenAI API
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set.")
        
        headers = {
            "Authorization": f"Bearer {openai_api_key}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json={
                "model": "gpt-4",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 1500,
                "n": 1,
                "stop": None,
                "stream": False,
                "top_p": 1,
                "frequency_penalty": 0,
                "presence_penalty": 0
            }
        )

    try:
        result = response.json()
        if use_local_ollama:
            llm_response = result.get("response")
        else:
            llm_response = result["choices"][0]["message"]["content"]
    except Exception as e:
        llm_response = f"❌ Failed to parse LLM response: {e}\n{response.text}"

    # Write results to Markdown file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Agent-Based Simulation Results\n\n")
        f.write(f"## Network Type: `{network_type}`\n\n")

        f.write(f"### 📊 Per-Strategy Statistical Summary:\n\n")
        f.write(f"{strategy_table}\n\n")

        f.write(f"### 📈 Overall Performance Statistics:\n\n```\n{overall_stats}\n```\n\n")

        f.write(f"### 🏆 Top-Performing Agent:\n\n```\n{top_agent}\n```\n\n")

        f.write(f"### 🚨 Lowest-Performing Agent:\n\n```\n{bottom_agent}\n```\n\n")

        f.write(f"---\n\n## 🤖 LLM Summary and Recommendations:\n\n{llm_response}\n")

    print(f"✅ Results written to {filename}")

# ========== Main ==========

if __name__ == "__main__":
    network_type = "one_vs_all"  # Change as needed: "fully_connected", "small_world", "ring", "one_vs_all"
    df = run_networked_sim(seeds=range(5), num_agents=6, steps=50, network_type=network_type)

    # Generate summaries for both models
    summarize_with_llm(df, network_type=network_type, model_name="ollama", use_local_ollama=True)
    summarize_with_llm(df, network_type=network_type, model_name="openai", use_local_ollama=False)

    print("✅ Summaries for both models written to respective files.")
