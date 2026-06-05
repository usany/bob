from django.db import models


class MenuItem(models.Model):
    id = models.CharField(max_length=200, primary_key=True)
    main = models.CharField(max_length=200)
    side = models.CharField(max_length=200)
    enmain = models.CharField(max_length=200, null=True, blank=True)
    enside = models.CharField(max_length=200, null=True, blank=True)
    place = models.CharField(max_length=200)
    extra = models.CharField(max_length=200, null=True, blank=True)
    date = models.CharField(max_length=200, null=True, blank=True)
    day = models.CharField(max_length=200, null=True, blank=True)
    meal = models.CharField(max_length=200, null=True, blank=True)
    price = models.CharField(max_length=200, null=True, blank=True)
    stamp = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['place']
    
    def __str__(self):
        return self.main
