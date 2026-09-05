"""
Generates synthetic failed-transaction data for the Smart Payment Recovery Assistant.
""" 

import random
from datetime import datetime, timedelta

import pandas as pd

FAILURE_REASONS = [
    "insufficient_funds",
    "card_declined",
    "network_timeout",
    "bank_server_error",
    "otp_failed",
]

CUSTOMER_NAMES = [
    "Aarav Sharma", "Priya Patel", "Rohan Mehta", "Ananya Iyer", "Vikram Singh",
    "Sneha Reddy", "Karan Malhotra", "Divya Nair", "Arjun Kapoor", "Ishita Rao",
    "Aditya Verma", "Meera Joshi", "Rahul Gupta", "Kavya Menon", "Siddharth Rao",
]

PAYMENT_METHODS = ["credit_card", "debit_card", "upi", "netbanking", "wallet"]


def generate_transactions(n: int = 500, seed: int = 42) -> pd.DataFrame:
    """Generate n synthetic failed-transaction records."""
    random.seed(seed)
    rows = []
    now = datetime.now()

    for i in range(n):
        reason = random.choices(
            FAILURE_REASONS,
            weights=[30, 25, 20, 15, 10],  # insufficient_funds is most common
            k=1,
        )[0]
        rows.append({
            "transaction_id": f"txn_{1000 + i}",
            "customer_name": random.choice(CUSTOMER_NAMES),
            "amount": round(random.uniform(199, 15000), 2),
            "payment_method": random.choice(PAYMENT_METHODS),
            "failure_reason": reason,
            "failed_at": now - timedelta(hours=random.randint(1, 720)),
            "attempt_number": random.choice([1, 1, 1, 2, 2, 3]),
        })

    df = pd.DataFrame(rows)
    df = df.sort_values("failed_at", ascending=False).reset_index(drop=True)
    return df
