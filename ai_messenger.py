"""
Generates a friendly, personalized customer recovery message using an LLM.

This is the ONE place in the project that calls an AI model. Turning a
structured (failure_reason, strategy) pair into natural, reassuring
customer-facing text is exactly the kind of task an LLM is good at and a
static template is bad at (templates read robotic and don't adapt tone).

If no API key is configured, we fall back to a clean hand-written template
so the whole app still runs end-to-end with zero setup -- useful for a demo,
and also a natural "graceful failure handling" story for the pitch.
"""
import os

TEMPLATE_MESSAGES = {
    "retry_after_24h": (
        "Hi {name}, your payment of Rs.{amount:,.0f} didn't go through due to a "
        "balance issue. No worries -- we'll automatically retry it in 24 hours. "
        "You can also retry anytime from your account."
    ),
    "suggest_alternate_method": (
        "Hi {name}, we couldn't process your payment of Rs.{amount:,.0f} with your "
        "card. Would you like to try UPI or netbanking instead? It only takes a minute."
    ),
    "retry_immediately": (
        "Hi {name}, your payment of Rs.{amount:,.0f} hit a temporary technical issue. "
        "We're retrying it now -- you should see a confirmation shortly."
    ),
    "resend_otp_and_retry": (
        "Hi {name}, the OTP for your Rs.{amount:,.0f} payment didn't verify in time. "
        "We've sent a new OTP -- please enter it to complete your payment."
    ),
}


def _fallback_message(name: str, amount: float, strategy: str) -> str:
    template = TEMPLATE_MESSAGES.get(
        strategy,
        "Hi {name}, your payment of Rs.{amount:,.0f} didn't go through. Please try again.",
    )
    return template.format(name=name.split()[0], amount=amount)


def generate_recovery_message(name: str, amount: float, failure_reason: str,
                               strategy: str, rationale: str) -> str:
    """
    Returns a customer-facing recovery message.

    Uses the Anthropic API if ANTHROPIC_API_KEY is set in the environment;
    otherwise falls back to a template so the app always works out of the box.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback_message(name, amount, strategy)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        prompt = (
            f"Write a short, warm, 2-sentence message to a customer named "
            f"{name.split()[0]} whose payment of Rs.{amount:,.0f} failed due to "
            f"'{failure_reason}'. We plan to handle it via: {strategy} "
            f"(internal reason: {rationale}). Be reassuring, not apologetic or "
            f"robotic. Do not mention internal strategy names -- just tell the "
            f"customer what happens next in plain language."
        )
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception:
        # Any API error (bad key, rate limit, network) -> graceful fallback.
        # This is real, demo-able "failure recovery" behavior for the pitch.
        return _fallback_message(name, amount, strategy)
