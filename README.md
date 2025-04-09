# Tariff Game Simulation

An agent-based simulation to model tariff strategies between countries, built with Python and Mesa.

## Project Overview

This project simulates interactions between countries (agents) using different trade strategies in various network structures. The goal is to analyze how strategies like cooperation, defection, and retaliation perform in different network configurations and to summarize the results using local and remote language models (LLMs).

## How It Works

### 1. **Agents**
Each country is represented as an agent (`CountryAgent`) with the following attributes:
- **Strategy**: Determines how the agent interacts with others (e.g., cooperate, defect, tit-for-tat).
- **Payoff**: Tracks the agent's cumulative score based on interactions.
- **Interactions**: Counts the number of interactions the agent has participated in.
- **Betrayal Count**: Tracks how many times an opponent has defected against the agent.

Agents decide their strategy based on their type:
- **Cooperate**: Always cooperates.
- **Defect**: Always defects.
- **Random**: Randomly cooperates or defects.
- **Tit-for-Tat**: Mimics the opponent's last move.
- **Cooperate with Deterrence**: Cooperates unless the opponent defects too many times, then switches to defection.

### 2. **Networks**
The simulation models interactions between agents using different network structures:
- **Fully Connected**: Every agent interacts with every other agent.
- **Ring**: Agents interact with their immediate neighbors in a circular arrangement.
- **Small World**: A mix of local clustering and random long-range connections.
- **One vs. All**: One aggressive agent interacts with all others, who have limited connections.

### 3. **Simulation**
The `TariffGameModel` class manages the simulation:
- Initializes agents and assigns them to nodes in the network.
- Simulates interactions between agents based on the network structure.
- Tracks payoffs, interactions, and betrayal counts for each agent.

### 4. **LLM Summarization**
The simulation results are summarized using either:
- **Local LLM (Ollama)**: A locally hosted language model.
- **OpenAI API**: A remote language model (e.g., GPT-4).

The `summarize_with_llm` function generates a detailed Markdown report for each model, including:
- Statistical summaries of agent strategies.
- Overall performance metrics.
- Insights and recommendations based on the simulation results.

### 5. **Output**
The simulation outputs two Markdown files:
- `networked_simulation_results_ollama.md`: Results summarized by the local LLM.
- `networked_simulation_results_openai.md`: Results summarized by the OpenAI API.

## Project Structure

- `tarriff_sim.py`: Main simulation and summarization code.
- `data/`: Stores simulation outputs (optional).
- `notebooks/`: Exploratory analyses (optional).
- `README.md`: Project documentation.

## Setup and Running

### Prerequisites
- Python 3.8 or higher
- Required Python packages (install via `requirements.txt`)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/tariff_wars.git
   cd tariff_wars
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Simulation
Run the simulation and generate summaries:
```bash
python tarriff_sim.py
```

### Environment Variables
To use the OpenAI API, set your API key as an environment variable:
```bash
set OPENAI_API_KEY=your_openai_api_key
```

### Output
After running the simulation, you will find the following files in the project directory:
- `networked_simulation_results_ollama.md`
- `networked_simulation_results_openai.md`

## Example Results

### Network Type: `one_vs_all`
- **Top Strategy**: Defect
- **Lowest Strategy**: Cooperate
- **Insights**: Aggressive strategies dominate in asymmetric networks, while cooperative strategies require stronger alliances to succeed.

## Future Improvements
- Add more complex agent strategies.
- Explore additional network types.
- Visualize network interactions and payoffs over time.

## License
This project is licensed under the MIT License.
