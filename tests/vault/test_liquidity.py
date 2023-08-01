import pytest
import boa

BASE_LP = False
SAFETY_MODULE = True


@pytest.fixture(scope="session")
def setup(owner, vault, weth, usdc, alice):
    weth.approve(vault, 1000 * 10**18)
    usdc.approve(vault, 1000000 * 10**6)
    with boa.env.prank(alice):
        usdc.approve(vault, 1000000 * 10**6)


def test_provide_liquidity_liqudity_records_total_amount(vault, usdc, owner):
    before = vault.base_lp_total_amount(usdc)

    amount = 100 * 10**6
    vault.provide_liquidity(usdc, amount, BASE_LP)

    after = vault.base_lp_total_amount(usdc)

    assert after == before + amount


def test_first_provide_liquidity_records_user_shares(vault, usdc, owner):
    before = vault.base_lp_shares(usdc, owner)

    amount = 100 * 10**6
    vault.provide_liquidity(usdc, amount, BASE_LP)

    after = vault.base_lp_shares(usdc, owner)

    assert after == before + amount * 10**18 - 1


def test_first_provide_liquidity_records_total_shares(vault, usdc, owner):
    before = vault.base_lp_total_shares(usdc)

    amount = 100 * 10**6
    vault.provide_liquidity(usdc, amount, BASE_LP)

    after = vault.base_lp_total_shares(usdc)

    assert after == before + amount * 10**18 - 1


def test_multiple_provide_record_shares_correctly(vault, usdc, owner, alice):
    before_total_shares = vault.base_lp_total_shares(usdc)
    before_owner_shares = vault.base_lp_shares(usdc, owner)
    before_alice_shares = vault.base_lp_shares(usdc, alice)

    amount = 100 * 10**6
    vault.provide_liquidity(usdc, amount, BASE_LP)
    assert vault.base_lp_total_shares(usdc) == before_total_shares + amount * 10**18 - 1
    assert vault.base_lp_shares(usdc, owner) == before_owner_shares + amount * 10**18 - 1

    with boa.env.prank(alice):
        amount_2 = 30 * 10**6
        vault.provide_liquidity(usdc, amount_2, BASE_LP)

    assert vault.base_lp_total_shares(usdc) == before_total_shares + (amount + amount_2) * 10**18 - 1 - 1
    assert vault.base_lp_shares(usdc, owner) == before_owner_shares + amount * 10**18 - 1
    assert vault.base_lp_shares(usdc, alice) == before_alice_shares + amount_2 * 10**18 - 1


def test_shares_to_amount_are_calculated_correctly(vault, usdc):
    amount = 100 * 10**6

    # first shares
    vault.eval(f"self.base_lp_total_shares[{usdc.address}] = {0}")
    vault.eval(f"self.base_lp_total_amount[{usdc.address}] = {0}")
    assert (
        vault.internal._amount_to_lp_shares(usdc, amount, BASE_LP) == amount * 10**18
    )

    # second shares, no profits yet
    vault.eval(f"self.base_lp_total_shares[{usdc.address}] = {amount * 10**18}")
    vault.eval(f"self.base_lp_total_amount[{usdc.address}] = {amount}")
    assert (
        vault.internal._amount_to_lp_shares(usdc, amount, BASE_LP) == amount * 10**18
    )

    # second shares, previous profit
    vault.eval(f"self.base_lp_total_shares[{usdc.address}] = {amount * 10**18}")
    vault.eval(f"self.base_lp_total_amount[{usdc.address}] = {2*amount}")
    assert (
        vault.internal._amount_to_lp_shares(usdc, amount, BASE_LP)
        == int(amount / 2) * 10**18
    )

    # second shares, previous loss
    vault.eval(f"self.base_lp_total_shares[{usdc.address}] = {amount * 10**18}")
    vault.eval(f"self.base_lp_total_amount[{usdc.address}] = {int(amount/2)}")
    assert (
        vault.internal._amount_to_lp_shares(usdc, amount, BASE_LP)
        == amount * 2 * 10**18
    )


