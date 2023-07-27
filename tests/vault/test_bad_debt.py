import pytest


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
    min_weth_out = 1 * 10**18

    uid, amount_bought = vault.open_position(
        owner,  # account
        weth,  # position_token
        min_weth_out,  # min_position_amount_out
        usdc,  # debt_token
        usdc_in,  # debt_amount
        margin_amount,  # margin_amount
    )

    return uid, amount_bought


def test_repay_bad_debt_001(vault, usdc, weth, owner):
    """when bad-debt is repaid it should be reduced in the vault,
    the available-liquidity should go up correspondentingly"""
    bad_debt_before = vault.bad_debt(usdc)
    position_uid, _ = open_position(vault, owner, weth, usdc)
    bad_debt_before = vault.bad_debt(usdc)
    assert bad_debt_before == 0

    vault.positions(position_uid)
    vault.internal._close_position(position_uid, 1)  # 1 wei out
    bad_debt_after = vault.bad_debt(usdc)

    assert bad_debt_after == 150 * 10**6 - 1
    assert vault.available_liquidity(usdc) == 999700000002

    vault.repay_bad_debt(usdc, bad_debt_after)
    bad_debt_after_repaying = vault.bad_debt(usdc)
    assert bad_debt_after_repaying == 0

    assert vault.available_liquidity(usdc) == 999700000002 + bad_debt_after 


def test_base_lp_is_impacted_by_bad_debt_if_safety_module_doesnt_cover_it_all(vault, usdc, weth, owner):
    safety_module_amount = 50_000_0000000
    base_lp_amount = 100_000_0000000
    vault.provide_liquidity(usdc, safety_module_amount, True)

    assert vault.bad_debt(usdc) == 0
    assert vault.safety_module_lp_total_amount(usdc) == safety_module_amount
    assert vault.base_lp_total_amount(usdc) == base_lp_amount

    base_lp_value_before = vault.lp_shares_to_amount(usdc, 1 * 10**36, False)
    safety_module_lp_value_before = vault.lp_shares_to_amount(usdc, 1 * 10**36, True)

    vault.eval(f"self.bad_debt[{usdc.address}] = {int(safety_module_amount/2)}")

    assert vault.lp_shares_to_amount(usdc, 1 * 10**36, True) == safety_module_lp_value_before/2
    assert vault.lp_shares_to_amount(usdc, 1 * 10**36, False) == base_lp_value_before

    vault.eval(f"self.bad_debt[{usdc.address}] = {safety_module_amount}")

    assert vault.lp_shares_to_amount(usdc, 1 * 10**36, True) == 0
    assert vault.lp_shares_to_amount(usdc, 1 * 10**36, False) == base_lp_value_before
    
    vault.eval(f"self.bad_debt[{usdc.address}] = {safety_module_amount + int(base_lp_amount/2)}")
    
    assert vault.lp_shares_to_amount(usdc, 1 * 10**36, True) == 0
    assert vault.lp_shares_to_amount(usdc, 1 * 10**36, False) == base_lp_value_before/2