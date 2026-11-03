from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    x: int


def run(inputs):
    return {"out": Point(inputs["n"]).x}
