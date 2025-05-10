from __future__ import annotations

import pygame

from my_safari_project.audio.audio_manager import AudioManager

# Sound effect functions for common game actions
def play_button_click() -> bool:
    """Play UI button click sound."""
    return AudioManager().play_sound("ui_click")

def play_purchase_success() -> bool:
    """Play successful purchase sound."""
    return AudioManager().play_sound("notification_purchase_success")

def play_insufficient_funds() -> bool:
    """Play insufficient funds alert sound."""
    return AudioManager().play_sound("notification_insufficient_funds")

def play_place_item() -> bool:
    """Play placing item on board sound."""
    return AudioManager().play_sound("ui_place")

def play_day_transition() -> bool:
    """Play day transition sound."""
    return AudioManager().play_sound("notification_day_complete")

def play_money_received() -> bool:
    """Play money received sound."""
    return AudioManager().play_sound("notification_money")

def play_jeep_start() -> bool:
    """Play jeep engine start sound."""
    return AudioManager().play_sound("vehicle_jeep_start")

def play_jeep_move() -> bool:
    """Play jeep moving sound."""
    return AudioManager().play_sound("vehicle_jeep_move")

def play_jeep_stop() -> bool:
    """Play jeep engine stop sound."""
    return AudioManager().play_sound("vehicle_jeep_stop")

def play_jeep_crash() -> bool:
    """Play jeep crash sound."""
    return AudioManager().play_sound("vehicle_jeep_crash")

def play_animal_sound(animal_type: str) -> bool:
    """Play sound for specific animal type."""
    return AudioManager().play_sound(f"animal_{animal_type.lower()}")

def play_random_animal_sound() -> bool:
    """Play random animal sound."""
    return AudioManager().play_random_sound("animal")

def play_footsteps(entity_type: str) -> bool:
    """Play footsteps sound for entity type."""
    # Try to play specific footsteps first
    if AudioManager().play_sound(f"ui_footsteps_{entity_type.lower()}"):
        return True
    # Fall back to generic footsteps
    return AudioManager().play_sound("ui_footsteps")

# Music control functions
def play_game_music() -> bool:
    """Play main gameplay background music."""
    return AudioManager().play_music("game_theme")

def play_menu_music() -> bool:
    """Play menu background music."""
    return AudioManager().play_music("menu_theme")

def stop_music() -> None:
    """Stop all music."""
    AudioManager().stop_music()

def toggle_music() -> bool:
    """Toggle music on/off."""
    return AudioManager().toggle_music()

def toggle_sound_effects() -> bool:
    """Toggle sound effects on/off."""
    return AudioManager().toggle_sfx()

def set_music_volume(volume: float) -> None:
    """Set music volume (0.0 to 1.0)."""
    AudioManager().set_music_volume(volume)

def set_sfx_volume(volume: float) -> None:
    """Set sound effects volume (0.0 to 1.0)."""
    AudioManager().set_sfx_volume(volume)