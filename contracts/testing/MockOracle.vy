interface ChainlinkOracle:
    def latestRoundData() -> (
      uint80,  # roundId,
      int256,  # answer,
      uint256, # startedAt,
      uint256, # updatedAt,
      uint80   # answeredInRound
    ): view


implements: ChainlinkOracle

@external
def __init__(_answer: int256):
    self.answer = _answer

answer: public(int256) # 8 dec

@view
@external
def latestRoundData() -> (
      uint80,  # roundId,
      int256,  # answer,
      uint256, # startedAt,
      uint256, # updatedAt,
      uint80   # answeredInRound
    ):
    return 1, self.answer, block.timestamp, block.timestamp, 1


@external
def set_answer(_answer: int256): 
    self.answer = _answer


@view
@external
def decimals() -> uint256:
    return 8