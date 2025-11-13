# modules/visualizer.py

import matplotlib.pyplot as plt

def plot_results(df, question):
    if df.empty:
        return

    fig, ax = plt.subplots()

    num_cols = df.select_dtypes(include="number").columns.tolist()
    if len(df.columns) >= 2 and num_cols:
        x = df.columns[0]
        y = num_cols[0]
        df.plot(x=x, y=y, marker="o", ax=ax)
        plt.title("Insights")
        plt.show()
