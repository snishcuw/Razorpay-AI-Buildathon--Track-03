"""
Smart Payment Recovery Assistant -- Razorpay AI Buildathon 2026
Track: AI Revenue Recovery

Run with:  streamlit run app.py
"""
import pandas as pd
import plotly.express as px
import streamlit as st

from ai_messenger import generate_recovery_message
from data_generator import generate_transactions
from recovery_engine import (
    assign_recovery_strategy,
    simulate_recovery_outcomes,
    summarize_impact,
)

st.set_page_config(
    page_title="Smart Payment Recovery Assistant",
    page_icon="💳",
    layout="wide",
)

# ---------------------------------------------------------------- sidebar --
st.sidebar.title("⚙️ Simulation Settings")
n_transactions = st.sidebar.slider("Number of failed transactions", 50, 2000, 500, step=50)
seed = st.sidebar.number_input("Random seed", value=42, step=1)
st.sidebar.markdown("---")
st.sidebar.caption(
    "This demo uses synthetic failed-transaction data so it runs with zero "
    "setup. Swap `data_generator.py` for real Razorpay test-mode data to go "
    "from prototype to production."
)
st.sidebar.markdown("---")
st.sidebar.caption(
    "💡 Set the `ANTHROPIC_API_KEY` environment variable to get live "
    "AI-generated customer messages below. Without it, clean template "
    "messages are used instead -- the app always works either way."
)

# ------------------------------------------------------------------ data --
raw_df = generate_transactions(n=n_transactions, seed=int(seed))
df = assign_recovery_strategy(raw_df)
df = simulate_recovery_outcomes(df, seed=int(seed) + 1)
impact = summarize_impact(df)

# ----------------------------------------------------------------- title --
st.title("💳 Smart Payment Recovery Assistant")
st.caption(
    "Every failed payment is lost revenue. This assistant classifies *why* "
    "each payment failed, picks the right recovery strategy, and drafts the "
    "customer message -- automatically."
)

# --------------------------------------------------------------- metrics --
c1, c2, c3, c4 = st.columns(4)
c1.metric("Failed Transactions", f"{impact['total_failed_transactions']:,}")
c2.metric("Total Amount At Risk", f"₹{impact['total_amount_at_risk']:,.0f}")
c3.metric(
    "Recovery Rate — No Action",
    f"{impact['baseline_recovery_rate']*100:.1f}%",
)
c4.metric(
    "Recovery Rate — With Assistant",
    f"{impact['strategy_recovery_rate']*100:.1f}%",
    delta=f"+{(impact['strategy_recovery_rate']-impact['baseline_recovery_rate'])*100:.1f} pts",
)

st.success(
    f"💰 **₹{impact['incremental_amount_recovered']:,.0f} additional revenue recovered** "
    f"compared to doing nothing, across {impact['total_failed_transactions']:,} failed transactions."
)

st.markdown("---")

# ---------------------------------------------------------------- charts --
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Why payments are failing")
    reason_counts = df["failure_reason"].value_counts().reset_index()
    reason_counts.columns = ["failure_reason", "count"]
    fig1 = px.pie(
        reason_counts,
        names="failure_reason",
        values="count",
        hole=0.45,
    )
    fig1.update_layout(margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig1, use_container_width=True)

with col_right:
    st.subheader("Recovery rate: before vs. after")
    compare_df = pd.DataFrame({
        "scenario": ["No action", "With Recovery Assistant"],
        "recovery_rate": [
            impact["baseline_recovery_rate"] * 100,
            impact["strategy_recovery_rate"] * 100,
        ],
    })
    fig2 = px.bar(
        compare_df, x="scenario", y="recovery_rate",
        text="recovery_rate", color="scenario",
        color_discrete_sequence=["#94a3b8", "#16a34a"],
    )
    fig2.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig2.update_layout(showlegend=False, yaxis_title="Recovery rate (%)",
                        margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ------------------------------------------------------------ strategies --
st.subheader("Recovery strategy by failure reason")
strategy_summary = (
    df.groupby(["failure_reason", "recovery_strategy", "strategy_rationale"])
    .agg(transactions=("transaction_id", "count"), total_amount=("amount", "sum"))
    .reset_index()
    .sort_values("transactions", ascending=False)
)
st.dataframe(
    strategy_summary.rename(columns={
        "failure_reason": "Failure Reason",
        "recovery_strategy": "Chosen Strategy",
        "strategy_rationale": "Why This Strategy",
        "transactions": "# Transactions",
        "total_amount": "Total Amount (₹)",
    }),
    use_container_width=True,
    hide_index=True,
)

st.markdown("---")

# -------------------------------------------------------- AI message demo --
st.subheader("🤖 AI-drafted customer message")
st.caption(
    "Pick a transaction to see the message our assistant would send. "
    "The recovery *strategy* is chosen by deterministic rules (auditable, "
    "predictable). The AI is used only to phrase the customer-facing message."
)

selected_id = st.selectbox("Select a transaction", df["transaction_id"].head(50))
row = df[df["transaction_id"] == selected_id].iloc[0]

msg_col1, msg_col2 = st.columns([1, 1])
with msg_col1:
    st.markdown("**Transaction details**")
    st.write(f"- Customer: {row['customer_name']}")
    st.write(f"- Amount: ₹{row['amount']:,.0f}")
    st.write(f"- Failure reason: `{row['failure_reason']}`")
    st.write(f"- Chosen strategy: `{row['recovery_strategy']}`")
    st.caption(row["strategy_rationale"])

with msg_col2:
    st.markdown("**Message sent to customer**")
    with st.spinner("Drafting message..."):
        message = generate_recovery_message(
            name=row["customer_name"],
            amount=row["amount"],
            failure_reason=row["failure_reason"],
            strategy=row["recovery_strategy"],
            rationale=row["strategy_rationale"],
        )
    st.info(message)

st.markdown("---")
st.caption(
    "Built for the Razorpay AI Buildathon 2026 — AI Revenue Recovery track. "
    "Synthetic data used for demo purposes; recovery-strategy success rates "
    "are illustrative and would be replaced with real outcome data in production."
)
