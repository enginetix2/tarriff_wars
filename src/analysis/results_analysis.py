import matplotlib.pyplot as plt

def plot_total_payoff(model_data):
    model_data.plot(title='Total Payoff Over Time', ylabel='Payoff', xlabel='Step')
    plt.grid(True)
    plt.tight_layout()
    plt.show()
