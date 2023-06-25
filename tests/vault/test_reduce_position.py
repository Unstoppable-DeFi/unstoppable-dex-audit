import pytest
import boa

BASE_LP = False


@pytest.fixture(autouse=True)
def setup(vault, mock_router, owner, usdc, weth):
    vault.set_swap_router(mock_router.address)
    vault.set_is_whitelisted_dex(owner, True)
    usdc.approve(vault.address, 999999999999999999)
    vault.fund_account(usdc.address, 1000000000)
    vault.provide_liquidity(usdc, 1000000000000, False)


def test_reduce_position(vault, owner, weth, usdc, mock_router, eth_usd_oracle):
    eth_usd_oracle.set_answer(9300_00000000)
    assert vault.swap_router() == mock_router.address

    uid, amount_bought = vault.open_position(
        owner,  # account
        weth,  # position_token
        1 * 10**18,  # min_position_amount_out
        usdc,  # debt_token
        9000 * 10**6,  # debt_amount
        300 * 10**6,  # margin_amount
    )


    # struct Position:
    # uid: bytes32
    # account: address
    # debt_token: address
    # margin_amount: uint256
    # debt_shares: uint256
    # position_token: address
    # position_amount: uint256
    position_before = vault.positions(uid)
    position_amount_before = position_before[6]
    assert position_amount_before == 1 * 10**18

    margin_amount_before = position_before[3]
    assert margin_amount_before == 300 * 10**6
    
    
    debt_amount_before = vault.debt(uid)
    assert debt_amount_before == 9000 * 10**6

    assert vault.debt(uid) > 0

    vault.reduce_position(uid, int(position_amount_before/3), 3100 * 10**6)

    position_after = vault.positions(uid)

    debt_amount_after = vault.debt_shares_to_amount(usdc.address, position_after[4])
    assert debt_amount_after == pytest.approx(6000 * 10**6, 10000000)

    margin_amount_after = position_after[3]
    assert margin_amount_after == pytest.approx(200 * 10**6, 1000000)

    position_amount_after = position_after[6]
    assert position_amount_after == pytest.approx(int(1 * 10**18 / 3 * 2), 1000)


# def test_mock_swap_router(mock_router, usdc, weth, owner):
#     before = weth.balanceOf(owner)

#     min_amount_out = 1* 10**18
#     amount_out = mock_router.swap(usdc.address, weth.address, 1 * 10**6, min_amount_out)
#     after = weth.balanceOf(owner)

#     assert after == before + min_amount_out