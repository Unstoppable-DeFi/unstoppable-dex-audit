import pytest
import boa

def test_limit_order_is_recorded(spot_limit, usdc, weth, owner):
    before = spot_limit.get_all_open_positions(owner)
    assert len(before) == 0

    # post_limit_order(
    #     _token_in: address,
    #     _token_out: address,
    #     _amount_in: uint256,
    #     _min_amount_out: uint256,
    #     _valid_until: uint256
    # ):
    amount_in = 100 * 10**6
    min_amount_out = 1 * 10**18
    valid_until = 99999999999

    usdc.approve(spot_limit, amount_in)

    spot_limit.post_limit_order(usdc, weth, amount_in, min_amount_out, valid_until)

    after = spot_limit.get_all_open_positions(owner)
    assert len(after) == 1

    order = after[0]

    # struct LimitOrder:
    #     uid: bytes32
    #     account: address
    #     token_in: address
    #     token_out: address
    #     amount_in: uint256
    #     min_amount_out: uint256
    #     valid_until: uint256
    assert order[1] == owner
    assert order[2] == usdc.address
    assert order[3] == weth.address
    assert order[4] == amount_in
    assert order[5] == min_amount_out
    assert order[6] == valid_until


def test_limit_order_can_be_executed(spot_limit, owner, weth, usdc):
    amount_in = 100 * 10**6
    min_amount_out = 1 * 10**18
    valid_until = 99999999999

    usdc.approve(spot_limit, amount_in)

    spot_limit.post_limit_order(usdc, weth, amount_in, min_amount_out, valid_until)

    order = spot_limit.get_all_open_positions(owner)[0]

    usdc_balance_before = usdc.balanceOf(owner)
    weth_balance_before = weth.balanceOf(owner)

    spot_limit.execute_limit_order(order[0], [usdc.address, weth.address], [500], False)

    usdc_balance_after = usdc.balanceOf(owner)
    weth_balance_after = weth.balanceOf(owner)

    assert usdc_balance_after == usdc_balance_before - amount_in
    assert weth_balance_after >= weth_balance_before + min_amount_out


def test_execute_reverts_with_invalid_path(spot_limit, owner, weth, usdc):
    amount_in = 100 * 10**6
    min_amount_out = 1 * 10**18
    valid_until = 99999999999

    usdc.approve(spot_limit, amount_in)

    spot_limit.post_limit_order(usdc, weth, amount_in, min_amount_out, valid_until)

    order = spot_limit.get_all_open_positions(owner)[0]

    with boa.reverts():
        spot_limit.execute_limit_order(order[0], [weth.address, usdc.address], [500], False)

    with boa.reverts():
        spot_limit.execute_limit_order(order[0], [usdc.address, usdc.address], [500], False)


def test_post_limit_reverts_with_insufficient_allowance(spot_limit, owner, weth, usdc):
    amount_in = 100 * 10**6
    min_amount_out = 1 * 10**18
    valid_until = 99999999999

    assert usdc.allowance(owner, spot_limit) < amount_in

    with boa.reverts("insufficient allowance"):
        spot_limit.post_limit_order(usdc, weth, amount_in, min_amount_out, valid_until)

    

def test_can_cancel_order(spot_limit, owner, weth, usdc):
    amount_in = 100 * 10**6
    min_amount_out = 1 * 10**18
    valid_until = 99999999999

    usdc.approve(spot_limit, amount_in)

    spot_limit.post_limit_order(usdc, weth, amount_in, min_amount_out, valid_until)

    before = spot_limit.get_all_open_positions(owner)
    assert len(before) == 1

    order = before[0]

    spot_limit.cancel_limit_order(order[0])

    after = spot_limit.get_all_open_positions(owner)
    assert len(after) == 0

def test_NON_owner_CANNOT_cancel_order(spot_limit, owner, weth, usdc, alice):
    amount_in = 100 * 10**6
    min_amount_out = 1 * 10**18
    valid_until = 99999999999

    usdc.approve(spot_limit, amount_in)

    spot_limit.post_limit_order(usdc, weth, amount_in, min_amount_out, valid_until)

    before = spot_limit.get_all_open_positions(owner)
    assert len(before) == 1

    order = before[0]

    with boa.env.prank(alice):
        with boa.reverts("unauthorized"):
            spot_limit.cancel_limit_order(order[0])