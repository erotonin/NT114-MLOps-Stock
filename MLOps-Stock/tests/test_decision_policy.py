import pytest
from src.models_logic.decision_policy import DecisionContext, build_decision, label_action_from_realized_return, _clamp

def test_clamp():
    assert _clamp(5.0, 0.0, 10.0) == 5.0
    assert _clamp(-1.0, 0.0, 10.0) == 0.0
    assert _clamp(15.0, 0.0, 10.0) == 10.0

def test_build_decision_invalid_price():
    ctx = DecisionContext(current_price=-10.0, predicted_price=100.0, uncertainty_pct=1.0)
    res = build_decision(ctx)
    assert res.action == "HOLD"
    assert res.reason == "Invalid current price"
    assert res.confidence == 0.0
    assert res.expected_return_pct == 0.0

def test_build_decision_buy():
    # Buy when edge > hold_band_pct
    ctx = DecisionContext(current_price=100.0, predicted_price=105.0, uncertainty_pct=0.5)
    # gross = 5.0, net = 4.8, penalty = 0.35 => effective = 4.45 > 0.3
    res = build_decision(ctx, transaction_cost_pct=0.2, hold_band_pct=0.3, uncertainty_penalty=0.7)
    assert res.action == "BUY"
    assert "Positive expected edge" in res.reason

def test_build_decision_sell():
    # Sell when edge < -hold_band_pct
    ctx = DecisionContext(current_price=100.0, predicted_price=90.0, uncertainty_pct=0.5)
    # gross = -10.0, net = -10.2, penalty = 0.35 => effective = -10.55 < -0.3
    res = build_decision(ctx, transaction_cost_pct=0.2, hold_band_pct=0.3, uncertainty_penalty=0.7)
    assert res.action == "SELL"
    assert "Negative expected edge" in res.reason

def test_build_decision_hold():
    # Hold when inside band
    ctx = DecisionContext(current_price=100.0, predicted_price=100.1, uncertainty_pct=2.0)
    # gross = 0.1, net = -0.1, penalty = 1.4 => effective = -1.5 (Wait, if effective < -0.3 it becomes SELL)
    # Let's adjust to keep it in [-0.3, 0.3]
    # effective_edge_pct = (100.1-100)/100*100 - 0.2 - 0.7*0.0 = 0.1 - 0.2 = -0.1
    ctx2 = DecisionContext(current_price=100.0, predicted_price=100.1, uncertainty_pct=0.0)
    res = build_decision(ctx2, transaction_cost_pct=0.2, hold_band_pct=0.3, uncertainty_penalty=0.7)
    assert res.action == "HOLD"
    assert "inside hold band or too uncertain" in res.reason

def test_label_action_from_realized_return():
    assert label_action_from_realized_return(1.0, hold_band_pct=0.3) == "BUY"
    assert label_action_from_realized_return(-1.0, hold_band_pct=0.3) == "SELL"
    assert label_action_from_realized_return(0.1, hold_band_pct=0.3) == "HOLD"
    # test volatility override
    assert label_action_from_realized_return(1.0, hold_band_pct=0.3, realized_volatility_pct=4.0) == "HOLD" # band becomes 2.0
