from django.db import models


class SearchTerm(models.Model):
    term = models.CharField(max_length=100, unique=True)
    date_searched = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now_add=True)
    attempts = models.IntegerField(default=0)

    def __str__(self):
        return self.term
