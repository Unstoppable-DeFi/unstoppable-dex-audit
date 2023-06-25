import pytest
import boa


MIN_INTEREST_RATE = 3_00_000
MID_INTEREST_RATE = 20_00_000
MAX_INTEREST_RATE = 100_00_000
RATE_SWITCH_UTILIZATION = 80_00_000
FOURTY_PERCENT = 40_00_000
NINETY_PERCENT = 90_00_000
ONE_HUNDRED_PERCENT = 100_00_000

WETH_ADDRESS = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
USDC_ADDRESS = "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"


@pytest.fixture
def vault_with_weth_interst_configured(vault):
    vault.set_variable_interest_parameters(
        WETH_ADDRESS,
        MIN_INTEREST_RATE,
        MID_INTEREST_RATE,
        MAX_INTEREST_RATE,
        RATE_SWITCH_UTILIZATION,
    )

    return vault


@pytest.fixture
def vault_with_weth_interest_configured2(vault):
    vault.set_variable_interest_parameters(
        WETH_ADDRESS,
        5_00_000,
        40_00_000,
        120_00_000,
        50_00_000,
    )

    return vault


@pytest.fixture
def vault_configured(vault):
    vault.set_variable_interest_parameters(
        USDC_ADDRESS,
        MIN_INTEREST_RATE,
        MID_INTEREST_RATE,
        MAX_INTEREST_RATE,
        RATE_SWITCH_UTILIZATION,
    )

    vault.set_variable_interest_parameters(
        WETH_ADDRESS,
        5_00_000,
        40_00_000,
        120_00_000,
        50_00_000,
    )

    return vault


def test_variable_interest_rate_setters_001(vault):
    # given we set the configuration manually
    vault.set_variable_interest_parameters(
        WETH_ADDRESS,
        MIN_INTEREST_RATE,
        MID_INTEREST_RATE,
        MAX_INTEREST_RATE,
        RATE_SWITCH_UTILIZATION,
    )

    # when we access the config
    # then the set values are returned
    assert vault.internal._min_interest_rate(WETH_ADDRESS) == MIN_INTEREST_RATE
    assert vault.internal._mid_interest_rate(WETH_ADDRESS) == MID_INTEREST_RATE
    assert vault.internal._max_interest_rate(WETH_ADDRESS) == MAX_INTEREST_RATE
    assert (
        vault.internal._rate_switch_utilization(WETH_ADDRESS) == RATE_SWITCH_UTILIZATION
    )


def test_variable_interest_rate_setters_002(vault):
    # given we set the config for token1 (USDC) and we do not set the config for token2 (WETH)
    vault.set_variable_interest_parameters(
        USDC_ADDRESS,
        2_00_000,
        19_00_000,
        99_00_000,
        79_00_000,
    )

    # when we access the config for token2 (WETH)
    # then the default-values are returned
    assert vault.internal._min_interest_rate(WETH_ADDRESS) == 3_00_000
    assert vault.internal._mid_interest_rate(WETH_ADDRESS) == 20_00_000
    assert vault.internal._max_interest_rate(WETH_ADDRESS) == 100_00_000
    assert vault.internal._rate_switch_utilization(WETH_ADDRESS) == 80_00_000

    # when we access the config for token1 (WETH)
    # then the set values are returned
    assert vault.internal._min_interest_rate(USDC_ADDRESS) == 2_00_000
    assert vault.internal._mid_interest_rate(USDC_ADDRESS) == 19_00_000
    assert vault.internal._max_interest_rate(USDC_ADDRESS) == 99_00_000
    assert vault.internal._rate_switch_utilization(USDC_ADDRESS) == 79_00_000

    # given we set the configuration manually
    vault.set_variable_interest_parameters(
        WETH_ADDRESS,
        4_00_000,
        21_00_000,
        101_00_000,
        81_00_000,
    )
    # when we access the config
    # then the set values are returned
    assert vault.internal._min_interest_rate(WETH_ADDRESS) == 4_00_000
    assert vault.internal._mid_interest_rate(WETH_ADDRESS) == 21_00_000
    assert vault.internal._max_interest_rate(WETH_ADDRESS) == 101_00_000
    assert vault.internal._rate_switch_utilization(WETH_ADDRESS) == 81_00_000


