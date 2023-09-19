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
    margin_amount = 10 * 10**6
    usdc_in = 90 * 10**6
    min_weth_out = int(0.081 * 10**18)

    uid, amount_bought = vault.open_position(
        owner,  # account
        weth,  # position_token
        min_weth_out,  # min_position_amount_out
        usdc,  # debt_token
        usdc_in,  # debt_amount
        margin_amount,  # margin_amount
    )

    return uid, amount_bought


def test_liquidate_001(vault, owner, alice, weth, usdc):
    """if the caller is not whitelisted the call should revert"""
    position_uid, _ = open_position(vault, owner, weth, usdc)
    with boa.env.prank(alice):
        with boa.reverts("unauthorized"):
            vault.liquidate(position_uid)


def test_liquidate_002(vault, owner, alice, weth, usdc):
    """if the position is not yet liquidateable the contract should revert"""
    position_uid, _ = open_position(vault, owner, weth, usdc)
    with boa.reverts("position not liquidateable"):
        vault.liquidate(position_uid)


def test_liquidate_003(vault, owner, alice, weth, usdc, eth_usd_oracle):
    """if the position is liquidateable it should not revert"""
    position_uid, _ = open_position(vault, owner, weth, usdc)
    eth_usd_oracle.set_answer(1234_0000_0000)

    # we have have a margin of 10USDC, borrow 90 and buy for 100 thus
    # our effective leverage is 10 as we have 10 times our margin-value in ETH
    assert vault.effective_leverage(position_uid) == 10
    eth_usd_oracle.set_answer(1133_0000_0000)
    assert vault.effective_leverage(position_uid) == 51
    vault.liquidate(position_uid)


def test_liquidate_004(vault, owner, alice, weth, usdc, eth_usd_oracle):
    """if the position is liquidated the position should be closed"""
    position_uid, _ = open_position(vault, owner, weth, usdc)
    eth_usd_oracle.set_answer(1133_0000_0000)

    # we have have a margin of 10USDC, borrow 90 and buy for 100 thus
    # our effective leverage is 10 as we have 10 times our margin-value in ETH
    vault.liquidate(position_uid)
    assert vault.positions(position_uid)[1:] == (
        "0x0000000000000000000000000000000000000000",
        "0x0000000000000000000000000000000000000000",
        0,
        0,
        "0x0000000000000000000000000000000000000000",
        0,
    )


def test_liquidate_005(vault, owner, alice, weth, usdc, eth_usd_oracle):
    """if the position is liquidated and there is enough swapped back to cover the
    the liquidation penalty it should be removed from the users margin"""

    margin_before = vault.margin(owner, usdc)

    fee = vault.trade_open_fee()
    safety_module_interest_share_percentage = vault.safety_module_interest_share_percentage()
    trading_fee_lp_share = vault.trading_fee_lp_share()

    penalty = 1_00  # 1%
    vault.set_fee_configuration(
        fee,
        penalty,
        safety_module_interest_share_percentage,
        trading_fee_lp_share
    )

    balance_penalty_receiver = usdc.balanceOf(
        "0x0000000000000000000000000000000000000066"
    )
    assert vault.liquidation_penalty() == penalty

    vault.set_liquidate_slippage_for_market(weth, usdc, 1_00)

    position_uid, _ = open_position(vault, owner, weth, usdc)

    # 10000000 is the margin used for the trade
    assert vault.margin(owner, usdc) == margin_before - 10000000
    
    eth_usd_oracle.set_answer(1234_0000_0000)
    assert vault.effective_leverage(position_uid) == 10

    vault.set_max_leverage_for_market(usdc, weth, 9) # make position liquidatable

    vault.liquidate(position_uid)

    # we are penalizing with 1% of the debt 
    penalty_amount = 900000
    assert (
        usdc.balanceOf("0x0000000000000000000000000000000000000066")
        == balance_penalty_receiver + penalty_amount
    )

    slippage_amount = 1045540
    assert vault.margin(owner, usdc) == margin_before - penalty_amount - slippage_amount


def test_liquidate_007(vault, owner, alice, weth, usdc, eth_usd_oracle):
    """if the position is liquidated and there is not enough swapped back to
    cover the the liquidation penalty the difference between the swap-back
    amount and the debt should be removed from the users margin"""
    margin_before = vault.margin(owner, usdc)

    fee = vault.trade_open_fee()
    safety_module_interest_share_percentage = vault.safety_module_interest_share_percentage()
    trading_fee_lp_share = vault.trading_fee_lp_share()

    penalty = 1_00  # 1%
    vault.set_fee_configuration(
        fee,
        penalty,
        safety_module_interest_share_percentage,
        trading_fee_lp_share
    )

    assert vault.liquidation_penalty() == penalty
    vault.set_liquidate_slippage_for_market(weth, usdc, 1_00)

    balance_penalty_receiver = usdc.balanceOf(
        "0x0000000000000000000000000000000000000066"
    )

    position_uid, _ = open_position(vault, owner, weth, usdc)

    # 10000000 is the margin used for the trade
    assert vault.margin(owner, usdc) == margin_before - 10000000
    eth_usd_oracle.set_answer(1130_0000_0000)

    vault.liquidate(position_uid)
    loss = 10000000  # we lost the whole margin

    # with ETH price of 1135 the pnl for the trader should be
    # 90_614_700  from this 9015650 would be transferred to the margin
    # as we are penalizing with 1% of the debt we remove 900000 this is more
    # then the user got back, thus we transfer onl 614_700, leaving the
    # users margin at a 100% loss

    penalty_amount = 614_700  # what can be deducted
    assert (
        usdc.balanceOf("0x0000000000000000000000000000000000000066")
        == balance_penalty_receiver + penalty_amount
    )

    assert vault.margin(owner, usdc) == margin_before - loss


def test_liquidate_008(vault, owner, alice, weth, usdc, eth_usd_oracle):
    """if the position is liquidated in bad debt nothing should be removed from
    the users margin"""
    margin_before = vault.margin(owner, usdc)
    
    fee = vault.trade_open_fee()
    safety_module_interest_share_percentage = vault.safety_module_interest_share_percentage()
    trading_fee_lp_share = vault.trading_fee_lp_share()

    penalty = 1_00  # 1%
    vault.set_fee_configuration(
        fee,
        penalty,
        safety_module_interest_share_percentage,
        trading_fee_lp_share
    )

    assert vault.liquidation_penalty() == penalty
    vault.set_liquidate_slippage_for_market(weth, usdc, 1_00)

    balance_penalty_receiver = usdc.balanceOf(
        "0x0000000000000000000000000000000000000066"
    )

    position_uid, _ = open_position(vault, owner, weth, usdc)

    assert vault.margin(owner, usdc) == margin_before - 10000000

    eth_usd_oracle.set_answer(1120_0000_0000)
    vault.liquidate(position_uid)
    loss = 10000000  # we lost the whole margin

    # with ETH price of 1125 the returned amount for the trader would be
    # 89812800, thus it would not be enought to pay back the debt and we would
    # be in bad debt. Accordingly there is not penalty to distribute and we will have bad debt

    penalty_amount = 0  # what can be
    assert (
        usdc.balanceOf("0x0000000000000000000000000000000000000066")
        == balance_penalty_receiver + penalty_amount
    )

    assert vault.margin(owner, usdc) == margin_before - loss
