import pytest
import boa

@pytest.fixture(autouse=True)
def setup(dex, mock_vault):
    dex.set_vault(mock_vault.address)


def test_open_trade_does_not_revert(dex, vault, owner, weth, usdc):
    before = dex.get_all_open_trades(owner)
    assert len(before) == 0

    dex.open_trade(
        owner,  # account
        weth,  # position_token
        1 * 10**18,  # min_position_amount_out
        usdc,  # debt_token
        1000 * 10**6,  # debt_amount
        234 * 10**6,  # margin_amount
        [],  # tp orders
        []   # sl orders
    )

    after = dex.get_all_open_trades(owner)
    assert len(after) == 1


def test_open_trade_creates_trade_struct(dex, owner, weth, usdc, mock_vault):
    margin_amount = 15 * 10**6
    usdc_in = 150 * 10**6
    min_weth_out = 123
    trade = dex.open_trade(owner, weth, min_weth_out, usdc, usdc_in, margin_amount, [], [])

    # struct Trade:
    #     uid: bytes32
    #     account: address
    #     vault_position_uid: bytes32
    #     tp_orders: DynArray[TakeProfitOrder, 8]
    #     sl_orders: DynArray[StopLossOrder, 8]
    # assert trade[0] == 'uid'                     # uid
    assert trade[1] == owner  # account
    assert trade[2] == mock_vault.op_uid()  # debt_token
    assert trade[3] == []  # tp orders
    assert trade[4] == []  # sl orders


def test_open_trade_is_recorded_correctly(dex, owner, weth, usdc, mock_vault):
    margin_amount = 15 * 10**6
    usdc_in = 150 * 10**6
    min_weth_out = 123
    trade = dex.open_trade(owner, weth, min_weth_out, usdc, usdc_in, margin_amount, [], [])

    trades = dex.get_all_open_trades(owner)
    assert len(trades) == 1
    assert trade[0] == trades[0][0]

def test_cleanup_trade(dex, owner, weth, usdc, mock_vault):
    margin_amount = 15 * 10**6
    usdc_in = 150 * 10**6
    min_weth_out = 123
    trade = dex.open_trade(owner, weth, min_weth_out, usdc, usdc_in, margin_amount, [], [])

    trades = dex.get_all_open_trades(owner)
    assert len(trades) == 1
    
    dex.internal._cleanup_trade(trade[0])

    trades_after = dex.get_all_open_trades(owner)
    assert len(trades_after) == 0