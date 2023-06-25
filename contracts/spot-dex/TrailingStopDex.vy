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

    def getRoundData(_round_id: uint80) -> (
        uint80,  # roundId
        int256,  # answer
        uint256, # startedAt
        uint256, # updatedAt
        uint80   # answeredInRound
    ): view

# struct ExactInputSingleParams {
#         address tokenIn;
#         address tokenOut;
#         uint24 fee;
#         address recipient;
#         uint256 deadline;
#         uint256 amountIn;
#         uint256 amountOutMinimum;
#         uint160 sqrtPriceLimitX96;
#     }
struct ExactInputSingleParams:
    tokenIn: address
    tokenOut: address
    fee: uint24
    recipient: address
    deadline: uint256
    amountIn: uint256
    amountOutMinimum: uint256
    sqrtPriceLimitX96: uint160

# function exactInputSingle(ExactInputSingleParams calldata params) external payable returns (uint256 amountOut);
interface UniswapV3SwapRouter:
    def exactInputSingle(_params: ExactInputSingleParams) -> uint256: payable


UNISWAP_ROUTER: constant(address) = 0xE592427A0AEce92De3Edee1F18E0157C05861564

# token_addr -> oracle_addr
oracle_addresses: public(HashMap[address, address])

owner: public(address)

# Trailing Stop Limit Orders
struct TrailingStopLimitOrder:
    uid: bytes32
    account: address
    token_in: address
    token_out: address
    amount_in: uint256
    min_amount_out: uint256
    trailing_percentage: uint256
    created_at: uint256
    valid_until: uint256
    executed: bool

# user address -> position UID
position_uids: public(HashMap[address, DynArray[bytes32, 1024]])
# UID -> position
positions: public(HashMap[bytes32, TrailingStopLimitOrder])
CANCELED_TIMESTAMP: constant(uint256) = 111


@external
def __init__():
    self.owner = msg.sender


event TrailingStopLimitOrderPosted:
    uid: bytes32
    token_in: indexed(address)
    token_out: indexed(address)
    trailing_percentage: uint256
    valid_until: uint256
    

@external
def post_trailing_stop_limit_order(
        _token_in: address,
        _token_out: address,
        _amount_in: uint256,
        _min_amount_out: uint256,
        _trailing_percentage: uint256,
        _valid_until: uint256
    ):
    #TODO validate
    #TODO check approval
    
    order: TrailingStopLimitOrder = TrailingStopLimitOrder({
        uid: empty(bytes32),
        account: msg.sender,
        token_in: _token_in,
        token_out: _token_out,
        amount_in: _amount_in,
        min_amount_out: _min_amount_out,
        trailing_percentage: _trailing_percentage,
        created_at: block.timestamp,
        valid_until: _valid_until,
        executed: False
    })

    uid: bytes32 = self._uid(order)
    order.uid = uid

    self.positions[uid] = order
    self.position_uids[msg.sender].append(uid)

    log TrailingStopLimitOrderPosted(uid, _token_in, _token_out, _trailing_percentage, _valid_until)



event TrailingStopLimitOrderExecuted:
    uid: bytes32

event TrailingStopLimitOrderFailed:
    uid: bytes32
    account: indexed(address)
    reason: String[32]

@external
def execute_trailing_stop_limit_order(_uid: bytes32, _proof_round_id: uint80 ,_uni_pool_fee: uint24):
    order: TrailingStopLimitOrder = self.positions[_uid]

    assert order.valid_until > block.timestamp, "order expired"
    assert order.executed == False, "order already executed"

    account_balance: uint256 = ERC20(order.token_in).balanceOf(order.account)
    if account_balance < order.amount_in:
        log TrailingStopLimitOrderFailed(_uid, order.account, "insufficient balance")
        self._cancel_limit_order(_uid)
        return

    account_allowance: uint256 = ERC20(order.token_in).allowance(order.account, self)
    if account_allowance < order.amount_in:
        log TrailingStopLimitOrderFailed(_uid, order.account, "insufficient allowance")
        self._cancel_limit_order(_uid)
        return

    order.executed = True
    self.positions[_uid] = order

    oracle_address: address = self.oracle_addresses[order.token_in]

    # get price at _proof_round_id
    proof_round_price: uint256 = 0
    proof_round_price_updated_at: uint256 = 0

    (proof_round_price, proof_round_price_updated_at) = self._get_price_at_round(oracle_address, _proof_round_id)

    # ensure proof_round was after order created
    assert proof_round_price_updated_at > order.created_at, "invalid proof: too old"

    # check current price
    current_price: uint256 = self._get_latest_oracle_price(oracle_address)

    # ensure current price < proof_round_price - trailing_percentage
    trigger_price: uint256 = proof_round_price * (100 - order.trailing_percentage) / 100 # TODO check
    assert current_price < trigger_price, "trigger price not reached"

    # transfer token_in from user to self
    ERC20(order.token_in).transferFrom(order.account, self, order.amount_in)

    # approve UNISWAP_ROUTER to spend token_in
    ERC20(order.token_in).approve(UNISWAP_ROUTER, order.amount_in)

    uni_params: ExactInputSingleParams = ExactInputSingleParams({
        tokenIn: order.token_in,
        tokenOut: order.token_out,
        fee: _uni_pool_fee,
        recipient: self,
        deadline: order.valid_until,
        amountIn: order.amount_in,
        amountOutMinimum: order.min_amount_out,
        sqrtPriceLimitX96: 0
    })

    UniswapV3SwapRouter(UNISWAP_ROUTER).exactInputSingle(uni_params)

    ERC20(order.token_out).transfer(order.account, order.min_amount_out) # anything > min_amount_out stays in contract as profit

    # TODO swap profits into what?
    # TODO share profit between msg.sender and self?

    log TrailingStopLimitOrderExecuted(_uid)


event TrailingStopLimitOrderCanceled:
    uid: bytes32

@external
def cancel_trailing_stop_limit_order(_uid: bytes32):
    order: TrailingStopLimitOrder = self.positions[_uid]
    assert order.account == msg.sender, "unauthorized"
    self._cancel_limit_order(_uid)

@internal
def _cancel_limit_order(_uid: bytes32):
    order: TrailingStopLimitOrder = self.positions[_uid]
    self.positions[_uid] = empty(TrailingStopLimitOrder)

    log TrailingStopLimitOrderCanceled(_uid)



@external
def withdraw_fees(_token: address):
    amount: uint256 = ERC20(_token).balanceOf(self)
    assert amount > 0, "zero balance"

    ERC20(_token).transfer(self.owner, amount)


@external
@view
def uid(_order: TrailingStopLimitOrder) -> bytes32:
    return self._uid(_order)

@internal
@view
def _uid(_order: TrailingStopLimitOrder) -> bytes32:
    # TODO better uid
    position_uid: bytes32 = keccak256(_abi_encode(_order.account, _order.token_in, _order.token_out, block.timestamp))
    return position_uid


@internal
def _get_latest_oracle_price(_oracle_address: address) -> uint256:
    answer: int256 = ChainlinkOracle(_oracle_address).latestRoundData()[1]
    price: uint256 = convert(answer, uint256) # 6 dec
    return price

@internal
def _get_price_at_round(_oracle_address: address, _round_id: uint80) -> (uint256, uint256):
    answer: int256 = ChainlinkOracle(_oracle_address).getRoundData(_round_id)[1]
    updated_at: uint256 = ChainlinkOracle(_oracle_address).getRoundData(_round_id)[3]
    price: uint256 = convert(answer, uint256) # 6 dec
    return (price, updated_at)