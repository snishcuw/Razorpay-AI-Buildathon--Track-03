from dataclasses import dataclass

import numpy as np
import pandas as pd

# Illustrative base recovery rates per strategy, used only to drive the
# demo simulation. In production these would be learned from real
# retry/recovery outcomes (e.g. via Razorpay webhooks).
STRATEGY_BASE_SUCCESS_RATE = {
    "retry_immediately": 0.62,
    "retry_after_24h": 0.45,
    "suggest_alternate_method": 0.38,
    "resend_otp_and_retry": 0.55,
}

# What recovery looks like with no intervention at all -- our comparison baseline.
BASELINE_SUCCESS_RATE = 0.12


@dataclass
class RecoveryPlan:
    strategy: str
    reason_for_strategy: str


REASON_TO_STRATEGY = {
    "insufficient_funds": RecoveryPlan(
        strategy="retry_after_24h",
        reason_for_strategy="Balance issues often resolve within a day (salary credit, "
                             "top-up); retrying immediately usually just fails again.",
    ),
    "card_declined": RecoveryPlan(
        strategy="suggest_alternate_method",
        reason_for_strategy="An issuer-side decline is unlikely to succeed on retry; "
                             "offering UPI/netbanking as an alternative converts better.",
    ),
    "network_timeout": RecoveryPlan(
        strategy="retry_immediately",
        reason_for_strategy="Network blips are transient -- an immediate retry has a "
                             "high chance of succeeding.",
    ),
    "bank_server_error": RecoveryPlan(
        strategy="retry_immediately",
        reason_for_strategy="Bank-side server errors are usually momentary outages.",
    ),
    "otp_failed": RecoveryPlan(
        strategy="resend_otp_and_retry",
        reason_for_strategy="OTP failures are typically a typo or timeout; resending "
                             "the OTP resolves most cases.",
    ),
}


def assign_recovery_strategy(df: pd.DataFrame) -> pd.DataFrame:
    """Attach a recovery strategy + rationale + expected success rate to each row."""
    df = df.copy()
    df["recovery_strategy"] = df["failure_reason"].map(
        lambda r: REASON_TO_STRATEGY[r].strategy
    )
    df["strategy_rationale"] = df["failure_reason"].map(
        lambda r: REASON_TO_STRATEGY[r].reason_for_strategy
    )
    df["expected_success_rate"] = df["recovery_strategy"].map(STRATEGY_BASE_SUCCESS_RATE)
    return df


def simulate_recovery_outcomes(df: pd.DataFrame, seed: int = 7) -> pd.DataFrame:
    """
    Simulates whether each transaction is recovered, comparing:
      - 'baseline'       -> no intervention at all
      - 'with_strategy'  -> our recovery strategy applied

    This is a simulation for demo purposes. In a real deployment this column
    would instead be filled in from actual retry outcomes tracked via
    Razorpay webhooks, not randomly generated.
    """
    rng = np.random.default_rng(seed)
    df = df.copy()
    df["recovered_baseline"] = rng.random(len(df)) < BASELINE_SUCCESS_RATE
    df["recovered_with_strategy"] = rng.random(len(df)) < df["expected_success_rate"]
    return df


def summarize_impact(df: pd.DataFrame) -> dict:
    """Roll up transaction-level results into headline metrics for the dashboard."""
    total_at_risk = df["amount"].sum()
    baseline_recovered = df.loc[df["recovered_baseline"], "amount"].sum()
    strategy_recovered = df.loc[df["recovered_with_strategy"], "amount"].sum()

    return {
        "total_failed_transactions": len(df),
        "total_amount_at_risk": total_at_risk,
        "baseline_recovered_amount": baseline_recovered,
        "baseline_recovery_rate": df["recovered_baseline"].mean(),
        "strategy_recovered_amount": strategy_recovered,
        "strategy_recovery_rate": df["recovered_with_strategy"].mean(),
        "incremental_amount_recovered": strategy_recovered - baseline_recovered,
    }
