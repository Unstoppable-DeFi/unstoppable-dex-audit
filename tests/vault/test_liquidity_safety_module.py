import pytest
import boa

BASE_LP = False
SAFETY_MODULE = True

@pytest.fixture(scope="session")
def setup(owner, vault, weth, usdc, alice):
    weth.approve(vault, 1000*10**18)
    usdc.approve(vault, 1000000*10**6)
    with boa.env.prank(alice):
        usdc.approve(vault, 1000000*10**6)



def test_provide_liquidity_liqudity_records_total_amount(vault, usdc, owner):
    before = vault.safety_module_lp_total_amount(usdc)

    amount = 100 * 10**6
    vault.provide_liquidity(usdc, amount, SAFETY_MODULE)

    after = vault.safety_module_lp_total_amount(usdc)

    assert after == before + amount
    
def test_first_provide_liquidity_records_user_shares(vault, usdc, owner):
    before = vault.safety_module_lp_shares(usdc, owner)
    assert before == 0

    amount = 100 * 10**6
    vault.provide_liquidity(usdc, amount, SAFETY_MODULE)

    after = vault.safety_module_lp_shares(usdc, owner)

    assert after == amount * 10**18

def test_first_provide_liquidity_records_total_shares(vault, usdc, owner):
    before = vault.safety_module_lp_total_shares(usdc)
    assert before == 0

    amount = 100 * 10**6
    vault.provide_liquidity(usdc, amount, SAFETY_MODULE)

    after = vault.safety_module_lp_total_shares(usdc)

    assert after == amount * 10**18

def test_multiple_provide_record_shares_correctly(vault, usdc, owner, alice):
    before = vault.safety_module_lp_total_shares(usdc)
    assert before == 0

    amount = 100 * 10**6
    vault.provide_liquidity(usdc, amount, SAFETY_MODULE)
    assert vault.safety_module_lp_total_shares(usdc) == amount * 10**18
    assert vault.safety_module_lp_shares(usdc, owner) == amount * 10**18

    with boa.env.prank(alice):
        amount_2 = 30 * 10**6
        vault.provide_liquidity(usdc, amount_2, SAFETY_MODULE)

    assert vault.safety_module_lp_total_shares(usdc) == (amount + amount_2) * 10**18
    assert vault.safety_module_lp_shares(usdc, owner) == amount * 10**18
    assert vault.safety_module_lp_shares(usdc, alice) == amount_2 * 10**18


def test_shares_to_amount_are_calculated_correctly(vault, usdc):
    amount = 100 * 10**6

    # first shares
    assert vault.safety_module_lp_total_shares(usdc) == 0
    assert vault.internal._amount_to_lp_shares(usdc, amount, SAFETY_MODULE) == amount * 10**18

    # second shares, no profits yet
    vault.eval(f"self.safety_module_lp_total_shares[{usdc.address}] = {amount * 10**18}")
    vault.eval(f"self.safety_module_lp_total_amount[{usdc.address}] = {amount}")
    assert vault.internal._amount_to_lp_shares(usdc, amount, SAFETY_MODULE) == amount * 10**18

    # second shares, previous profit
    vault.eval(f"self.safety_module_lp_total_shares[{usdc.address}] = {amount * 10**18}")
    vault.eval(f"self.safety_module_lp_total_amount[{usdc.address}] = {2*amount}")
    assert vault.internal._amount_to_lp_shares(usdc, amount, SAFETY_MODULE) == int(amount/2) * 10**18
    
    # second shares, previous loss
    vault.eval(f"self.safety_module_lp_total_shares[{usdc.address}] = {amount * 10**18}")
    vault.eval(f"self.safety_module_lp_total_amount[{usdc.address}] = {int(amount/2)}")
    assert vault.internal._amount_to_lp_shares(usdc, amount, SAFETY_MODULE) == amount*2 * 10**18


def test_amount_to_shares_are_calculated_correctly(vault, usdc):
    assert vault.internal._lp_shares_to_amount(usdc, 0, SAFETY_MODULE) == 0

    vault.eval(f"self.safety_module_lp_total_shares[{usdc.address}] = {1}")
    vault.eval(f"self.safety_module_lp_total_amount[{usdc.address}] = {1}")
    assert vault.internal._lp_shares_to_amount(usdc, 1, SAFETY_MODULE) == 1

    vault.eval(f"self.safety_module_lp_total_shares[{usdc.address}] = {1}")
    vault.eval(f"self.safety_module_lp_total_amount[{usdc.address}] = {2}")
    assert vault.internal._lp_shares_to_amount(usdc, 1, SAFETY_MODULE) == 2
    assert vault.internal._lp_shares_to_amount(usdc, 2, SAFETY_MODULE) == 4

def test_amount_to_shares_to_amount_is_calculated_correctly(vault, usdc):
    vault.provide_liquidity(usdc, 9876543210, SAFETY_MODULE)

    amount = 123456789
    shares = vault.internal._amount_to_lp_shares(usdc, amount, SAFETY_MODULE)

    assert vault.internal._lp_shares_to_amount(usdc, shares, SAFETY_MODULE) == amount


