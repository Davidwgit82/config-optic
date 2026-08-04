from django.db import models
from django.utils.text import slugify

class TimeMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AutoSlugMixin(models.Model):
    """Mixin pour générer automatiquement un slug depuis 'title' ou 'name'."""

    slug = models.SlugField(max_length=255, unique=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug:
            # Récupère la valeur de 'title' ou 'name' s'ils existent sur le modèle
            source_value = getattr(self, "title", None) or getattr(self, "name", None)

            if source_value:
                self.slug = slugify(source_value)

        super().save(*args, **kwargs)


""" NamedModel """
class NamedModel(AutoSlugMixin, TimeMixin):
    name = models.CharField(max_length=100)

    # def __str__(self):
    #     return self.name

    class Meta:
        abstract = True
