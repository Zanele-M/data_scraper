from rest_framework import serializers

from api.models.search_results import SearchResults


class SearchResultsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchResults
        fields = '__all__'  # You can list the fields you want to include in the serializer.
