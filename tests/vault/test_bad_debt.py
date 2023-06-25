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


def test_repay_bad_debt_001(vault, usdc, weth, owner):
    """when bad-debt is repayd it should be reduced in the vault,
    the available-liquidity should go up correspondentingly"""
    bad_debt_before = vault.bad_debt(usdc)
    position_uid, _ = open_position(vault, owner, weth, usdc)
    bad_debt_before = vault.bad_debt(usdc)
    assert bad_debt_before == 0

    vault.positions(position_uid)
    vault.close_position(position_uid, 0)  # 0 out
    bad_debt_after = vault.bad_debt(usdc)

    assert bad_debt_after == 150 * 10**6
    assert vault.available_liquidity(usdc) == 999700000000

    vault.repay_bad_debt(usdc, 150 * 10**6)
    bad_debt_after_repaying = vault.bad_debt(usdc)
    assert bad_debt_after_repaying == 0

    assert vault.available_liquidity(usdc) == 999700000000 + 150 * 10**6
