from django.db import models

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    source = models.CharField(max_length=50, default='Steam')

    def __str__(self):
        return f"{self.name} ({self.source})"

class Game(models.Model):
    itad_id = models.CharField(max_length=255, unique=True, db_index=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    banner_url = models.URLField(blank=True, null=True)
    
    genres = models.ManyToManyField(Genre, blank=True, related_name='games')
    tags = models.ManyToManyField(Tag, blank=True, related_name='games')

    current_best_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    current_best_store = models.CharField(max_length=100, blank=True, null=True)
    historical_low_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    historical_low_store = models.CharField(max_length=100, blank=True, null=True)
    last_price_sync = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title