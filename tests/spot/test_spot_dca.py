import pytest
import boa

def test_dca_order_is_recorded(spot_dca, usdc, weth, owner):
    before = spot_dca.get_all_open_positions(owner)
    assert len(before) == 0

    # post_dca_order(
    #     _token_in: address,
    #     _token_out: address,
    #     _amount_in_per_execution: uint256,
    #     _seconds_between_executions: uint256,
    #     _max_number_of_executions: uint8,
    #     _max_slippage: uint256,
    #     _twap_length: uint32
    # ):
    amount_in = 10 * 10**6
    seconds_between = 60
    max_executions = 10
    max_slippage = 50
    twap_length = 300

    usdc.approve(spot_dca, amount_in * max_executions)

    spot_dca.post_dca_order(usdc, weth, amount_in, seconds_between, max_executions, max_slippage, twap_length)

    after = spot_dca.get_all_open_positions(owner)
    assert len(after) == 1

    order = after[0]

    # DCA Orders
    # struct DcaOrder:
    #     uid: bytes32
    #     account: address
    #     token_in: address
    #     token_out: address
    #     amount_in_per_execution: uint256
    #     seconds_between_executions: uint256
    #     max_number_of_executions: uint8
    #     max_slippage: uint256
    #     twap_length: uint32
    #     number_of_executions: uint8
    #     last_execution: uint256
    assert order[1] == owner
    assert order[2] == usdc.address
    assert order[3] == weth.address
    assert order[4] == amount_in
    assert order[5] == seconds_between
    assert order[6] == max_executions
    assert order[7] == max_slippage
    assert order[8] == twap_length
    assert order[9] == 0
    assert order[10] == 0


def test_execute_reverts_with_invalid_path(spot_dca, owner, weth, usdc):
    amount_in = 10 * 10**6
    seconds_between = 60
    max_executions = 10
    max_slippage = 50
    twap_length = 300

    usdc.approve(spot_dca, amount_in * max_executions)

    spot_dca.post_dca_order(usdc, weth, amount_in, seconds_between, max_executions, max_slippage, twap_length)

    order = spot_dca.get_all_open_positions(owner)[0]

    with boa.reverts():
        spot_dca.execute_dca_order(order[0], [weth.address, usdc.address], [500], False)

    with boa.reverts():
        spot_dca.execute_dca_order(order[0], [usdc.address, usdc.address], [500], False)


def test_post_limit_reverts_with_insufficient_allowance(spot_dca, owner, weth, usdc):
    amount_in = 10 * 10**6
    seconds_between = 60
    max_executions = 10
    max_slippage = 50
    twap_length = 300

    assert usdc.allowance(owner, spot_dca) < amount_in

    with boa.reverts("insufficient allowance"):
        spot_dca.post_dca_order(usdc, weth, amount_in, seconds_between, max_executions, max_slippage, twap_length)

    

def test_can_cancel_order(spot_dca, owner, weth, usdc):
    amount_in = 10 * 10**6
    seconds_between = 60
    max_executions = 10
    max_slippage = 50
    twap_length = 300

    usdc.approve(spot_dca, amount_in * max_executions)

    spot_dca.post_dca_order(usdc, weth, amount_in, seconds_between, max_executions, max_slippage, twap_length)

    before = spot_dca.get_all_open_positions(owner)
    assert len(before) == 1

    order = before[0]

    spot_dca.cancel_dca_order(order[0])

    after = spot_dca.get_all_open_positions(owner)
    assert len(after) == 0

def test_NON_owner_CANNOT_cancel_order(spot_dca, owner, weth, usdc, alice):
    amount_in = 10 * 10**6
    seconds_between = 60
    max_executions = 10
    max_slippage = 50
    twap_length = 300

    usdc.approve(spot_dca, amount_in * max_executions)

    spot_dca.post_dca_order(usdc, weth, amount_in, seconds_between, max_executions, max_slippage, twap_length)

    before = spot_dca.get_all_open_positions(owner)
    assert len(before) == 1

    order = before[0]

    with boa.env.prank(alice):
        with boa.reverts("unauthorized"):
            spot_dca.cancel_dca_order(order[0])