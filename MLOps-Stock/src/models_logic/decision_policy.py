from dataclasses import dataclass


@dataclass
class DecisionContext:
    current_price: float
    predicted_price: float
    # Model disagreement in percentage points of current price.
    uncertainty_pct: float


@dataclass
class DecisionResult:
    action: str
    expected_return_pct: float
    confidence: float
    reason: str


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def build_decision(
    ctx: DecisionContext,
    transaction_cost_pct: float = 0.2,
    hold_band_pct: float = 0.3,
    uncertainty_penalty: float = 0.7,
    realized_volatility_pct: float = 0.0,
) -> DecisionResult:
    """
    Convert regression forecast into an actionable HOLD/BUY/SELL decision.

    - transaction_cost_pct: round-trip execution cost approximation (percent).
    - hold_band_pct: minimum expected edge to avoid over-trading (percent).
    - uncertainty_penalty: how strongly model disagreement reduces confidence.
    """
    if ctx.current_price <= 0:
        return DecisionResult(
            action="HOLD",
            expected_return_pct=0.0,
            confidence=0.0,
            reason="Invalid current price",
        )

    gross_return_pct = ((ctx.predicted_price - ctx.current_price) / ctx.current_price) * 100.0

    # Adapt hold threshold by recent volatility to reduce over-trading in noisy regimes.
    dynamic_hold_band = max(hold_band_pct, 0.5 * realized_volatility_pct)

    # Penalize for estimated costs and uncertainty.
    net_return_pct = gross_return_pct - transaction_cost_pct
    disagreement_penalty = uncertainty_penalty * abs(ctx.uncertainty_pct)
    effective_edge_pct = net_return_pct - disagreement_penalty

    # Confidence is based on model agreement and edge magnitude.
    agreement = 1.0 / (1.0 + abs(ctx.uncertainty_pct))
    edge_score = min(abs(effective_edge_pct) / max(dynamic_hold_band, 1e-6), 2.0) / 2.0
    confidence = _clamp(0.55 * agreement + 0.45 * edge_score, 0.0, 1.0)

    if effective_edge_pct > dynamic_hold_band:
        # nosemgrep: hardcoded-password-assignment
        action = "BUY"
        # nosemgrep: hardcoded-password-assignment
        reason = "Positive expected edge after costs and uncertainty adjustment"
    elif effective_edge_pct < -dynamic_hold_band:
        # nosemgrep: hardcoded-password-assignment
        action = "SELL"
        # nosemgrep: hardcoded-password-assignment
        reason = "Negative expected edge after costs and uncertainty adjustment"
    else:
        # nosemgrep: hardcoded-password-assignment
        action = "HOLD"
        # nosemgrep: hardcoded-password-assignment
        reason = "Signal is inside hold band or too uncertain"

    return DecisionResult(
        action=action,
        expected_return_pct=float(effective_edge_pct),
        confidence=float(confidence),
        reason=reason,
    )


def label_action_from_realized_return(
    realized_return_pct: float,
    hold_band_pct: float = 0.3,
    realized_volatility_pct: float = 0.0,
) -> str:
    """Label realized market move into BUY/SELL/HOLD for evaluation metrics."""
    dynamic_hold_band = max(hold_band_pct, 0.5 * realized_volatility_pct)
    if realized_return_pct > dynamic_hold_band:
        return "BUY"
    if realized_return_pct < -dynamic_hold_band:
        return "SELL"
    return "HOLD"
