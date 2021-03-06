from __future__ import unicode_literals
from django.db import models
from django.test import TestCase
from rest_framework import generics, serializers, status
from rest_framework.tests.utils import RequestFactory
import json

factory = RequestFactory()


# Regression for #666

class ValidationModel(models.Model):
    blank_validated_field = models.CharField(max_length=255)


class ValidationModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValidationModel
        fields = ('blank_validated_field',)
        read_only_fields = ('blank_validated_field',)


class UpdateValidationModel(generics.RetrieveUpdateDestroyAPIView):
    model = ValidationModel
    serializer_class = ValidationModelSerializer


class TestPreSaveValidationExclusions(TestCase):
    def test_pre_save_validation_exclusions(self):
        """
        Somewhat weird test case to ensure that we don't perform model
        validation on read only fields.
        """
        obj = ValidationModel.objects.create(blank_validated_field='')
        request = factory.put('/', json.dumps({}),
                              content_type='application/json')
        view = UpdateValidationModel().as_view()
        response = view(request, pk=obj.pk).render()
        self.assertEquals(response.status_code, status.HTTP_200_OK)


# Regression for #653

class ShouldValidateModel(models.Model):
    should_validate_field = models.CharField(max_length=255)


class ShouldValidateModelSerializer(serializers.ModelSerializer):
    renamed = serializers.CharField(source='should_validate_field', required=False)

    class Meta:
        model = ShouldValidateModel
        fields = ('renamed',)


class TestPreSaveValidationExclusions(TestCase):
    def test_renamed_fields_are_model_validated(self):
        """
        Ensure fields with 'source' applied do get still get model validation.
        """
        # We've set `required=False` on the serializer, but the model
        # does not have `blank=True`, so this serializer should not validate.
        serializer = ShouldValidateModelSerializer(data={'renamed': ''})
        self.assertEquals(serializer.is_valid(), False)
