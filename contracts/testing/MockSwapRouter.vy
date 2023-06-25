# @version ^0.3.7

from vyper.interfaces import ERC20

interface Mintable:
    def mint(_to: address, _value: uint256): nonpayable

interface SwapRouter:
    def swap(
        _token_in: address,
        _token_out: address,
        _amount_in: uint256,
        _min_amount_out: uint256
        ) -> uint256: nonpayable

implements: SwapRouter


swap_token_in: public(address)
swap_token_out: public(address)
swap_amount_in: public(uint256)
swap_min_amount_out: public(uint256)

@external
def swap(_token_in: address, _token_out: address, _amount_in: uint256, _min_amount_out: uint256) -> uint256:
    self.swap_token_in = _token_in
    self.swap_token_out = _token_out
    self.swap_amount_in = _amount_in
    self.swap_min_amount_out = _min_amount_out

    ERC20(_token_in).transferFrom(msg.sender, self, _amount_in)
    Mintable(_token_out).mint(msg.sender, _min_amount_out)

    return _min_amount_out
