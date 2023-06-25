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


def test_available_liquidity_is_calculated_correctly(vault, usdc):
    before = vault.available_liquidity(usdc)

    amount = 100 * 10**6
    vault.provide_liquidity(usdc, amount, BASE_LP)

    assert vault.available_liquidity(usdc) == before + amount

    borrow_amount = 30 * 10**6
    vault.internal._borrow(usdc, borrow_amount)

    assert vault.available_liquidity(usdc) == before + amount - borrow_amount

def test_cannot_withdraw_liquidity_outstanding_debt(vault, usdc):
    amount = 100 * 10**6
    vault.provide_liquidity(usdc, amount, BASE_LP)

    available_before = vault.available_liquidity(usdc)
    
    borrow_amount = 30 * 10**6
    vault.internal._borrow(usdc, borrow_amount)
    assert vault.available_liquidity(usdc) == available_before - borrow_amount

    with boa.reverts("liquidity not available"):
        vault.withdraw_liquidity(usdc, available_before, BASE_LP)

def test_can_set_withdraw_liquidity_cooldown(vault, usdc):
    assert vault.withdraw_liquidity_cooldown() != 30
    vault.set_withdraw_liquidity_cooldown(30)
    assert vault.withdraw_liquidity_cooldown() == 30


def test_provide_liquidity_records_cooldown_expiry_for_account(vault, usdc, owner):
    cooldown_duration = 30
    vault.set_withdraw_liquidity_cooldown(cooldown_duration)

    assert vault.account_withdraw_liquidity_cooldown(owner) < boa.env.vm.patch.timestamp + cooldown_duration
    vault.provide_liquidity(usdc, 100 * 10**6, BASE_LP)
    assert vault.account_withdraw_liquidity_cooldown(owner) == boa.env.vm.patch.timestamp + cooldown_duration


def test_cannot_withdraw_liquidity_before_cooldown_expires(vault, usdc):
    vault.set_withdraw_liquidity_cooldown(30)
    assert vault.withdraw_liquidity_cooldown() == 30

    amount = 100 * 10**6
    vault.provide_liquidity(usdc, amount, BASE_LP)

    with boa.reverts("cooldown"):
        vault.withdraw_liquidity(usdc, amount, BASE_LP)


def test_can_withdraw_liquidity_after_cooldown_expires(vault, usdc):
    vault.set_withdraw_liquidity_cooldown(30)
    assert vault.withdraw_liquidity_cooldown() == 30

    amount = 100 * 10**6
    vault.provide_liquidity(usdc, amount, BASE_LP)

    boa.env.time_travel(30)

    vault.withdraw_liquidity(usdc, amount, BASE_LP)