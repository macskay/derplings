from dataclasses import dataclass


@dataclass
class InventoryComponent:
    deflator: int = 0
    inflator: int = 0
    jetpack: int = 0
    ladder: int = 0
    rocket: int = 0
    trampoline: int = 0
    stop_sign: int = 0
    tnt: int = 0
    umbrella: int = 0
