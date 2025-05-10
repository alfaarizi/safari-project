from __future__ import annotations

import os
import random
from typing import Dict, List, Optional, Tuple

import pygame

# Initialize pygame mixer
pygame.mixer.init()

class AudioManager:
    """
    Manages all game audio including background music and sound effects.
    Implements singleton pattern to ensure only one audio manager exists.
    """
    _instance = None
    
    def __new__(cls) -> AudioManager:
        if cls._instance is None:
            cls._instance = super(AudioManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        
        # Audio settings
        self.music_volume = 0.5
        self.sfx_volume = 0.7
        self.music_enabled = True
        self.sfx_enabled = True

        # Sound categories (for random selection)
        self.sound_categories: Dict[str, List[str]] = {
            "animal": [],
            "ui": [],
            "vehicle": [],
            "ambient": [],
            "notification": []
        }

        # Paths
        self.sound_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "audio")
        self._ensure_dirs()
        
        # Sound storage
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.music_tracks: Dict[str, str] = {}

        # Current music
        self.current_music: Optional[str] = None
        
        # Reserved channels
        self.ui_channel = pygame.mixer.Channel(0)
        self.ambient_channel = pygame.mixer.Channel(1)
        self.notification_channel = pygame.mixer.Channel(2)
        self.vehicle_channel = pygame.mixer.Channel(3)

        # Load sounds and music
        self._load_sounds()
        self._load_music()

    
    def _ensure_dirs(self):
        """Ensure directory structure exists."""
        # Create base directories if they don't exist
        os.makedirs(os.path.join(self.sound_dir, "sfx"), exist_ok=True)
        os.makedirs(os.path.join(self.sound_dir, "music"), exist_ok=True)
        
        # Create category subdirectories
        for category in self.sound_categories.keys():
            os.makedirs(os.path.join(self.sound_dir, "sfx", category), exist_ok=True)
    
    def _load_sounds(self):
        """Load all sound effects from the assets directory."""
        for category in self.sound_categories.keys():
            category_dir = os.path.join(self.sound_dir, "sfx", category)
            if os.path.exists(category_dir):
                for filename in os.listdir(category_dir):
                    if filename.endswith(('.wav', '.ogg', '.mp3')):
                        sound_name = f"{category}_{os.path.splitext(filename)[0]}"
                        sound_path = os.path.join(category_dir, filename)
                        try:
                            self.sounds[sound_name] = pygame.mixer.Sound(sound_path)
                            self.sounds[sound_name].set_volume(self.sfx_volume)
                            self.sound_categories[category].append(sound_name)
                        except pygame.error:
                            print(f"Error loading sound: {sound_path}")
    
    def _load_music(self):
        """Load all music tracks from the assets directory."""
        music_dir = os.path.join(self.sound_dir, "music")
        if os.path.exists(music_dir):
            for filename in os.listdir(music_dir):
                if filename.endswith(('.wav', '.ogg', '.mp3')):
                    track_name = os.path.splitext(filename)[0]
                    self.music_tracks[track_name] = os.path.join(music_dir, filename)
    
    def play_sound(self, sound_name: str) -> bool:
        """
        Play a sound effect by name.
        Returns True if sound was played, False otherwise.
        """
        if not self.sfx_enabled:
            return False
            
        if sound_name in self.sounds:
            # Determine which channel to use based on sound category
            if sound_name.startswith("ui_"):
                self.ui_channel.play(self.sounds[sound_name])
            elif sound_name.startswith("notification_"):
                self.notification_channel.play(self.sounds[sound_name])
            elif sound_name.startswith("vehicle_"):
                self.vehicle_channel.play(self.sounds[sound_name])
            elif sound_name.startswith("ambient_"):
                self.ambient_channel.play(self.sounds[sound_name])
            else:
                # Use a general channel for other sounds
                pygame.mixer.find_channel().play(self.sounds[sound_name])
            return True
        else:
            print(f"Sound '{sound_name}' not found")
            return False
    
    def play_random_sound(self, category: str) -> bool:
        """
        Play a random sound from the specified category.
        Returns True if sound was played, False otherwise.
        """
        if category in self.sound_categories and self.sound_categories[category]:
            sound_name = random.choice(self.sound_categories[category])
            return self.play_sound(sound_name)
        return False
    
    def play_music(self, track_name: str, fade_ms: int = 1000) -> bool:
        """
        Play a music track by name.
        Fades out current track and fades in new track.
        Returns True if music was started, False otherwise.
        """
        if not self.music_enabled:
            return False
            
        if track_name in self.music_tracks:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(fade_ms)
            
            pygame.mixer.music.load(self.music_tracks[track_name])
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1, fade_ms=fade_ms)  # Loop indefinitely
            self.current_music = track_name
            return True
        else:
            print(f"Music track '{track_name}' not found")
            return False
    
    def stop_music(self, fade_ms: int = 1000) -> None:
        """Stop the currently playing music with optional fade out."""
        pygame.mixer.music.fadeout(fade_ms)
        self.current_music = None
    
    def set_music_volume(self, volume: float) -> None:
        """Set music volume (0.0 to 1.0)."""
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)
    
    def set_sfx_volume(self, volume: float) -> None:
        """Set sound effects volume (0.0 to 1.0)."""
        self.sfx_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.sfx_volume)
    
    def toggle_music(self) -> bool:
        """Toggle music on/off. Returns new state."""
        self.music_enabled = not self.music_enabled
        if not self.music_enabled:
            self.stop_music()
        elif self.current_music:
            self.play_music(self.current_music)
        return self.music_enabled
    
    def toggle_sfx(self) -> bool:
        """Toggle sound effects on/off. Returns new state."""
        self.sfx_enabled = not self.sfx_enabled
        return self.sfx_enabled
    
