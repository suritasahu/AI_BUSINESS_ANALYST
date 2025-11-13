# modules/analyzer.py

def summarize_results(df, question: str) -> str:
    if df.empty:
        return "No results found for this query."

    q = question.lower()

    try:
        if "revenue" in q or "sales" in q:
            if "total_revenue" in df.columns:
                total = df["total_revenue"].sum()
                top = df.iloc[df["total_revenue"].idxmax()]
                return f"Highest revenue: {top['total_revenue']} | Total: {total}"
        return f"Returned {len(df)} rows."
    except:
        return "Could not summarize results."
