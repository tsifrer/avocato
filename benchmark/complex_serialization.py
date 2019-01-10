from pprint import pprint

import marshmallow

from rest_framework import serializers as drf_serializers

import serpy

from utils import benchmark_serialization

import avocato


class SubDRF(drf_serializers.Serializer):
    w = drf_serializers.FloatField()
    x = drf_serializers.SerializerMethodField()
    y = drf_serializers.CharField()
    z = drf_serializers.IntegerField()

    def get_x(self, obj):
        return obj.x + 10


class DRFSerializer(drf_serializers.Serializer):
    foo = drf_serializers.ReadOnlyField()
    bar = drf_serializers.IntegerField()
    sub = SubDRF()
    subs = SubDRF(many=True)


class SubMarshmallow(marshmallow.Schema):
    w = marshmallow.fields.Int()
    x = marshmallow.fields.Method('get_x')
    y = marshmallow.fields.Str()
    z = marshmallow.fields.Int()

    def get_x(self, obj):
        return obj.x + 10


class CallMarshmallowField(marshmallow.fields.Field):

    def _serialize(self, value, attr, obj):
        return value


class MarshmallowSerializer(marshmallow.Schema):
    foo = marshmallow.fields.Str()
    bar = CallMarshmallowField()
    sub = marshmallow.fields.Nested(SubMarshmallow)
    subs = marshmallow.fields.Nested(SubMarshmallow, many=True)


class SubSerpy(serpy.Serializer):
    w = serpy.IntField()
    x = serpy.MethodField()
    y = serpy.StrField()
    z = serpy.IntField()

    def get_x(self, obj):
        return obj.x + 10


class SerpySerializer(serpy.Serializer):
    foo = serpy.StrField()
    bar = serpy.IntField(call=True)
    sub = SubSerpy()
    subs = SubSerpy(many=True)


class SubAvocato(avocato.Serializer):
    w = avocato.IntField()
    x = avocato.MethodField()
    y = avocato.StrField()
    z = avocato.IntField()

    def get_x(self, obj):
        return obj.x + 10


class AvocatoSerializer(avocato.Serializer):
    foo = avocato.StrField()
    bar = avocato.IntField(call=True)
    sub = SubAvocato()
    subs = SubAvocato(many=True)


if __name__ == '__main__':
    data = {
        'foo': 'bar',
        'bar': lambda: 5,
        'sub': {
            'w': 1000,
            'x': 20,
            'y': 'hello',
            'z': 10
        },
        'subs': [{
            'w': 1000 * i,
            'x': 20 * i,
            'y': 'hello' * i,
            'z': 10 * i
        } for i in range(10)]
    }
    serializers = [
        # ('DRF', DRFSerializer,),
        # ('Marshmallow', MarshmallowSerializer().dump,),
        # ('serpy', SerpySerializer,),
        ('avocato', AvocatoSerializer,),
    ]
    pprint(benchmark_serialization(data, serializers, 100))
