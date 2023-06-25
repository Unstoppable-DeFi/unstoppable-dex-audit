import pytest

@pytest.fixture(autouse=True)
def setup(dex, mock_vault):
    dex.set_vault(mock_vault.address)

def test_post_limit_order(dex, owner, usdc, weth):
    # post_limit_order(
    # _account: address,
    # _position_token: address,
    # _debt_token: address,
    # _margin_amount: uint256,
    # _debt_amount: uint256,
    # _min_amount_out: uint256, 
    # _valid_until: uint256,
    # _tp_orders: DynArray[TakeProfitOrder, 8],
    # _sl_orders: DynArray[StopLossOrder, 8]
    # ):

    limit_order = dex.post_limit_order(
        owner,
        weth,
        usdc,
        100 * 10**6,
        900 * 10**6,
        1 * 10**18,
        999999999999,
        [],
        []
    )

    uid = limit_order[0]

    assert limit_order == dex.limit_orders(uid)

    # struct LimitOrder:
    #     uid: bytes32
    #     account: address
    #     position_token: address
    #     min_position_amount_out: uint256
    #     debt_token: address
    #     margin_amount: uint256
    #     debt_amount: uint256
    #     valid_until: uint256
    #     tp_orders: DynArray[TakeProfitOrder, 8]
    #     sl_orders: DynArray[StopLossOrder, 8]
    assert limit_order[1] == owner
    assert limit_order[2] == weth.address
    assert limit_order[3] == 1 * 10**18
    assert limit_order[4] == usdc.address
    assert limit_order[5] == 100 * 10**6
    assert limit_order[6] == 900 * 10**6
    assert limit_order[7] == 999999999999
    assert limit_order[8] == []
    assert limit_order[9] == []
