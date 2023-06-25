# @version ^0.3.7

from vyper.interfaces import ERC20

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

# struct ExactInputParams {
#     bytes path;
#     address recipient;
#     uint256 deadline;
#     uint256 amountIn;
#     uint256 amountOutMinimum;
# }
struct ExactInputParams:
    path: Bytes[160]
    recipient: address
    deadline: uint256
    amountIn: uint256
    amountOutMinimum: uint256


# function exactInputSingle(ExactInputSingleParams calldata params) external payable returns (uint256 amountOut);
interface UniswapV3SwapRouter:
    def exactInputSingle(_params: ExactInputSingleParams) -> uint256: payable
    def exactInput(_params: ExactInputParams) -> uint256: payable


UNISWAP_ROUTER: constant(address) = 0xE592427A0AEce92De3Edee1F18E0157C05861564


@external
def swap(_path: DynArray[address, 3], _uni_pool_fees: DynArray[uint24, 2], _amount_in: uint256):
    # transfer token_in from user to self
    ERC20(_path[0]).transferFrom(msg.sender, self, _amount_in)

    # approve UNISWAP_ROUTER to spend amount token_in
    ERC20(_path[0]).approve(UNISWAP_ROUTER, _amount_in)

    path: Bytes[66] = empty(Bytes[66])
    if(len(_path) == 2):
        path = concat(convert(_path[0], bytes20), convert(_uni_pool_fees[0], bytes3), convert(_path[1], bytes20))
    elif(len(_path) == 3):
        path = concat(convert(_path[0], bytes20), convert(_uni_pool_fees[0], bytes3), convert(_path[1], bytes20), convert(_uni_pool_fees[1], bytes3), convert(_path[2], bytes20))

    

    uni_params: ExactInputParams = ExactInputParams({
        path: path,
        recipient: self,
        deadline: block.timestamp,
        amountIn: _amount_in,
        amountOutMinimum: 0
    })
    amount_out: uint256 = UniswapV3SwapRouter(UNISWAP_ROUTER).exactInput(uni_params)
    
    ERC20(_path[len(_path)-1]).transfer(msg.sender, amount_out)


@external
@view
def encode(_path: DynArray[address, 3], _uni_pool_fees: DynArray[uint24, 2]) -> Bytes[66]:
    # path: Bytes[160] = concat(convert(_path[0], bytes20), convert(_uni_pool_fees[0], bytes3), convert(_path[1], bytes20))
    # path: DynArray[bytes, 66] = concat(convert(_path[0], bytes20), convert(_uni_pool_fees[0], bytes3), convert(_path[1], bytes20), convert(_uni_pool_fees[1], bytes3), convert(_path[2], bytes20))

    path: Bytes[66] = empty(Bytes[66])
    if(len(_path) == 2):
        path = concat(convert(_path[0], bytes20), convert(_uni_pool_fees[0], bytes3), convert(_path[1], bytes20))
    elif(len(_path) == 3):
        path = concat(convert(_path[0], bytes20), convert(_uni_pool_fees[0], bytes3), convert(_path[1], bytes20), convert(_uni_pool_fees[1], bytes3), convert(_path[2], bytes20))

    return path


@external
@view
def foo() -> Bytes[160]:
    a: address = 0x82aF49447D8a07e3bd95BD0d56f35241523fBab1
    b: address = 0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8
    f: uint24 = 500
    
    return _abi_encode(a, f, b)

@external
@view
def bar() -> Bytes[160]:
    a: address = 0x82aF49447D8a07e3bd95BD0d56f35241523fBab1
    b: address = 0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8
    f: uint24 = 500
    
    return concat(convert(a, bytes20), convert(f, bytes3), convert(b, bytes20))