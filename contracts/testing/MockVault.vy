# @version ^0.3.7

interface Vault:
    def open_position(
        _account: address, 
        _position_token: address,
        _min_position_amount_out: uint256,
        _debt_token: address, 
        _debt_amount: uint256,
        _margin_amount: uint256
    ) -> (bytes32, uint256): nonpayable
    def close_position(_position_uid: bytes32, _min_amount_out: uint256) -> uint256: nonpayable
    def reduce_position(_position_uid: bytes32, _reduce_by_amount: uint256, _min_amount_out: uint256) -> uint256: nonpayable
    def liquidate(_position_uid: bytes32): nonpayable
    def is_enabled_market(_token1: address, _token2: address) -> bool: view
    def debt(_position_uid: bytes32) -> uint256: view
    def position_amount(_position_uid: bytes32) -> uint256: view
    def add_margin(_position_uid: bytes32, _amount: uint256): nonpayable
    def remove_margin(_position_uid: bytes32, _amount: uint256): nonpayable
    def effective_leverage(_position_uid: bytes32) -> uint256: view
    def current_exchange_rate(_position_uid: bytes32) -> uint256: view
    def is_liquidatable(_position_uid: bytes32) -> bool: view
    def swap_margin(_account: address, _token_in: address, _token_out: address, _amount_in: uint256, _min_amount_out: uint256) -> uint256: nonpayable

# implements Vault

uid_nonce: uint256


op_account: public(address)
op_position_token: public(address)
op_min_position_amount_out: public(uint256)
op_debt_token: public(address)
op_debt_amount: public(uint256)
op_margin_amount: public(uint256)
op_uid: public(bytes32)

@external
def open_position(
        _account: address, 
        _position_token: address,
        _min_position_amount_out: uint256,
        _debt_token: address, 
        _debt_amount: uint256,
        _margin_amount: uint256
    ) -> (bytes32, uint256):

    self.op_account = _account
    self.op_position_token = _position_token
    self.op_min_position_amount_out = _min_position_amount_out
    self.op_debt_token = _debt_token
    self.op_debt_amount = _debt_amount
    self.op_margin_amount = _margin_amount
    self.op_uid = self._generate_uid()

    return self.op_uid, _min_position_amount_out


@external
@view
def is_enabled_market(_token1: address, _token2: address) -> bool:
    return True

@internal
def _generate_uid() -> bytes32:
    uid: bytes32 = keccak256(_abi_encode(chain.id, self.uid_nonce, block.timestamp))
    self.uid_nonce += 1
    return uid

