import pytest 


@pytest.fixture(autouse=True)
def setup(vault, mock_router, owner, usdc, weth):
    vault.set_swap_router(mock_router.address)
    vault.set_is_whitelisted_dex(owner, True)
    usdc.approve(vault.address, 999999999999999999)
    vault.fund_account(usdc.address, 1000000000)
    vault.provide_liquidity(usdc, 1000000000000, False)


def test_effective_leverage(vault):
    # _calculate_leverage(_position_value: uint256, _debt_value: uint256, _margin_value: uint256)
    assert vault.internal._calculate_leverage(1000, 900) == 10

    assert vault.internal._calculate_leverage(1100, 900) == 5

    assert vault.internal._calculate_leverage(950, 900) == 19


def test_is_liquidatable(vault, weth, usdc, owner, eth_usd_oracle):
    assert vault.max_leverage(weth, usdc) == 50

    eth_usd_oracle.set_answer(1000_00000000)
    uid, _ = vault.open_position(
        owner,  # account
        weth,  # position_token
        1 * 10**18,  # min_position_amount_out
        usdc,  # debt_token
        900 * 10**6,  # debt_amount
        100 * 10**6,  # margin_amount
    )

    assert vault.effective_leverage(uid) == 10
    assert not vault.is_liquidatable(uid) 

    eth_usd_oracle.set_answer(950_00000000)
    assert vault.effective_leverage(uid) == 19
    assert not vault.is_liquidatable(uid) 

    vault.eval(f"self.max_leverage[{usdc.address}][{weth.address}] = 19")
    assert vault.effective_leverage(uid) == 19
    assert vault.max_leverage(usdc, weth) == 19
    assert not vault.is_liquidatable(uid) 

    vault.eval(f"self.max_leverage[{usdc.address}][{weth.address}] = 18")
    assert vault.max_leverage(usdc, weth) == 18
    assert vault.effective_leverage(uid) == 19
    assert vault.is_liquidatable(uid) 