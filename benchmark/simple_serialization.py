from pprint import pprint

import marshmallow

from rest_framework import serializers as drf_serializers

import serpy

from utils import benchmark_serialization

import avocato


class DRFSerializer(drf_serializers.Serializer):
    foo = drf_serializers.ReadOnlyField()


class MarshmallowSerializer(marshmallow.Schema):
    foo = marshmallow.fields.Str()


class SerpySerializer(serpy.Serializer):
    foo = serpy.Field()


class AvocatoSerializer(avocato.Serializer):
    foo = avocato.Field()


if __name__ == '__main__':
    data = {'foo': 'bar'}

    serializers = [
        ('DRF', DRFSerializer,),
        ('Marshmallow', MarshmallowSerializer().dump,),
        ('serpy', SerpySerializer,),
        ('avocato', AvocatoSerializer,),
    ]
    pprint(benchmark_serialization(data, serializers, 100))
