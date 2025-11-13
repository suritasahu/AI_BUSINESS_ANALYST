# main.py

import pandas as pd
from modules.sql_generator import generate_sql_from_prompt
from modules.sql_executor import run_query_on_dataframe
from modules.analyzer import summarize_results
from modules.visualizer import plot_results

def ai_business_agent(question, df):
    print(f"\n🧠 Question: {question}")

    schema = {col: str(df[col].dtype) for col in df.columns}

    sql = generate_sql_from_prompt(question, schema)
    print("\nSQL Generated:\n", sql)

    results = run_query_on_dataframe(df, sql)
    print("\nResults:\n", results.head())

    summary = summarize_results(results, question)
    print("\nSummary:\n", summary)

    plot_results(results, question)


if __name__ == "__main__":
    df = pd.read_csv("sample.csv")  # load ANY file
    question = input("Ask your question: ")
    ai_business_agent(question, df)
