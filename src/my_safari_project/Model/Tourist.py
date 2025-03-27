from typing import Tuple

class Tourist:
    def __init__(
        self,
        tourist_id: int,
        name: str,
        budget: float,
        satisfaction: float,
        location: Tuple[float, float]
    ):
        self.tourist_id = tourist_id
        self.name = name
        self.budget = budget
        self.satisfaction = satisfaction
        self.location = location

    def pay(self, amount: float) -> bool:
        if self.budget >= amount:
            self.budget -= amount
            return True
        return False

    def boardJeep(self, jeep: "Jeep") -> bool:
        if jeep.isAvailable and jeep.currentPassengers < jeep.capacity:
            if self.pay(jeep.rentalPrice):
                jeep.currentPassengers += 1
                return True
        return False

    def disembarkJeep(self, jeep: "Jeep") -> bool:
        if jeep.currentPassengers > 0:
            jeep.currentPassengers -= 1
            return True
        return False

    def observeAnimal(self, animal: "Animal") -> None:
        self.satisfaction += 1.0

    def rateExperience(self, score: float) -> None:
        self.satisfaction = (self.satisfaction + score) / 2.0

    def __repr__(self) -> str:
        return (
            f"Tourist(id={self.tourist_id}, "
            f"name={self.name}, budget={self.budget}, "
            f"satisfaction={self.satisfaction}, location={self.location})"
        )
