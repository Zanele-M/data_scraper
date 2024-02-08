from django.db import models


class Program(models.Model):
    program_Id = models.IntegerField()
    program_name = models.CharField(max_length=80)

    def __str__(self):
        return self.program_name
