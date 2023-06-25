import pytest
import boa


@pytest.fixture(scope="session")
def setup(vault, mock_router, owner, weth, usdc):
    vault.set_swap_router(mock_router.address)
    vault.set_is_whitelisted_dex(owner, True)
    usdc.approve(vault.address, 999999999999999999)
    vault.fund_account(usdc, 1000000000)
    vault.provide_liquidity(usdc, 1000000000000, False)


def open_position(vault, owner, weth, usdc):
    margin_amount = 15 * 10**6
    usdc_in = 150 * 10**6
    min_weth_out = 123

    uid, amount_bought = vault.open_position(
        owner,  # account
        weth,  # position_token
        min_weth_out,  # min_position_amount_out
        usdc,  # debt_token
        usdc_in,  # debt_amount
        margin_amount,  # margin_amount
    )

    return uid, amount_bought


def test_non_whitelisted_address_cannot_open_a_positions(
    vault, owner, alice, weth, usdc
):
    with boa.env.prank(alice):
        with boa.reverts("unauthorized"):
            open_position(vault, owner, weth, usdc)


def test_close_position_reduces_position_to_zero(vault, owner, weth, usdc):
    position_uid, _ = open_position(vault, owner, weth, usdc)
    position_before = vault.positions(position_uid)

    assert position_before[6] > 0  # [6] = postion_amount

    vault.close_position(position_uid, 150 * 10**6)
    position_after = vault.positions(position_uid)

    assert position_after[6] == 0  # [6] = position_amount


def test_close_position_swaps_liquidity_for_underlying(vault, weth, usdc, owner):
    position_uid, _ = open_position(vault, owner, weth, usdc)
    liquidity_before = usdc.balanceOf(vault)
    underlying_before = weth.balanceOf(vault)

    weth_in = 123
    min_usdc_out = 150 * 10**6
    vault.close_position(position_uid, min_usdc_out)

    liquidity_after = usdc.balanceOf(vault)
    underlying_after = weth.balanceOf(vault)

    assert liquidity_after == liquidity_before + min_usdc_out
    assert underlying_after == underlying_before - weth_in


def test_close_position_in_profit_increases_margin(vault, weth, usdc, owner):
    position_uid, _ = open_position(vault, owner, weth, usdc)

    account_margin_after_trade_open = vault.margin(owner, usdc)

    position = vault.positions(position_uid)
    position_margin = position[3]
    assert position_margin == 15 * 10**6

    min_usdc_out = (
        250 * 10**6
    )  # simulated profit of 100 in addition to initial (margin + borrowed)
    vault.close_position(position_uid, min_usdc_out)

    margin_after = vault.margin(owner, usdc)

    expected_pnl = 85 * 10**6
    assert (
        margin_after == account_margin_after_trade_open + position_margin + expected_pnl
    )


def test_close_position_in_loss_reduces_margin(vault, usdc, weth, owner):
    position_uid, _ = open_position(vault, owner, weth, usdc)
    account_margin_after_trade_open = vault.margin(owner, usdc)

    position = vault.positions(position_uid)
    position_margin = position[3]

    # position-supply = debt + margin = 150 + 15
    expected_loss = 10 * 10**6
    min_usdc_out = 165 * 10**6 - expected_loss  # simulated loss of 10
    vault.close_position(position_uid, min_usdc_out)

    margin_after = vault.margin(owner, usdc)

    assert (
        margin_after
        == account_margin_after_trade_open + position_margin - expected_loss
    )  # 150-140


def test_reduce_position_partially_reduces_debt(vault, usdc, weth, owner):
    margin_amount = 15 * 10**6
    usdc_in = 150 * 10**6
    min_weth_out = 123 * 10**18

    position_uid, _ = vault.open_position(
        owner,  # account
        weth,  # position_token
        min_weth_out,  # min_position_amount_out
        usdc,  # debt_token
        usdc_in,  # debt_amount
        margin_amount,  # margin_amount
    )

    debt_shares_before = vault.positions(position_uid)[4]

    assert debt_shares_before > 0
    assert vault.positions(position_uid)[6] == 123 * 10**18

    vault.reduce_position(position_uid, 1 * 10**18, 5 * 10**6)

    assert vault.positions(position_uid)[6] == 122 * 10**18

    debt_shares_after_reduce = vault.positions(position_uid)[4]

    # we have a margin of 15 and a debt of 150, the margin to debt ratio is
    # 15/165 = 0.0909.. accordingly we are reducing the margin by 0.45
    # and the debt by 4.55
    expected_debt_shares = 145500000000000000000000000
    assert debt_shares_after_reduce == expected_debt_shares


def test_close_position_in_bad_debt_records_bad_debt(vault, usdc, weth, owner):
    position_uid, _ = open_position(vault, owner, weth, usdc)
    bad_debt_before = vault.bad_debt(usdc)
    assert bad_debt_before == 0

    vault.positions(position_uid)
    vault.close_position(position_uid, 0)  # 0 out
    bad_debt_after = vault.bad_debt(usdc)

    # TODO ensure position-debt is here the correct value
    # we are minting new bad-debt shares and it is the first
    # position, thus all share-positions should now be bad-debt
    # that means all the 150 that where borrowed are now bad debt
    assert bad_debt_after == 150 * 10**6


def test_close_position_in_bad_debt_deactivates_accepting_new_orders(
    vault, usdc, weth, owner
):
    position_uid, _ = open_position(vault, owner, weth, usdc)
    assert vault.is_accepting_new_orders()
    vault.positions(position_uid)

    vault.close_position(position_uid, 0)  # 0 out

    bad_debt_after = vault.bad_debt(usdc)

    assert bad_debt_after > 0
    assert vault.is_accepting_new_orders() is False
