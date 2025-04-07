from typing import Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from tourist import Tourist

class Jeep:
    def __init__(
        self,
        jeep_id: int,
        capacity: int,
        fuel_level: float,
        position: Tuple[float, float],
        rental_price: float
    ):
        self.jeep_id = jeep_id
        self.capacity = capacity
        self.current_passengers = 0
        self.fuel_level = fuel_level
        self.position = position
        self.is_available = True
        self.rental_price = rental_price

    def move_to(self, dest: Tuple[float, float]) -> None:
        self.position = dest
        self.fuel_level -= 1.0

    def pick_up(self, tourist: "Tourist") -> bool:
        if self.is_available and self.current_passengers < self.capacity:
            self.current_passengers += 1
            return True
        return False

    def drop_off(self, tourist: "Tourist") -> bool:
        if self.current_passengers > 0:
            self.current_passengers -= 1
            return True
        return False

    def refuel(self, amount: float) -> None:
        self.fuel_level += amount

    def rent_out(self) -> None:
        self.is_available = False

    def return_to_garage(self) -> None:
        self.is_available = True
        self.current_passengers = 0

    def __repr__(self) -> str:
        return (
            f"Jeep(id={self.jeep_id}, capacity={self.capacity}, "
            f"passengers={self.current_passengers}, fuel={self.fuel_level}, "
            f"position={self.position}, available={self.is_available}, "
            f"rentalPrice={self.rental_price})"
        )
