from django.db import models


class MenuItem(models.Model):
    title = models.CharField(max_length=200)
    order = models.IntegerField(default=0)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    main = models.CharField(max_length=200)
    side = models.CharField(max_length=200)
    time = models.CharField(max_length=200)
    place = models.CharField(max_length=200)
    extra_menu = models.CharField(max_length=200)
    extra_price = models.IntegerField(default=0)
    day = models.CharField(max_length=200)
    price = models.IntegerField(default=0)
    pork = models.BooleanField(default=False)
    url = models.CharField(max_length=200)

    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.title
