import pytest
import boa

BASE_LP = False

@pytest.fixture(autouse=True)
def setup(vault, mock_router, owner, usdc, weth):
    vault.set_swap_router(mock_router.address)
    vault.set_is_whitelisted_dex(owner, True)
    usdc.approve(vault.address, 999999999999999999)
    vault.fund_account(usdc.address, 1000000000)
    vault.provide_liquidity(usdc, 1000000000000, BASE_LP)


def test_can_add_margin(vault, owner, weth, usdc, mock_router, eth_usd_oracle):
    uid, _ = vault.open_position(
        owner,  # account
        weth,  # position_token
        1 * 10**18,  # min_position_amount_out
        usdc,  # debt_token
        900 * 10**6,  # debt_amount
        100 * 10**6,  # margin_amount
    )

    # struct Position:
    #     uid: bytes32
    #     account: address
    #     debt_token: address
    #     margin_amount: uint256
    #     debt_shares: uint256
    #     position_token: address
    #     position_amount: uint256
    position_before = vault.positions(uid)
    margin_before = position_before[3]
    assert margin_before == 100 * 10**6

    vault.add_margin(uid, 100 * 10**6)

    position_after = vault.positions(uid)
    margin_after = position_after[3]
    assert margin_after == margin_before + 100 * 10**6

def test_can_remove_margin(vault, owner, weth, usdc, mock_router, eth_usd_oracle):
    uid, _ = vault.open_position(
        owner,  # account
        weth,  # position_token
        1 * 10**18,  # min_position_amount_out
        usdc,  # debt_token
        900 * 10**6,  # debt_amount
        100 * 10**6,  # margin_amount
    )

    # struct Position:
    #     uid: bytes32
    #     account: address
    #     debt_token: address
    #     margin_amount: uint256
    #     debt_shares: uint256
    #     position_token: address
    #     position_amount: uint256
    position_before = vault.positions(uid)
    margin_before = position_before[3]
    assert margin_before == 100 * 10**6

    vault.remove_margin(uid, 10 * 10**6)

    position_after = vault.positions(uid)
    margin_after = position_after[3]
    assert margin_after == margin_before - 10 * 10**6

def test_cannot_remove_more_than_margin(vault, owner, weth, usdc, mock_router, eth_usd_oracle):
    uid, _ = vault.open_position(
        owner,  # account
        weth,  # position_token
        1 * 10**18,  # min_position_amount_out
        usdc,  # debt_token
        900 * 10**6,  # debt_amount
        100 * 10**6,  # margin_amount
    )

    # struct Position:
    #     uid: bytes32
    #     account: address
    #     debt_token: address
    #     margin_amount: uint256
    #     debt_shares: uint256
    #     position_token: address
    #     position_amount: uint256
    position_before = vault.positions(uid)
    margin_before = position_before[3]
    assert margin_before == 100 * 10**6

    with boa.reverts("not enough margin"):
        vault.remove_margin(uid, 110 * 10**6)

def test_cannot_remove_too_much_margin(vault, owner, weth, usdc, mock_router, eth_usd_oracle):
    uid, _ = vault.open_position(
        owner,  # account
        weth,  # position_token
        1 * 10**18,  # min_position_amount_out
        usdc,  # debt_token
        900 * 10**6,  # debt_amount
        100 * 10**6,  # margin_amount
    )

    # struct Position:
    #     uid: bytes32
    #     account: address
    #     debt_token: address
    #     margin_amount: uint256
    #     debt_shares: uint256
    #     position_token: address
    #     position_amount: uint256
    position_before = vault.positions(uid)
    margin_before = position_before[3]
    assert margin_before == 100 * 10**6

    eth_usd_oracle.set_answer(910_00000000)

    assert vault.internal._calculate_leverage(910, 900, 10) == 91
    assert vault.max_leverage(weth, usdc) == 50

    with boa.reverts("exceeds max leverage"):
        vault.remove_margin(uid, 90 * 10**6)