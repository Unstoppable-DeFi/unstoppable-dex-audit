import pytest


def test_token_to_token_conversion(vault, weth, usdc, usdc_usd_oracle, wbtc):
    usdc_usd_oracle.set_answer(90000000)  # 0.9 usdc
    one_eth = 1 * 10**18

    eth_usd_oracle_price = vault.to_usd_oracle_price(weth.address)
    assert eth_usd_oracle_price == 1234_00000000
    usdc_usd_oracle_price = vault.to_usd_oracle_price(usdc.address)
    assert usdc_usd_oracle_price == 90000000

    weth_in_usdc = vault.internal._quote_token_to_token(weth, usdc, one_eth)
    assert weth_in_usdc == int(1234 * 10**6 / 0.9)

    wbtc_oracle_price = vault.to_usd_oracle_price(wbtc.address)
    assert wbtc_oracle_price == 3010000000000

    weth_in_wbtc = vault.internal._quote_token_to_token(weth, wbtc, one_eth)
    assert weth_in_wbtc == 4099667  # ~0.041
