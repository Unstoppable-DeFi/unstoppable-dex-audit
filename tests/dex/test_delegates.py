import boa


def test_add_delegate(dex, owner, alice):
    assert not dex.is_delegate(owner, alice)

    dex.add_delegate(alice)

    assert dex.is_delegate(owner, alice)

    
def test_remove_delegate(dex, owner, alice):
    dex.add_delegate(alice)
    assert dex.is_delegate(owner, alice)

    dex.remove_delegate(alice)

    assert not dex.is_delegate(owner, alice)



def test_non_delegate_cannot_open_trade_on_behalf(dex, owner, alice, usdc, weth):
    assert not dex.is_delegate(owner, alice)

    with boa.env.prank(alice):
        with boa.reverts("unauthorized"):
            dex.open_trade(owner, weth, 1, usdc, 1, 1, [], [])

def test_non_delegate_cannot_swap_margin_on_behalf(dex, owner, alice, usdc, weth):
    assert not dex.is_delegate(owner, alice)

    with boa.env.prank(alice):
        with boa.reverts("unauthorized"):
            dex.swap_margin(owner, weth, usdc, 1, 1)

def test_non_delegate_cannot_add_tp(dex, owner, alice, usdc, weth):
    assert not dex.is_delegate(owner, alice)

    with boa.env.prank(alice):
        with boa.reverts("unauthorized"):
            dex.add_tp_order("foo".encode('utf-8'), (1, 1, False))

def test_non_delegate_cannot_add_sl(dex, owner, alice, usdc, weth):
    assert not dex.is_delegate(owner, alice)

    with boa.env.prank(alice):
        with boa.reverts("unauthorized"):
            dex.add_sl_order("foo".encode('utf-8'), (1, 1, False))

def test_non_delegate_cannot_cancel_tp(dex, owner, alice, usdc, weth):
    assert not dex.is_delegate(owner, alice)

    with boa.env.prank(alice):
        with boa.reverts("unauthorized"):
            dex.cancel_tp_order("foo".encode('utf-8'), 0)

def test_non_delegate_cannot_cancel_sl(dex, owner, alice, usdc, weth):
    assert not dex.is_delegate(owner, alice)

    with boa.env.prank(alice):
        with boa.reverts("unauthorized"):
            dex.cancel_sl_order("foo".encode('utf-8'), 0)

def test_non_delegate_cannot_post_limit_order(dex, owner, alice, usdc, weth):
    assert not dex.is_delegate(owner, alice)

    with boa.env.prank(alice):
        with boa.reverts("unauthorized"):
            dex.post_limit_order(owner, weth, usdc, 1, 1, 1, 999, [], [])