def test_low_dynamic_utilization_rate_001(vault_with_weth_interst_configured):
    i = vault_with_weth_interst_configured.internal._dynamic_interest_rate_low_utilization(
        WETH_ADDRESS, 0
    )
    assert i == MIN_INTEREST_RATE


def test_low_dynamic_utilization_rate_002(vault_with_weth_interst_configured):
    i = vault_with_weth_interst_configured.internal._dynamic_interest_rate_low_utilization(
        WETH_ADDRESS, FOURTY_PERCENT
    )
    assert i == 11_50_000


def test_low_dynamic_utilization_rate_003(vault_with_weth_interst_configured):
    i = vault_with_weth_interst_configured.internal._dynamic_interest_rate_low_utilization(
        WETH_ADDRESS, 70_00_000
    )
    assert i == 17_87_500


def test_low_dynamic_utilization_rate_004(vault_with_weth_interst_configured):
    i = vault_with_weth_interst_configured.internal._dynamic_interest_rate_low_utilization(
        WETH_ADDRESS, RATE_SWITCH_UTILIZATION
    )
    assert i == MID_INTEREST_RATE


def test_low_dynamic_utilization_rate_005(vault_with_weth_interest_configured2):
    i = vault_with_weth_interest_configured2.internal._dynamic_interest_rate_low_utilization(
        WETH_ADDRESS, 0
    )
    assert i == 5_00_000


def test_low_dynamic_utilization_rate_006(vault_with_weth_interest_configured2):
    i = vault_with_weth_interest_configured2.internal._dynamic_interest_rate_low_utilization(
        WETH_ADDRESS, 40_00_000
    )
    assert i == 33_00_000


def test_low_dynamic_utilization_rate_007(vault_with_weth_interest_configured2):
    i = vault_with_weth_interest_configured2.internal._dynamic_interest_rate_low_utilization(
        WETH_ADDRESS, 50_00_000
    )
    assert i == 40_00_000


def test_high_dynamic_utilization_rate_001(vault_with_weth_interst_configured):
    i = vault_with_weth_interst_configured.internal._dynamic_interest_rate_high_utilization(
        WETH_ADDRESS, RATE_SWITCH_UTILIZATION
    )
    assert i == MID_INTEREST_RATE


def test_high_dynamic_utilization_rate_002(vault_with_weth_interst_configured):
    i = vault_with_weth_interst_configured.internal._dynamic_interest_rate_high_utilization(
        WETH_ADDRESS, NINETY_PERCENT
    )
    assert i == 60_00_000


def test_high_dynamic_utilization_rate_003(vault_with_weth_interst_configured):
    i = vault_with_weth_interst_configured.internal._dynamic_interest_rate_high_utilization(
        WETH_ADDRESS, ONE_HUNDRED_PERCENT
    )
    assert i == MAX_INTEREST_RATE


def test_high_dynamic_utilization_rate_004(vault_with_weth_interest_configured2):
    i = vault_with_weth_interest_configured2.internal._dynamic_interest_rate_high_utilization(
        WETH_ADDRESS, 50_00_000
    )
    assert i == 40_00_000


def test_high_dynamic_utilization_rate_005(vault_with_weth_interest_configured2):
    i = vault_with_weth_interest_configured2.internal._dynamic_interest_rate_high_utilization(
        WETH_ADDRESS, 75_00_000
    )
    assert i == 80_00_000


def test_high_dynamic_utilization_rate_006(vault_with_weth_interest_configured2):
    i = vault_with_weth_interest_configured2.internal._dynamic_interest_rate_high_utilization(
        WETH_ADDRESS, ONE_HUNDRED_PERCENT
    )
    assert i == 120_00_000


def test_interest_rate_by_utilization_001(vault_with_weth_interst_configured):
    i = vault_with_weth_interst_configured.internal._interest_rate_by_utilization(
        WETH_ADDRESS, 0
    )
    assert i == MIN_INTEREST_RATE


