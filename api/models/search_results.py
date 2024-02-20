from django.db import models

from api.models.program import Program
from api.models.search_term import SearchTerm


class SearchResults(models.Model):
    url = models.URLField(max_length=200, unique=True)
    search_term = models.ForeignKey(SearchTerm, on_delete=models.CASCADE)
    position = models.IntegerField()
    date_added = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    program_id = models.ForeignKey(Program, on_delete=models.CASCADE)
    match = models.BooleanField(null=True)

    def __str__(self):
        return self.url

    class Meta:
        ordering = ['-last_updated']
