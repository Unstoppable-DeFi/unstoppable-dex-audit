import pytest
import boa

BASE_LP = False


@pytest.fixture(autouse=True)
def setup(dex, mock_vault):
    dex.set_vault(mock_vault.address)

def test_adding_tp_sl_orders(dex, vault, owner, weth, usdc):
    trade_before = dex.open_trade(
        owner,  # account
        weth,  # position_token
        1 * 10**18,  # min_position_amount_out
        usdc,  # debt_token
        1000 * 10**6,  # debt_amount
        234 * 10**6,  # margin_amount
        [],  # tp 
        []   # sl orders
    )
    uid = trade_before[0]
    # struct Trade:
    #     uid: bytes32
    #     account: address
    #     vault_position_uid: bytes32
    #     tp_orders: DynArray[TakeProfitOrder, 8]
    #     sl_orders: DynArray[StopLossOrder, 8]

    # struct TakeProfitOrder:
    #     reduce_by_amount: uint256
    #     min_amount_out: uint256
    #     executed: bool
    new_tp_order = (123, 321, False)
    assert trade_before[3] == []
    dex.add_tp_order(uid, new_tp_order)

    trade_tp = dex.open_trades(uid)
    assert trade_tp[3] == [(123, 321, False)]
    

    # struct StopLossOrder:
    #     trigger_price: uint256
    #     reduce_by_amount: uint256
    #     executed: bool
    new_sl_order = (999, 321, False)
    assert trade_before[4] == []
    dex.add_sl_order(uid, new_sl_order)

    trade_sl = dex.open_trades(uid)
    assert trade_sl[4] == [(999, 321, False)]


def test_cancel_tp_sl_orders(dex, owner, weth, usdc):
    trade_before = dex.open_trade(
        owner,  # account
        weth,  # position_token
        1 * 10**18,  # min_position_amount_out
        usdc,  # debt_token
        1000 * 10**6,  # debt_amount
        234 * 10**6,  # margin_amount
        ((123, 321, False),),  # tp 
        ((888, 321, False), (999, 321, False))   # sl orders
    )
    uid = trade_before[0]
    dex.cancel_tp_order(uid, 0)
    dex.cancel_sl_order(uid, 1)

    trade_after = dex.open_trades(uid)

    assert trade_after[3] == []
    assert trade_after[4] == [(888, 321, False)]
