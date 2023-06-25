import pytest
import boa
from vyper.utils import checksum_encode


def pytest_configure():
    pytest.ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
    pytest.WETH = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
    pytest.USDC = "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"
    pytest.WBTC = "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f"
    # pytest.UNISWAP_ROUTER = "0xE592427A0AEce92De3Edee1F18E0157C05861564"
    pytest.UNISWAP_ROUTER = "0xE592427A0AEce92De3Edee1F18E0157C05861564"
    # pytest.ORACLE = "0xc351628EB244ec633d5f21fBD6621e1a683B1181"
    pytest.ETH_USD_ORACLE = "0x639fe6ab55c921f74e7fac1ee960c0b6293ba612"
    pytest.USDC_USD_ORACLE = "0x50834f3163758fcc1df9973b6e91f0f0f0434ad3"
    pytest.WBTC_USD_ORACLE = "0x6ce185860a4963106506c203335a2910413708e9"
    pytest.ARBITRUM_SEQUENCER_FEED = "0xFdB631F5EE196F0ed6FAa767959853A9F217697D"


# ----------
#  Accounts
# ----------
OWNER = boa.env.generate_address("owner")
boa.env.eoa = OWNER


@pytest.fixture(scope="session")
def owner():
    return OWNER


@pytest.fixture(scope="session")
def alice():
    return boa.env.generate_address("alice")


@pytest.fixture(scope="session")
def bob():
    return boa.env.generate_address("bob")


# -----------
#  Contracts
# -----------


@pytest.fixture(scope="session", autouse=True)
def spot_limit():
    dex = boa.load("contracts/spot-dex/LimitOrders.vy")
    dex.set_is_accepting_new_orders(True)
    return dex

@pytest.fixture(scope="session", autouse=True)
def spot_dca():
    dex = boa.load("contracts/spot-dex/Dca.vy")
    dex.set_is_accepting_new_orders(True)
    return dex

@pytest.fixture(scope="session", autouse=True)
def dex():
    dex = boa.load("contracts/margin-dex/MarginDex.vy")
    dex.set_is_accepting_new_orders(True)
    return dex


@pytest.fixture(scope="session", autouse=True)
def vault(eth_usd_oracle, usdc_usd_oracle, wbtc_usd_oracle):
    vault = boa.load("contracts/margin-dex/Vault.vy")
    vault.whitelist_token(pytest.WETH, pytest.ETH_USD_ORACLE)
    vault.whitelist_token(pytest.USDC, pytest.USDC_USD_ORACLE)
    vault.whitelist_token(pytest.WBTC, pytest.WBTC_USD_ORACLE)
    vault.enable_market(pytest.WETH, pytest.USDC, 50)
    vault.enable_market(pytest.USDC, pytest.WETH, 50)
    vault.set_variable_interest_parameters(pytest.WETH, 0, 0, 0, 80_00_000)
    vault.set_variable_interest_parameters(pytest.USDC, 0, 0, 0, 80_00_000)
    vault.set_is_accepting_new_orders(True)
    return vault

@pytest.fixture(scope="session")
def mock_vault():
    return boa.load("contracts/testing/MockVault.vy")


@pytest.fixture(scope="session", autouse=True)
def eth_usd_oracle():
    return boa.load(
        "contracts/testing/MockOracle.vy",
        1234_0000_0000,
        override_address=pytest.ETH_USD_ORACLE,
    )

@pytest.fixture(scope="session", autouse=True)
def usdc_usd_oracle():
    return boa.load(
        "contracts/testing/MockOracle.vy",
        1_0000_0000,
        override_address=pytest.USDC_USD_ORACLE,
    )

@pytest.fixture(scope="session", autouse=True)
def wbtc_usd_oracle():
    return boa.load(
        "contracts/testing/MockOracle.vy",
        30100_0000_0000,
        override_address=pytest.WBTC_USD_ORACLE,
    )

@pytest.fixture(scope="session", autouse=True)
def arbitrum_sequencer():
    return boa.load(
        "contracts/testing/MockOracle.vy",
        0,
        override_address=pytest.ARBITRUM_SEQUENCER_FEED,
    )


@pytest.fixture(scope="session", autouse=True)
def swap_router():
    swap_router = boa.load("contracts/margin-dex/SwapRouter.vy")
    swap_router.add_direct_route(pytest.USDC, pytest.WETH, 500)
    return swap_router

@pytest.fixture(scope="session", autouse=True)
def mock_router():
    return boa.load(
        "contracts/testing/MockSwapRouter.vy"
    )

@pytest.fixture(scope="session", autouse=True)
def mock_uniswap_router():
    return boa.load(
        "contracts/testing/MockUniswapRouter.vy",
        override_address=pytest.UNISWAP_ROUTER,
    )



@pytest.fixture(scope="session", autouse=True)
def usdc(alice, bob):
    usdc = boa.load(
        "contracts/testing/MockERC20.vy",
        "USDC",
        "USDC",
        6,
        100_000_000 * 10**6,
        override_address=pytest.USDC,
    )
    usdc.transfer(alice, 1000 * 10**6)
    usdc.transfer(bob, 1000 * 10**6)
    return usdc

@pytest.fixture(scope="session", autouse=True)
def weth(alice, bob):
    weth = boa.load(
        "contracts/testing/MockERC20.vy",
        "wrapped ETH",
        "WETH",
        18,
        1000000 * 10**18,
        override_address=pytest.WETH,
    )
    weth.transfer(alice, 10 * 10**18)
    weth.transfer(bob, 10 * 10**18)
    return weth

@pytest.fixture(scope="session", autouse=True)
def wbtc():
    return boa.load(
        "contracts/testing/MockERC20.vy",
        "wrapped ETH",
        "WETH",
        8,
        1000000 * 10**18,
        override_address=pytest.WBTC,
    )

# -----------
#    setup
# -----------
@pytest.fixture(scope="session", autouse=True)
def setup(swap_router, vault, dex):
    vault.set_is_whitelisted_dex(dex.address, True)
    vault.set_swap_router(swap_router)
    dex.set_vault(vault.address)
