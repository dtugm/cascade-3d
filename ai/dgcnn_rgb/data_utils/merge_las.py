import laspy
import os

def append_to_las(in_las, out_las):
    with laspy.open(out_las, mode='a') as outlas:
        with laspy.open(in_las) as inlas:
            for points in inlas.chunk_iterator(2_000_000):
                outlas.append_points(points)