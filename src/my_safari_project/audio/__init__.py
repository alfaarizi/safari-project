from my_safari_project.audio.audio_manager import AudioManager
from my_safari_project.audio.sound_events import SoundEventHandler
from my_safari_project.audio.sound_effects import (
    # UI sounds
    play_button_click,
    play_purchase_success,
    play_insufficient_funds,
    play_place_item,
    play_day_transition,
    play_money_received,
    play_footsteps,
    
    # Vehicle sounds
    play_jeep_start,
    play_jeep_move,
    play_jeep_stop,
    play_jeep_crash,
    
    # Animal sounds
    play_animal_sound,
    play_random_animal_sound,
    
    # Music control
    play_game_music,
    play_menu_music,
    stop_music,
    toggle_music,
    toggle_sound_effects,
    set_music_volume,
    set_sfx_volume
)

# Create a single instance of AudioManager to ensure initialization
_audio_manager = AudioManager()

# Create a sound event handler for tracking entity sounds
sound_events = SoundEventHandler()