def test_amount_to_shares_are_calculated_correctly(vault, usdc):
    assert vault.internal._lp_shares_to_amount(usdc, 0, BASE_LP) == 0

    vault.eval(f"self.base_lp_total_shares[{usdc.address}] = {1}")
    vault.eval(f"self.base_lp_total_amount[{usdc.address}] = {1}")
    assert vault.internal._lp_shares_to_amount(usdc, 1, BASE_LP) == 1

    vault.eval(f"self.base_lp_total_shares[{usdc.address}] = {1}")
    vault.eval(f"self.base_lp_total_amount[{usdc.address}] = {2}")
    assert vault.internal._lp_shares_to_amount(usdc, 1, BASE_LP) == 2
    assert vault.internal._lp_shares_to_amount(usdc, 2, BASE_LP) == 4


def test_amount_to_shares_to_amount_is_calculated_correctly(vault, usdc):
    vault.provide_liquidity(usdc, 9876543210, BASE_LP)

    amount = 123456789
    shares = vault.internal._amount_to_lp_shares(usdc, amount, BASE_LP)

    assert vault.internal._lp_shares_to_amount(usdc, shares, BASE_LP) == amount


def test_withdraw_liquidity_reduces_total_shares(vault, usdc, owner):
    vault.provide_liquidity(usdc.address, 100 * 10**6, BASE_LP)
    before = vault.base_lp_total_shares(usdc)

    withdraw_amount = 50 * 10**6
    withdraw_shares = vault.internal._amount_to_lp_shares(
        usdc, withdraw_amount, BASE_LP
    )
    vault.withdraw_liquidity(usdc, withdraw_amount, BASE_LP)

    after = vault.base_lp_total_shares(usdc)

    assert after == before - withdraw_shares


def test_withdraw_liquidity_reduces_user_shares(vault, usdc, owner):
    vault.provide_liquidity(usdc.address, 100 * 10**6, BASE_LP)
    before = vault.base_lp_shares(usdc, owner)

    withdraw_amount = 50 * 10**6
    withdraw_shares = vault.internal._amount_to_lp_shares(
        usdc, withdraw_amount, BASE_LP
    )
    vault.withdraw_liquidity(usdc, withdraw_amount, BASE_LP)

    after = vault.base_lp_shares(usdc, owner)

    assert after == before - withdraw_shares


def test_withdraw_liquidity_reduces_total_amount(vault, usdc, owner):
    vault.provide_liquidity(usdc, 100 * 10**6, BASE_LP)
    before = vault.base_lp_total_amount(usdc)

    withdraw_amount = 50 * 10**6
    vault.withdraw_liquidity(usdc, withdraw_amount, BASE_LP)

    after = vault.base_lp_total_amount(usdc)

    assert after == before - withdraw_amount


def test_cannot_withdraw_more_than_you_own(vault, usdc, owner, alice):
    amount = 100 * 10**6
    vault.provide_liquidity(usdc, amount, BASE_LP)

    with boa.env.prank(alice):
        vault.provide_liquidity(usdc, amount, BASE_LP)

    alice_shares = vault.base_lp_shares(usdc, alice)
    alice_amount = vault.lp_shares_to_amount(usdc, alice_shares, BASE_LP)
    assert alice_amount == amount - 1
    assert alice_shares == amount * 10**18 - 1

    with boa.env.prank(alice):
        with boa.reverts("cannot withdraw more than you own"):
            vault.withdraw_liquidity(usdc, alice_amount + 1, BASE_LP)


