import enum


class Network(enum.StrEnum):
    ETHEREUM = "ethereum"
    BNB = "bnb"
    SOLANA = "solana"


class TransactionType(enum.StrEnum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"


class TransactionStatus(enum.StrEnum):
    PENDING = "pending"
    BROADCASTED = "broadcasted"
    CONFIRMED = "confirmed"
    FAILED = "failed"
