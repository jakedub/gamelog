from django.db import models
from .catalog import Game

class PriceAlert(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='price_alerts')
    target_price = models.DecimalField(max_digits=8, decimal_places=2)
    preferred_store = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    triggered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Alert: {self.game.title} @ ${self.target_price}"

class PriceHistory(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='price_history')
    store_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    regular_price = models.DecimalField(max_digits=8, decimal_places=2)
    cut_percentage = models.PositiveSmallIntegerField(default=0)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.game.title} - ${self.price} on {self.store_name}"