def test_provide_liquidity_transfers_tokens(vault, usdc, owner):
    amount = 100 * 10**6
    owner_balance_before = usdc.balanceOf(owner)
    assert owner_balance_before >= amount

    vault_balance_before = usdc.balanceOf(vault)

    vault.provide_liquidity(usdc, amount, BASE_LP)

    owner_balance_after = usdc.balanceOf(owner)
    vault_balance_after = usdc.balanceOf(vault)

    assert owner_balance_after == owner_balance_before - amount
    assert vault_balance_after == vault_balance_before + amount


def test_withdraw_liquidity_transfers_tokens(vault, usdc, owner):
    amount = 100 * 10**6
    vault.provide_liquidity(usdc, amount, BASE_LP)

    owner_balance_before = usdc.balanceOf(owner)
    vault_balance_before = usdc.balanceOf(vault)
    assert vault_balance_before >= amount

    vault.withdraw_liquidity(usdc, amount - 1, BASE_LP)

    owner_balance_after = usdc.balanceOf(owner)
    vault_balance_after = usdc.balanceOf(vault)

    assert vault_balance_after == vault_balance_before - amount + 1
    assert owner_balance_after == owner_balance_before + amount - 1


def test_available_liquidty_is_calculated_correctly(vault, usdc):
    amount = 100 * 10**6
    vault.eval(f"self.base_lp_total_amount[{usdc.address}] = {amount}")
    vault.eval(f"self.safety_module_lp_total_amount[{usdc.address}] = {0}")
    vault.eval(f"self.total_debt_amount[{usdc.address}] = {int(amount/4)}")
    vault.eval(f"self.bad_debt[{usdc.address}] = {int(amount/4)}")

    assert vault.available_liquidity(usdc) == int(amount / 2)


def test_borrow_records_debt_amount_correctly(vault, usdc, owner):
    amount = 100 * 10**6
    vault.provide_liquidity(usdc, amount, BASE_LP)

    before = vault.total_debt_amount(usdc)

    borrow_amount = 5 * 10**6
    vault.internal._borrow(usdc, borrow_amount)

    after = vault.total_debt_amount(usdc)

    assert after == before + borrow_amount


def test_cannot_borrow_more_than_available_liqudity(vault, usdc):
    amount = 100 * 10**6
    vault.provide_liquidity(usdc, amount, BASE_LP)

    available_liquidity = vault.available_liquidity(usdc)

    with boa.reverts("not enough liquidity"):
        vault.internal._borrow(usdc, available_liquidity + 1)


def test_init_total_by_distributing_trading_fee_works(vault, usdc, owner):
    vault.set_trading_fee_lp_share(100_00)
    vault.set_safety_module_interest_share_percentage(60_00)

    vault.eval(f"self.base_lp_total_amount[{usdc.address}] = {0}")
    vault.eval(f"self.safety_module_lp_total_amount[{usdc.address}] = {0}")
    vault.eval(f"self.total_debt_amount[{usdc.address}] = {0}")
    vault.eval(f"self.base_lp_total_shares[{usdc.address}] = {0}")
    vault.eval(f"self.base_lp_shares[{usdc.address}][{owner}] = {0}")
    vault.eval(f"self.safety_module_lp_total_shares[{usdc.address}] = {0}")
    vault.eval(f"self.safety_module_lp_shares[{usdc.address}][{owner}] = {0}")

    assert vault.base_lp_total_amount(usdc) == 0
    assert vault.safety_module_lp_total_amount(usdc) == 0

    vault.internal._pay_interest_to_lps(usdc.address, 1 * 10**6)
    
    assert vault.base_lp_total_amount(usdc) == 400000
    assert vault.safety_module_lp_total_amount(usdc) == 600000

    before = vault.base_lp_shares(usdc, owner)

    amount = 100 * 10**6
    vault.provide_liquidity(usdc, amount, BASE_LP)

    after = vault.base_lp_shares(usdc, owner)

    assert after == before + amount * 10**18 - 1

    assert vault.lp_shares_to_amount(usdc, after, BASE_LP) == 100 * 10**6 + 400000 - 1
