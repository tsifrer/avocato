import time


class DummyObject(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, dict):
                v = DummyObject(**v)
            if isinstance(v, list):
                v = [DummyObject(**attrs) for attrs in v]
            setattr(self, k, v)


def time_serialization(serializer, num_objects, data):
    objects = [DummyObject(**data) for x in range(num_objects)]
    many = num_objects > 1
    if not many:
        objects = objects[0]

    time_start = time.time()
    serializer(objects, many=many).data
    total_time = time.time() - time_start
    return total_time


def benchmark_serialization(data, serializers_tuple, num_objects, repetitions=10):
    benchmarks = {}
    for serializer_name, serializer in serializers_tuple:
        times = []
        for _ in range(repetitions):
            total_time = time_serialization(serializer, num_objects, data)
            times.append(total_time)

        avg_time = sum(times) / len(times)
        benchmarks[serializer_name] = {
            'Num objects': num_objects,
            'Times': times,
            'Avg time': avg_time,
            'Avg objects/s': num_objects / avg_time
        }
    return benchmarks
