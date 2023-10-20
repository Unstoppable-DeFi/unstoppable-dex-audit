import pytest
import boa

BASE_LP = False


@pytest.fixture(autouse=True)
def setup(vault, mock_router, owner, usdc):
    vault.set_swap_router(mock_router.address)
    vault.set_is_whitelisted_dex(owner, True)
    usdc.approve(vault.address, 999999999999999999)
    vault.fund_account(usdc, 1000000000)
    vault.provide_liquidity(usdc, 1000000000000, False)


def test_open_position_records_position(vault, owner, weth, usdc):
    # _account: address,
    # _position_token: address,
    # _min_position_amount_out: uint256,
    # _debt_token: address,
    # _debt_amount: uint256,
    # _margin_amount: uint256
    uid, amount_bought = vault.open_position(
        owner,  # account
        weth,  # position_token
        1 * 10**18,  # min_position_amount_out
        usdc,  # debt_token
        1000 * 10**6,  # debt_amount
        234 * 10**6,  # margin_amount
    )

    assert uid != 0
    assert amount_bought != 0

    position = vault.positions(uid)

    # struct Position:
    #     uid: bytes32
    #     account: address
    #     debt_token: address
    #     margin_amount: uint256
    #     debt_shares: uint256
    #     position_token: address
    #     position_amount: uint256
    assert position[0] == uid
    assert position[1] == owner
    assert position[2].lower() == (usdc.address).lower()
    assert position[3] == 234 * 10**6
    assert position[4] == 1000 * 10**6 * 10**18
    assert position[5].lower() == (weth.address).lower()
    assert position[6] == 1 * 10**18


def test_open_position_records_total_debt_amount(vault, usdc, weth, owner):
    min_amount_out = 1 * 10**18
    debt_amount = 1000 * 10**6
    margin_amount = 234 * 10**6

    uid, amount_bought = vault.open_position(
        owner,  # account
        weth,  # position_token
        min_amount_out,  # min_position_amount_out
        usdc,  # debt_token
        debt_amount,  # debt_amount
        margin_amount,  # margin_amount
    )
    assert vault.total_debt_amount(usdc.address) == debt_amount


def test_open_position_records_total_debt_shares(vault, usdc, weth, owner):
    min_amount_out = 1 * 10**18
    debt_amount = 1000 * 10**6
    margin_amount = 234 * 10**6

    uid, amount_bought = vault.open_position(
        owner,  # account
        weth,  # position_token
        min_amount_out,  # min_position_amount_out
        usdc,  # debt_token
        debt_amount,  # debt_amount
        margin_amount,  # margin_amount
    )


def test_total_debt_plus_pending_interest(vault, usdc, weth, owner):
    min_amount_out = 1 * 10**18
    debt_amount = 1000 * 10**6
    margin_amount = 234 * 10**6

    uid, amount_bought = vault.open_position(
        owner,  # account
        weth,  # position_token
        min_amount_out,  # min_position_amount_out
        usdc,  # debt_token
        debt_amount,  # debt_amount
        margin_amount,  # margin_amount
    )
    debt_plus_interest = vault.internal._total_debt_plus_pending_interest(usdc.address)
    assert debt_plus_interest == debt_amount  # no time passed, so zero interest


def test_amount_per_debt_share_is_calculated_correctly(vault, usdc, weth, owner):
    min_amount_out = 1 * 10**18
    debt_amount = 1000 * 10**6
    margin_amount = 234 * 10**6

    uid, amount_bought = vault.open_position(
        owner,  # account
        weth,  # position_token
        min_amount_out,  # min_position_amount_out
        usdc,  # debt_token
        debt_amount,  # debt_amount
        margin_amount,  # margin_amount
    )

    amount_per_debt_share = vault.internal._amount_per_debt_share(usdc.address)
    assert amount_per_debt_share == 1 * 10**18


def test_debt_is_calculated_correctly(vault, usdc, weth, owner):
    min_amount_out = 1 * 10**18
    debt_amount = 1000 * 10**6
    margin_amount = 234 * 10**6

    uid, amount_bought = vault.open_position(
        owner,  # account
        weth,  # position_token
        min_amount_out,  # min_position_amount_out
        usdc,  # debt_token
        debt_amount,  # debt_amount
        margin_amount,  # margin_amount
    )

    assert vault.debt(uid) == debt_amount


def test_open_trade_swaps_liquidity_for_underlying(vault, owner, weth, usdc):
    """ensure that the available funds in the vault-contract are swapped according to the open-trade parameters"""
    liquidity_before = usdc.balanceOf(vault)
    underlying_before = weth.balanceOf(vault)

    margin_amount = 150 * 10**6
    min_borrow_amount = 1500 * 10**6
    min_position_amount = 3 * 10**18
    vault.open_position(
        owner, weth, min_position_amount, usdc, min_borrow_amount, margin_amount
    )

    liquidity_after = usdc.balanceOf(vault)
    underlying_after = weth.balanceOf(vault)

    assert liquidity_after == liquidity_before - min_borrow_amount - margin_amount
    assert underlying_after == underlying_before + min_position_amount


