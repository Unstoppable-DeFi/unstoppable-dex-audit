# @version ^0.3.7

from vyper.interfaces import ERC20

interface Mintable:
    def mint(_to: address, _value: uint256): nonpayable

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
    path: Bytes[66]
    recipient: address
    deadline: uint256
    amountIn: uint256
    amountOutMinimum: uint256


# function exactInputSingle(ExactInputSingleParams calldata params) external payable returns (uint256 amountOut);
interface UniswapV3SwapRouter:
    def exactInputSingle(_params: ExactInputSingleParams) -> uint256: payable
    def exactInput(_params: ExactInputParams) -> uint256: payable

implements: UniswapV3SwapRouter


swap_was_called: public(bool)

@payable
@external
def exactInputSingle(_params: ExactInputSingleParams) -> uint256:
    self.swap_was_called = True

    ERC20(_params.tokenIn).transferFrom(msg.sender, self, _params.amountIn)

    # mint token out to self first to have sufficient liquidity
    Mintable(_params.tokenOut).mint(self, _params.amountOutMinimum)

    ERC20(_params.tokenOut).transfer(msg.sender, _params.amountOutMinimum)

    return _params.amountOutMinimum    

@payable
@external
def exactInput(_params: ExactInputParams) -> uint256:
    self.swap_was_called = True

    token_in: address = convert(slice(_params.path, 0, 20), address)
    token_out: address = convert(slice(_params.path, len(_params.path)-20, 20), address)
    
    ERC20(token_in).transferFrom(msg.sender, self, _params.amountIn)

    # mint token out to self first to have sufficient liquidity
    Mintable(token_out).mint(self, _params.amountOutMinimum)

    ERC20(token_out).transfer(msg.sender, _params.amountOutMinimum)

    return _params.amountOutMinimum    