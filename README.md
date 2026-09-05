Razorpay-AI-Buildathon--Track-03
Smart Payment Recovery Assistant 

## The Problem

Every failed payment is potential lost revenue for a merchant. Payments fail for very different reasons: a temporary network blip, an insufficient balance, a bad OTP, a declined card, and each of those calls for a different recovery action. Most merchants either do nothing or treat every failure the same way (just retry), which recovers far less revenue than a reason-aware approach would.

Target user: merchants using Razorpay who want to recover more failed-payment revenue without building a custom recovery system from scratch.

## The Solution

A dashboard that, for every failed transaction:

1. Looks at why it failed
2. Assigns a recovery strategy based on that reason
3. Uses an LLM to draft a customer message explaining what happens next
4. Shows the merchant the revenue impact, before vs. after, with real numbers

## Architecture

```
data_generator.py    -> synthetic failed-transaction data (swap for real
                         Razorpay test-mode data in production)
recovery_engine.py   -> rule-based strategy assignment + before/after
                         impact simulation
ai_messenger.py      -> LLM-drafted customer message, with template fallback
app.py               -> Streamlit dashboard tying it all together
```

## Why AI is used only where it helps

Choosing the recovery strategy is a rule, not an AI decision. Given a failure reason, the best strategy is well understood: insufficient funds means retry after 24 hours, not immediately. A rule engine here is faster, predictable, and auditable, and there's no real reason to spend an LLM call on it.

Drafting the actual customer message is where AI adds value. Turning "insufficient_funds, retry_after_24h" into a message a customer would actually want to read is the kind of language task LLMs are good at and static templates are bad at.

If no API key is available, the app falls back to a template for the message, so it still runs end to end and the AI is additive rather than a single point of failure.

## Setup & Running

```bash
pip install -r requirements.txt

# Optional: enables live AI-generated messages instead of templates
export ANTHROPIC_API_KEY="your-key-here"

streamlit run app.py
```

The app runs fully without an API key; template messages are used instead of live LLM ones. Everything else (data, charts, strategy assignment, impact metrics) works either way.

## Limitations & Future Improvements

- Recovery strategies are currently a fixed rule table. A production version could learn strategy effectiveness over time from real outcomes.
- Success-rate numbers used in the simulation are illustrative, not measured. Real deployment would need to track actual retry outcomes via Razorpay webhooks.
- Only one channel (message text) is modeled. A real system would also decide when and where (SMS, email, push) to send it.

