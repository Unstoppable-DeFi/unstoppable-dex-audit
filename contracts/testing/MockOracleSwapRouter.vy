# @version ^0.3.7

from vyper.interfaces import ERC20

interface ChainlinkOracle:
    def latestRoundData() -> (
      uint80,  # roundId,
      int256,  # answer,
      uint256, # startedAt,
      uint256, # updatedAt,
      uint80   # answeredInRound
    ): view

interface Mintable:
    def mint(_to: address, _value: uint256): nonpayable


struct ExactInputSingleParams:
    tokenIn: address
    tokenOut: address
    fee: uint24
    recipient: address
    deadline: uint256
    amountIn: uint256
    amountOutMinimum: uint256
    sqrtPriceLimitX96: uint160

interface UniswapV3SwapRouter:
    def exactInputSingle(_params: ExactInputSingleParams) -> uint256: payable


implements: UniswapV3SwapRouter


USDC: public(address)
WETH: public(address)
ETH_USD_ORACLE: public(address)
owner: public(address)

@external
def __init__(_oracle: address, _usdc: address, _weth: address):
    self.owner = msg.sender
    self.ETH_USD_ORACLE = _oracle
    self.USDC = _usdc
    self.WETH = _weth

@payable
@external
def exactInputSingle(_params: ExactInputSingleParams) -> uint256:
    eth_usd_price: uint256 = self._eth_usd_oracle_price()

    amount_out: uint256 = 0
    if _params.tokenIn == self.USDC:
        amount_out = _params.amountIn * 10**20 /  eth_usd_price # 6 + 20 - 8 = 18 decimals

    elif _params.tokenIn == self.WETH:
        amount_out = _params.amountIn * eth_usd_price / 10**20 # 18 + 8 - 20 = 6 decimals

    else:
        raise "invalid token"

    ERC20(_params.tokenIn).transferFrom(msg.sender, self, _params.amountIn)

    # mint token out to self first to have sufficient liquidity
    Mintable(_params.tokenOut).mint(self, amount_out)

    ERC20(_params.tokenOut).transfer(msg.sender, amount_out)

    return amount_out    



@view
@external
def eth_usd_oracle_price() -> uint256:
    return self._eth_usd_oracle_price()

@view
@internal
def _eth_usd_oracle_price() -> uint256:
    answer: int256 = ChainlinkOracle(self.ETH_USD_ORACLE).latestRoundData()[1]
    eth_usd_price: uint256 = convert(answer, uint256) # 8 dec
    return eth_usd_price



@external
def set_oracle(_new_addr: address):
    assert msg.sender == self.owner, "unauthorized"
    self.ETH_USD_ORACLE = _new_addr

@external
def set_usdc(_new_addr: address):
    assert msg.sender == self.owner, "unauthorized"
    self.USDC = _new_addr

@external
def set_weth(_new_addr: address):
    assert msg.sender == self.owner, "unauthorized"
    self.WETH = _new_addr