def test_open_trade_reduces_free_margin_correctly(vault, owner, usdc, weth, alice):
    margin_before = vault.margin(owner, usdc)

    margin_amount = 150 * 10**6
    min_borrow_amount = 1500 * 10**6
    min_position_amount = 3 * 10**18
    vault.open_position(
        owner, weth, min_position_amount, usdc, min_borrow_amount, margin_amount
    )

    # margin_after = vault.margin[owner][usdc.address]
    margin_after = vault.margin(owner, usdc)

    assert margin_after == margin_before - margin_amount


def test_open_position_records_amount_lent_out_correctly(vault, owner, usdc, weth):
    debt_before = vault.total_debt_amount(usdc)

    margin_amount = 150 * 10**6
    min_borrow_amount = 1500 * 10**6
    min_position_amount = 3 * 10**18
    vault.open_position(
        owner, weth, min_position_amount, usdc, min_borrow_amount, margin_amount
    )

    debt_after = vault.total_debt_amount(usdc)

    assert debt_after == debt_before + min_borrow_amount


def test_cannot_open_trade_with_more_margin_than_available(vault, owner, weth, usdc):
    margin_before = vault.margin(owner, usdc)
    margin_amount = margin_before + 1
    min_borrow_amount = 150 * 10**6
    min_position_amount = 123

    with boa.reverts("not enough margin"):
        vault.open_position(
            owner, weth, min_position_amount, usdc, min_borrow_amount, margin_amount
        )


def test_cannot_open_trade_with_higher_than_max_leverage(vault, owner, weth, usdc):
    max_leverage = vault.max_leverage(usdc, weth)
    print(max_leverage)

    margin_amount = 15 * 10**6
    min_borrow_amount = margin_amount * max_leverage + 1
    min_position_amount = 123

    with boa.reverts("cannot open liquidatable position"):
        vault.open_position(
            owner, weth, min_position_amount, usdc, min_borrow_amount, margin_amount
        )

def test_fee_is_charged(vault, owner, weth, usdc):
    margin_before = vault.margin(owner, usdc)

    open_trade_fee = 10 # 0.10%
    penalty = vault.liquidation_penalty()
    safety_module_interest_share_percentage = vault.safety_module_interest_share_percentage()
    trading_fee_lp_share = vault.trading_fee_lp_share()

    vault.set_fee_configuration(
        open_trade_fee,
        penalty,
        safety_module_interest_share_percentage,
        trading_fee_lp_share
    )

    assert vault.trade_open_fee() == 10 # 0.1%

    min_amount_out = 1 * 10**18
    debt_amount = 1000 * 10**6
    margin_amount = 234 * 10**6

    uid, _ = vault.open_position(
        owner,  # account
        weth,  # position_token
        min_amount_out,  # min_position_amount_out
        usdc,  # debt_token
        debt_amount,  # debt_amount
        margin_amount,  # margin_amount
    )

    margin_after = vault.margin(owner, usdc)
    expected_fee = (margin_amount + debt_amount) * 10 / 10000
    expected_margin_after = margin_before - margin_amount - expected_fee
    assert margin_after == expected_margin_after

def test_fee_is_distributed(vault, owner, weth, usdc):
    available_liquidity_before = vault.available_liquidity(usdc)

    open_trade_fee = 1_00 # 1%
    penalty = vault.liquidation_penalty()
    safety_module_interest_share_percentage = 60_00 # 60%
    trading_fee_lp_share = 80_00 # 80%

    vault.set_fee_configuration(
        open_trade_fee,
        penalty,
        safety_module_interest_share_percentage,
        trading_fee_lp_share
    )

    assert vault.trade_open_fee() == 1_00 # 1%
    assert vault.trading_fee_lp_share() == 80_00
    assert vault.safety_module_interest_share_percentage() == 60_00 # 60%

    min_amount_out = 1 * 10**18
    debt_amount = 1000 * 10**6
    margin_amount = 234 * 10**6

    uid, _ = vault.open_position(
        owner,  # account
        weth,  # position_token
        min_amount_out,  # min_position_amount_out
        usdc,  # debt_token
        debt_amount,  # debt_amount
        margin_amount,  # margin_amount
    )

    expected_fee = (margin_amount + debt_amount) * 100 / 10000 * 0.8

    available_liquidity_after = vault.available_liquidity(usdc)

    expected_available_liquidity_after = available_liquidity_before - debt_amount + expected_fee

    assert available_liquidity_after == expected_available_liquidity_after




# test open_position does not work if
# not accepting new orders
# not a whitelisted margin-dex
# not an enabled market
# the account still has margin
# the leverage is not to high
# there is still liquidity available
# margin is reduced correctly
# debt_shares are saved to the position
# swap is executed with the correct amount thus amount bought is correct
# position struct is set correctly with the above information
