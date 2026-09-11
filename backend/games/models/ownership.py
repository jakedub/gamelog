from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .catalog import Game

class GameOwnership(models.Model):
    class Status(models.TextChoices):
        UNPLAYED = 'UNPLAYED', 'Unplayed'
        PLAYING = 'PLAYING', 'Playing'
        COMPLETED = 'COMPLETED', 'Completed'
        ABANDONED = 'ABANDONED', 'Abandoned'
        WISHLIST = 'WISHLIST', 'Wishlist'

    class Platform(models.TextChoices):
        STEAM = 'STEAM', 'Steam'
        GOG = 'GOG', 'Good Ol Games'
        EPIC = 'EPIC', 'Epic Games'
        SWITCH = 'SWITCH 2', 'Nintendo Switch 2'
        PS5 = 'PS5', 'PlayStation 5'
        XBOX = 'XBOX', 'Xbox Series X/S'

    class AccessType(models.TextChoices):
        DIGITAL = 'DIGITAL', 'Digital Purchase'
        PHYSICAL = 'PHYSICAL', 'Physical Disc/Cartridge'
        GAME_PASS = 'GAME_PASS', 'Xbox Game Pass'
        PS_PLUS = 'PS_PLUS', 'PlayStation Plus Extra/Premium'

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='ownerships')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNPLAYED)
    platform = models.CharField(max_length=20, choices=Platform.choices)
    access_type = models.CharField(max_length=20, choices=AccessType.choices, default=AccessType.DIGITAL)
    
    user_rating = models.PositiveSmallIntegerField(
        null=True, blank=True, 
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('game', 'platform')

    def __str__(self):
        return f"{self.game.title} - {self.get_platform_display()}"