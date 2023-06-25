import pytest


def test_market_order_slippage(vault, weth, usdc):

    vault.set_liquidate_slippage_for_market(weth, usdc, 500) # 5%
    assert vault.liquidate_slippage(weth, usdc) == 500

    assert vault.to_usd_oracle_price(weth.address) == 1234_00000000
    assert vault.internal._quote_token_to_token(weth, usdc, 1 * 10**18) == 1234_000000

    min_amount_out = vault.internal._market_order_min_amount_out(weth, usdc, 1 * 10**18)
    assert min_amount_out == 1234_000000 * 0.95


    vault.set_liquidate_slippage_for_market(weth, usdc, 1800) # 18%
    assert vault.liquidate_slippage(weth, usdc) == 1800

    assert vault.to_usd_oracle_price(weth.address) == 1234_00000000
    assert vault.internal._quote_token_to_token(weth, usdc, 2 * 10**18) == 2468_000000

    min_amount_out = vault.internal._market_order_min_amount_out(weth, usdc, 2 * 10**18)
    expected = 2468_000000 * 0.82
    assert min_amount_out == pytest.approx(expected)