def test_withdraw_liquidity_reduces_total_shares(vault, usdc, owner):
    vault.provide_liquidity(usdc.address, 100 * 10**6, SAFETY_MODULE)
    before = vault.safety_module_lp_total_shares(usdc)

    withdraw_amount = 50 * 10**6
    withdraw_shares = vault.internal._amount_to_lp_shares(usdc, withdraw_amount, SAFETY_MODULE)
    vault.withdraw_liquidity(usdc, withdraw_amount, SAFETY_MODULE)

    after = vault.safety_module_lp_total_shares(usdc)

    assert after == before - withdraw_shares


def test_withdraw_liquidity_reduces_user_shares(vault, usdc, owner):
    vault.provide_liquidity(usdc.address, 100 * 10**6, SAFETY_MODULE)
    before = vault.safety_module_lp_shares(usdc, owner)

    withdraw_amount = 50 * 10**6
    withdraw_shares = vault.internal._amount_to_lp_shares(usdc, withdraw_amount, SAFETY_MODULE)
    vault.withdraw_liquidity(usdc, withdraw_amount, SAFETY_MODULE)

    after = vault.safety_module_lp_shares(usdc, owner)

    assert after == before - withdraw_shares


def test_withdraw_liquidity_reduces_total_amount(vault, usdc, owner):
    vault.provide_liquidity(usdc, 100 * 10**6, SAFETY_MODULE)
    before = vault.safety_module_lp_total_amount(usdc)

    withdraw_amount = 50 * 10**6
    vault.withdraw_liquidity(usdc, withdraw_amount, SAFETY_MODULE)

    after = vault.safety_module_lp_total_amount(usdc)

    assert after == before - withdraw_amount


def test_cannot_withdraw_more_than_you_own(vault, usdc, owner, alice):
    amount = 100 * 10**6
    vault.provide_liquidity(usdc, amount, SAFETY_MODULE)

    with boa.env.prank(alice):
        vault.provide_liquidity(usdc, amount, SAFETY_MODULE)
    
    assert vault.safety_module_lp_total_amount(usdc) == 2 * amount 
    assert vault.safety_module_lp_total_shares(usdc) == 2 * amount * 10**18

    with boa.reverts("cannot withdraw more than you own"):
        vault.withdraw_liquidity(usdc, amount+1, SAFETY_MODULE)


def test_provide_liquidity_transfers_tokens(vault, usdc, owner):
    amount = 100 * 10**6
    owner_balance_before = usdc.balanceOf(owner)
    assert owner_balance_before >= amount

    vault_balance_before = usdc.balanceOf(vault)

    vault.provide_liquidity(usdc, amount, SAFETY_MODULE)

    owner_balance_after = usdc.balanceOf(owner)
    vault_balance_after = usdc.balanceOf(vault)

    assert owner_balance_after == owner_balance_before - amount
    assert vault_balance_after == vault_balance_before + amount

def test_withdraw_liquidity_transfers_tokens(vault, usdc, owner):
    amount = 100 * 10**6
    vault.provide_liquidity(usdc, amount, SAFETY_MODULE)

    owner_balance_before = usdc.balanceOf(owner)
    vault_balance_before = usdc.balanceOf(vault)
    assert vault_balance_before >= amount

    vault.withdraw_liquidity(usdc, amount, SAFETY_MODULE)

    owner_balance_after = usdc.balanceOf(owner)
    vault_balance_after = usdc.balanceOf(vault)

    assert vault_balance_after == vault_balance_before - amount
    assert owner_balance_after == owner_balance_before + amount


def test_available_liquidty_is_calculated_correctly(vault, usdc):
    amount = 100 * 10**6
    vault.eval(f"self.base_lp_total_shares[{usdc.address}] = {0}")
    vault.eval(f"self.base_lp_total_amount[{usdc.address}] = {0}")
    vault.eval(f"self.safety_module_lp_total_shares[{usdc.address}] = {amount}")
    vault.eval(f"self.safety_module_lp_total_amount[{usdc.address}] = {amount}")
    vault.eval(f"self.total_debt_amount[{usdc.address}] = {int(amount/2)}")

    assert vault.available_liquidity(usdc) == int(amount/2)


def test_borrow_records_debt_amount_correctly(vault, usdc, owner):
    amount = 100 * 10**6
    vault.provide_liquidity(usdc, amount, SAFETY_MODULE)

    before = vault.total_debt_amount(usdc)

    borrow_amount = 5 * 10**6
    vault.internal._borrow(usdc, borrow_amount)

    after = vault.total_debt_amount(usdc)
    
    assert after == before + borrow_amount


def test_cannot_borrow_more_than_available_liqudity(vault, usdc):
    amount = 100 * 10**6
    vault.provide_liquidity(usdc, amount, SAFETY_MODULE)

    available_liquidity = vault.available_liquidity(usdc)

    with boa.reverts("not enough liquidity"):
        vault.internal._borrow(usdc, available_liquidity+1)