def test_interest_rate_by_utilization_002(vault_with_weth_interst_configured):
    i = vault_with_weth_interst_configured.internal._interest_rate_by_utilization(
        WETH_ADDRESS, FOURTY_PERCENT
    )
    assert i == 11_50_000


def test_interest_rate_by_utilization_003(vault_with_weth_interst_configured):
    i = vault_with_weth_interst_configured.internal._interest_rate_by_utilization(
        WETH_ADDRESS, 70_00_000
    )
    assert i == 17_87_500


def test_interest_rate_by_utilization_004(vault_with_weth_interst_configured):
    i = vault_with_weth_interst_configured.internal._interest_rate_by_utilization(
        WETH_ADDRESS, RATE_SWITCH_UTILIZATION
    )
    assert i == MID_INTEREST_RATE


def test_interest_rate_by_utilization_005(vault_with_weth_interst_configured):
    i = vault_with_weth_interst_configured.internal._interest_rate_by_utilization(
        WETH_ADDRESS, NINETY_PERCENT
    )
    assert i == 60_00_000


def test_interest_rate_by_utilization_006(vault_with_weth_interst_configured):
    i = vault_with_weth_interst_configured.internal._interest_rate_by_utilization(
        WETH_ADDRESS, ONE_HUNDRED_PERCENT
    )
    assert i == MAX_INTEREST_RATE


def test_interest_rate_by_utilization_007(vault_configured):
    i1 = vault_configured.internal._interest_rate_by_utilization(
        USDC_ADDRESS, 60_00_000
    )
    assert i1 == 15_75_000

    i2 = vault_configured.internal._interest_rate_by_utilization(
        WETH_ADDRESS, 60_00_000
    )
    assert i2 == 56_00_000


def test_variable_interest_rate_based_on_utilization_001(vault_configured, weth, usdc):
    amount = 100 * 10**6
    # given we have a certain amount of liquidity
    vault_configured.eval(
        f"self.base_lp_total_amount[{usdc.address}] = {amount * 10**18}"
    )

    # and given we do not have any debt so far
    # the utilization_rate should be zero
    assert vault_configured.internal._utilization_rate(usdc.address) == 0

    # accordingly the current interest per second should be 3% so 3_00_000
    # per second that is (300000*10^18)/(365*24*60*60)
    expected_interest_per_second = 9512937595129375

    assert (
        expected_interest_per_second
        == vault_configured.internal._current_interest_per_second(usdc.address)
    )


def test_variable_interest_rate_based_on_utilization_002(vault_configured, weth, usdc):
    amount = 100 * 10**6
    # given we have a certain amount of liquidity
    vault_configured.eval(
        f"self.base_lp_total_amount[{usdc.address}] = {amount * 10**18}"
    )
    # and the same amount of deb
    vault_configured.eval(
        f"self.total_debt_amount[{usdc.address}] = { int(amount * 10**18 * 4/10)}"
    )

    # the utilization_rate should be 0.4 so 40_00_000
    assert vault_configured.internal._utilization_rate(usdc.address) == 40_00_000

    # accordingly the current interest per second should be 11.5% so 11_50_000
    # per second that is (1150000*10^18)/(365*24*60*60) =
    expected_interest_per_second = 36466260781329274

    assert (
        expected_interest_per_second
        == vault_configured.internal._current_interest_per_second(usdc.address)
    )


def test_variable_interest_rate_based_on_utilization_003(vault_configured, weth, usdc):
    amount = 100 * 10**6
    # given we have a certain amount of liquidity
    vault_configured.eval(
        f"self.base_lp_total_amount[{usdc.address}] = {amount * 10**18}"
    )
    # and the same amount of deb
    vault_configured.eval(f"self.total_debt_amount[{usdc.address}] = {amount * 10**18}")

    # the utilization_rate should be 1
    assert vault_configured.internal._utilization_rate(usdc.address) == 100_00_000

    # accordingly the current interest per second should be 100% so 100_00_000
    # per second that is (10000000*10^18)/(365*24*60*60) =
    expected_interest_per_second = 317097919837645865

    assert (
        expected_interest_per_second
        == vault_configured.internal._current_interest_per_second(usdc.address)
    )
