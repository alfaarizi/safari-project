# tourist_ai.py
from typing import Optional
from pygame.math import Vector2
from my_safari_project.model.tourist import Tourist
import random
import math


MAX_WAITING_TOURISTS = 30

class TouristAI:
    def __init__(self, board, capital, feedback_callback=None):
        self.board = board
        self.capital = capital
        self._tourist_timer = 0.0
        self._base_tourist_interval = 12.0  # Base interval when no animals
        self._min_tourist_interval = 3.0    # Minimum interval with many animals
        self._next_tourist_id = 1
        self._feedback = feedback_callback

    def update(self, dt: float):
        # Calculate dynamic spawn interval based on animals
        current_interval = self._calculate_spawn_interval()
        
        self._tourist_timer += dt
        if self._tourist_timer > current_interval:
            self._spawn_tourist()
            self._tourist_timer = 0.0

        # Check waiting tourists for available jeeps
        self._assign_waiting_tourists_to_jeeps()

        for tourist in self.board.tourists[:]:
            tourist.update(dt, self.board)
            tourist.detect_animals(self.board.animals, 5.0)

            if (
                tourist.in_jeep and
                tourist.in_jeep.at_path_end() and
                any(tourist.in_jeep.position.distance_to(exit_pos) < 1.0 for exit_pos in self.board.exits)
            ):
                tourist.exit_jeep()


            if tourist.is_done():
                reward = 200 + 30 * len(tourist.seen_animals)
                self.capital.addFunds(reward)
                self.board.tourists.remove(tourist)
                if tourist in self.board.waiting_tourists:
                    self.board.waiting_tourists.remove(tourist)
                if self._feedback:
                    self._feedback(f"Tourist#{tourist.id} saw {len(tourist.seen_animals)} animals → ${reward}")

    def _calculate_spawn_interval(self) -> float:
        if not self.board.animals:
            return self._base_tourist_interval
        
        # Count animals by type
        carnivore_count = 0
        herbivore_count = 0
        
        for animal in self.board.animals:
            if animal.is_alive:
                # Assuming species enum values: 0-2 are carnivores, 3-7 are herbivores
                if animal.species.value <= 2:  # hyena, lion, tiger
                    carnivore_count += 1
                else:  # buffalo, elephant, giraffe, hippo, zebra
                    herbivore_count += 1
        
        # Calculate attraction score
        attraction_score = carnivore_count * 2 + herbivore_count * 1
        
        if attraction_score <= 0:
            return self._base_tourist_interval
        
        # Calculate interval: more animals = lower interval
        spawn_multiplier = max(0.2, 1.0 / (1 + attraction_score * 0.15))
        interval = self._base_tourist_interval * spawn_multiplier
        
        return max(self._min_tourist_interval, interval)

    def _calculate_spawn_batch_size(self) -> int:
        if not self.board.animals:
            return 1
        
        # Count unique species
        unique_species = set()
        for animal in self.board.animals:
            if animal.is_alive:
                unique_species.add(animal.species.value)
        
        species_count = len(unique_species)
        
        # More species diversity = larger batches
        if species_count >= 6:
            return 3
        elif species_count >= 4:
            return 2
        else:
            return 1

    def _spawn_tourist(self):
        if len(self.board.waiting_tourists) >= MAX_WAITING_TOURISTS:
            return


        if not self.board.entrances:
            return

        # Calculate batch size based on animal diversity
        batch_size = self._calculate_spawn_batch_size()

        # Spawn multiple tourists per batch
        for _ in range(batch_size):
            # Pick a random entrance for each tourist
            entrance = random.choice(self.board.entrances)
            offset_angle = random.uniform(0, 2 * math.pi)
            offset_radius = random.uniform(0.3, 0.6)  # small radius
            offset = Vector2(
                offset_radius * math.cos(offset_angle),
                offset_radius * math.sin(offset_angle)
            )
            tourist = Tourist(self._next_tourist_id, Vector2(entrance) + offset, board=self.board)
            self._next_tourist_id += 1

            self.board.waiting_tourists.append(tourist)

    def _try_assign_tourist_to_jeep(self, tourist: Tourist) -> bool:
        available_jeeps = self.board.jeeps[:]
        random.shuffle(available_jeeps)
        
        for jeep in available_jeeps:
            # Check if jeep has space and is not at path end
            if len(jeep.tourists) < 4 and not jeep.at_path_end():
                if tourist.enter_jeep(jeep):
                    return True
        return False

    def _assign_waiting_tourists_to_jeeps(self):
        if not self.board.waiting_tourists:
            return
            
        # Check each waiting tourist
        for tourist in self.board.waiting_tourists[:]:
            if self._try_assign_tourist_to_jeep(tourist):
                self.board.waiting_tourists.remove(tourist)
                self.board.tourists.append(tourist)