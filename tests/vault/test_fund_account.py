import pytest


@pytest.fixture(autouse=True)
def setup(owner, vault, weth, usdc, mock_router):
    weth.approve(vault, 1000*10**18)
    usdc.approve(vault, 10000*10**6)
    vault.set_swap_router(mock_router.address)


def test_funding_account_increases_margin(vault, owner, weth, usdc):

    usdc_margin_before = vault.margin(owner, pytest.USDC)
    weth_margin_before = vault.margin(owner, pytest.WETH)

    usdc_amount = 100*10**6
    weth_amount = 1*10**18

    vault.fund_account(usdc, usdc_amount)
    vault.fund_account(weth, weth_amount)

    usdc_margin_after = vault.margin(owner, pytest.USDC)
    weth_margin_after = vault.margin(owner, pytest.WETH)
    
    assert usdc_margin_after == usdc_margin_before + usdc_amount
    assert weth_margin_after == weth_margin_before + weth_amount
    

def test_funding_account_transfers_token(vault, owner, weth):
    owner_balance_before = weth.balanceOf(owner)
    vault_balance_before = weth.balanceOf(vault)

    amount = 1 * 10**18

    vault.fund_account(pytest.WETH, amount)

    owner_balance_after = weth.balanceOf(owner)
    vault_balance_after = weth.balanceOf(vault)

    assert owner_balance_after == owner_balance_before - amount
    assert vault_balance_after == vault_balance_before + amount


def test_withdraw_decreases_margin(vault, owner, weth, usdc):
    usdc_amount = 100*10**6
    weth_amount = 1*10**18

    vault.fund_account(usdc, usdc_amount)
    vault.fund_account(weth, weth_amount)

    usdc_before = vault.margin(owner, pytest.USDC)
    weth_before = vault.margin(owner, pytest.WETH)

    vault.withdraw_from_account(usdc, int(usdc_amount/2))
    vault.withdraw_from_account(weth, int(weth_amount/2))

    assert vault.margin(owner, pytest.USDC) == usdc_before - int(usdc_amount/2)
    assert vault.margin(owner, pytest.WETH) == weth_before - int(weth_amount/2)


def test_swap_margin(vault, owner, weth, usdc):
    usdc_amount = 100*10**6
    weth_amount = 1*10**18

    vault.fund_account(usdc, usdc_amount)

    usdc_before = vault.margin(owner, pytest.USDC)
    weth_before = vault.margin(owner, pytest.WETH)

    vault.swap_margin(owner, usdc, weth, usdc_before, weth_amount)

    assert vault.margin(owner, pytest.USDC) == 0
    assert vault.margin(owner, pytest.WETH) == weth_before + weth_amount

