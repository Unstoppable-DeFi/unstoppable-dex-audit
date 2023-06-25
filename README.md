# Unstoppable

## Mission
Unstoppable is on a mission to make centralized exchanges obsolete and offer crypto natives and newcomers alike a fully decentralized, permissionless and community owned alternative to centralized exchanges.

This repo contains the contracts for our first step towards that goal, namely spot and margin trading functionality.

## Unstoppable:DEX
The most important thing first: we build on top of existing DeFi liquidity.
We are not just a DEX like Uniswap - in fact we need their liquidity and pools since we build on them.
We are also not just another perp DEX or fork, but instead use a different architecture based on leveraged spot trades where LPs and traders are not taking opposing sides and it's not a zero sum game.

### Spot
Our Spot DEX contracts provide advanced functionality and order types such as Limit Orders, Dollar-Cost-Average (DCA), and soon Trailing Stoplosses and more. All of it is built on top of existing Uniswap v3 liquidity and this is where trades are executed.

The main actors in the Spot DEX are:
1. Traders 
2. Keepers

Secondary actors that are indirectly involved are Uniswap LPs.

Traders can place Limit or DCA orders through our contracts in a permissionless way.
If the specified conditions are met, keepers can then execute the contracts on behalf of the traders.
No assets are deposited in the contracts, only an approval from the traders is needed that allows our contracts to swap the specified asset in exchange for another if conditions are met.

The main contracts here are:
```
contracts/spot-dex/LimitOrders.vy
contracts/spot-dex/Dca.vy
contracts/utils/Univ3Twap.sol
```

### Margin
Our Margin DEX allows traders to trade specific markets with leverage.

The main actors are:
1. Single Sided Liquidity Providers
2. Traders
3. Keepers

Secondary actors that are indirectly involved are Uniswap LPs.

Liquidity Providers can provide single sided liquidity similar to a money market like Aave.
This liquidity can be borrowed by traders in the form of an undercollateralized loan and swapped to another asset to gain leveraged exposure to the price movements of that asset.
Keepers monitor the positions and ensure a maximum sensible leverage is not exceeded in order to protect the system from accruing bad debt. If a positions effective leverage exceeds the maximum allowed leverage for that specific market, keepers can liquidate the position.

Liquidity Providers have the choice to provide liquidity in the "Base LP" pool or the "Safety Module" pool.
The Safety Module pool takes a first loss risk protecting the Base LP in exchange for a higher share of the trading and accruing interest.

Interest is reactive and dynamically adjust based on the utilization ratio (i.e. deposited liquidity vs borrowed amount).

Traders deposit a margin into the Vault and are then allowed to create leveraged spot positions by borrowing from the LPs and swapping to their target asset.

The main contracts here are:
```
contracts/margin-dex/MarginDex.vy
    - contains the trading logic, advanced order types and is the main contract traders interact with
contracts/margin-dex/Vault.vy
    - handles all assets, allows LPs to deposit liquidity and traders to fund their trading accounts
contracts/margin-dex/SwapRouter.vy
    - integrates into the secondary spot markets where swaps are executed (in this implementation only Uni v3)
```

## Development and Testing
We use primarily [Vyper](https://github.com/vyperlang/vyper) for smart contract development and [Titanoboa](https://github.com/vyperlang/titanoboa) for testing.
As python dependency management tool we us [Poetry](https://python-poetry.org/).

To run the tests, clone this repo and execute
```
$ poetry shell
$ poetry install
$ pytest
```

## Contact, learn more & join us
If what we have planned sounds interesting to you or you have any questions don't hesitate to reach out!

You can find us at
* Web: https://unstoppable.ooo
* Discord: https://unstoppable.ooo/discord
* Twitter: https://twitter.com/UnstoppableFi
