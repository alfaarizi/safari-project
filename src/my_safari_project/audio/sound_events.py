from typing import Dict, Any
import pygame

from my_safari_project.audio.sound_effects import (
    play_animal_sound,
    play_footsteps,
    play_jeep_start,
    play_jeep_move,
    play_jeep_stop,
    play_jeep_crash
)

class SoundEventHandler:
    """
    Handles sound event connections for game entities.
    Can be used to attach sound callbacks to entity events.
    """
    
    def __init__(self):
        # Store active entity sound states
        self.entity_states: Dict[int, Dict[str, Any]] = {}
        
        # Jeep movement sounds
        self.active_jeep_sounds: Dict[int, bool] = {}
        
        # Timer for ambient sounds
        self.ambient_timer = 0
        
    def register_entity(self, entity_id: int, entity_type: str) -> None:
        """Register an entity for sound tracking."""
        self.entity_states[entity_id] = {
            "type": entity_type.lower(),
            "moving": False,
            "sound_cooldown": 0,
            "last_position": None
        }
    
    def unregister_entity(self, entity_id: int) -> None:
        """Unregister an entity from sound tracking."""
        if entity_id in self.entity_states:
            del self.entity_states[entity_id]
        if entity_id in self.active_jeep_sounds:
            del self.active_jeep_sounds[entity_id]
    
    def update(self, dt: float) -> None:
        """Update sound states and timers."""
        # Update cooldowns
        for entity_id in self.entity_states:
            if self.entity_states[entity_id]["sound_cooldown"] > 0:
                self.entity_states[entity_id]["sound_cooldown"] -= dt
        
        # Update ambient timer
        self.ambient_timer -= dt
        if self.ambient_timer <= 0:
            self.ambient_timer = 30.0 
    def on_entity_move(self, entity_id: int, position, speed: float = 0.0) -> None:
        """
        Called when an entity moves.
        Plays movement sounds based on entity type and speed.
        """
        if entity_id not in self.entity_states:
            return
            
        entity = self.entity_states[entity_id]
        entity_type = entity["type"]
        
        # Get previous position
        last_pos = entity["last_position"]
        entity["last_position"] = position
        
        # If we don't have a previous position yet, just store this one
        if last_pos is None:
            return
            
        # Check if the entity is actually moving (compare positions)
        moving = (position != last_pos)
        
        # If movement state changed, potentially play sounds
        if moving != entity["moving"]:
            entity["moving"] = moving
            
            # Handle jeep movement sounds specially
            if entity_type == "jeep":
                if moving and entity_id not in self.active_jeep_sounds:
                    play_jeep_start()
                    # A slight delay before the moving sound starts
                    pygame.time.delay(300)
                    play_jeep_move()
                    self.active_jeep_sounds[entity_id] = True
                elif not moving and entity_id in self.active_jeep_sounds:
                    play_jeep_stop()
                    del self.active_jeep_sounds[entity_id]
            
            # Handle footsteps for other entity types
            elif moving and entity["sound_cooldown"] <= 0:
                # Animals make their specific sounds
                if entity_type in ["lion", "tiger", "hyena", "buffalo", 
                                   "elephant", "giraffe", "hippo", "zebra"]:
                    play_animal_sound(entity_type)
                # Other entities have footsteps
                elif entity_type in ["ranger", "tourist", "poacher"]:
                    play_footsteps(entity_type)
                    
                # Set cooldown to avoid sound spam (varies by entity type)
                if entity_type in ["lion", "tiger"]:
                    entity["sound_cooldown"] = 15.0  # Large predators make sounds rarely
                elif entity_type in ["hyena", "buffalo", "elephant", "giraffe", "hippo", "zebra"]:
                    entity["sound_cooldown"] = 10.0  # Herbivores make sounds more often
                else:
                    entity["sound_cooldown"] = 5.0  # People make footstep sounds frequently
    
    def on_entity_collision(self, entity_id: int, other_id: int) -> None:
        """Called when entities collide."""
        if entity_id not in self.entity_states or other_id not in self.entity_states:
            return
            
        entity1_type = self.entity_states[entity_id]["type"]
        entity2_type = self.entity_states[other_id]["type"]
        
        # Jeep crash handling
        if entity1_type == "jeep" or entity2_type == "jeep":
            play_jeep_crash()
        
        # Animal interactions could play specific sounds
        # This would be expanded based on your game's specific interactions
    
    def on_entity_action(self, entity_id: int, action: str) -> None:
        """
        Called when an entity performs a specific action.
        Actions could be: attack, eat, drink, etc.
        """
        if entity_id not in self.entity_states:
            return
            
        entity_type = self.entity_states[entity_id]["type"]
        
        # Handle special actions with sounds based on entity type and action
        if action == "attack":
            if entity_type in ["lion", "tiger", "hyena"]:
                play_animal_sound(entity_type)
        elif action == "drink":
            # Could play a drinking sound
            pass
