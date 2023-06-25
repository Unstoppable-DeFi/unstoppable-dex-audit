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


def test_initial_debt_shares_are_calculated_correctly(vault, usdc, weth):
    amount_1 = 123 * 10**6
    assert vault.total_debt_shares(usdc.address) == 0
    debt_shares_1 = vault.internal._amount_to_debt_shares(usdc.address, amount_1)

    assert debt_shares_1 == amount_1 * 10**18


def test_multiple_debt_shares_are_recorded_correctly(vault, usdc, alice):
    before = vault.total_debt_shares(usdc.address)
    assert before == 0

    amount = 100 * 10**6
    debt_shares_1 = vault.internal._borrow(usdc.address, amount)
    assert vault.total_debt_shares(usdc) == amount * 10**18
    assert vault.total_debt_amount(usdc) == amount
    assert debt_shares_1 == amount * 10**18

    amount_2 = 30 * 10**6
    debt_shares_2 = vault.internal._borrow(usdc.address, amount_2)

    assert vault.total_debt_amount(usdc) == (amount + amount_2)
    assert vault.total_debt_shares(usdc) == (amount + amount_2) * 10**18
    assert debt_shares_2 == amount_2 * 10**18


def test_full_circle_amount_to_debt_shares_to_amount(vault, usdc):
    amount_in = 1234567890
    debt_shares_1 = vault.internal._borrow(usdc.address, amount_in)
    amount_out = vault.debt_shares_to_amount(usdc.address, debt_shares_1)

    assert amount_out == amount_in
