import datetime
from time import time

from django.db import models




types = [('Father','Father'),('Mother','Mother'),('Cousin','Cousin'),('Sister','Sister'),('Brother','Brother')]
class Profile(models.Model):
    first_name = models.CharField(max_length=70)
    last_name = models.CharField(max_length=70)
    date = models.DateField(default=True)
    phone = models.BigIntegerField()
    email = models.EmailField()
    status = models.CharField(max_length=70)
    image = models.ImageField()
    updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.first_name +' '+self.last_name


class LastFace(models.Model):
    last_face = models.CharField(max_length=200)
    date = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.last_face

class MainUser(models.Model):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    user_name = models.CharField(max_length=20)
    email = models.EmailField()
    password = models.CharField(max_length=200)

    def register(self):
        return self.save()

    @staticmethod
    def loginByUsername(username):
        try:
            return MainUser.objects.get(user_name=username)
        except:
            return False