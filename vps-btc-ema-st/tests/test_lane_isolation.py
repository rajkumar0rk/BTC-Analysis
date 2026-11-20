"""Prevent reusing one SQLite journal between paper, demo and live order engines."""
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest

APP=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(APP))
from store import Store

def test_paper_state_cannot_be_reused_for_exchange_orders(tmp_path):
    db=Store(tmp_path)
    db.claim_lane("BTC","futures","demo","futures_paper")
    db.paper_transition(100,None,{"kind":"paper_initialized"})
    db.close()
    second=Store(tmp_path)
    with pytest.raises(ValueError,match="different strategy lane"):
        second.claim_lane("BTC","futures","demo","futures_exchange")
    second.close()

def test_reusing_state_after_mode_change_is_blocked(tmp_path):
    db=Store(tmp_path)
    db.claim_lane("ETH","options","demo","options_paper")
    db.close()
    db=Store(tmp_path)
    with pytest.raises(ValueError,match="different strategy lane"):
        db.claim_lane("ETH","options","live","options_paper")
    with pytest.raises(ValueError,match="different strategy lane"):
        db.claim_lane("BTC","options","demo","options_paper")
    db.close()

def test_legacy_state_paper_wallet_blocks_exchange_claim(tmp_path):
    db=Store(tmp_path)
    db.set("paper_wallet",87.5)
    with pytest.raises(ValueError,match="paper wallet"):
        db.claim_lane("BTC","futures","demo","futures_exchange")
    db.close()

def test_legacy_exchange_intent_blocks_paper_claim(tmp_path):
    db=Store(tmp_path)
    db.intent("oldid","entry",{"product_id":27})
    with pytest.raises(ValueError,match="Exchange order"):
        db.claim_lane("BTC","futures","demo","futures_paper")
    db.close()
