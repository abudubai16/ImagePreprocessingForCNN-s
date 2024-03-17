import concurrent.futures
import os
from multiprocessing import cpu_count

import cv2
import numpy as np

from ..errors import image_errors
from .. import Operations


class Image:
    def __init__(self, current_paths: np.ndarray, directory: str, bb: np.ndarray = None):
        self.current_paths = current_paths
        self.b_boxes = bb
        self.directory = directory

    def __add__(self, other):
        self.images = np.concatenate(self.images, other.images, axis=1)
        self.b_boxes = np.concatenate(self.b_boxes, other.b_boxes, axis=1)

        if self.directory != other.directory:
            raise image_errors.DirectoryNotSame

        return self

    def __repr__(self):
        if int(np.shape(self.current_paths)[0]) >= 5:
            st = f"Number of images:{int(np.shape(self.current_paths)[0])}\nThe first 5 paths are:"
            for i in range(5):
                st = st + f"\n{self.current_paths[i]}"
        else:
            st = f"Number of images:{int(np.shape(self.current_paths)[0])}\nThe first few paths are:"
            for path in self.current_paths:
                st = st + f"\n{path}"
        return st


class Sequential:
    def __init__(self, operations: list):
        self.operations = operations

    def append(self, operations: list):
        for operation in operations:
            self.operations.append(operation)

    def process(self, data: Image,  chunksize: int = 1, max_workers: int = cpu_count()):

        if chunksize == 1:
            chunksize = int(max(len(data.current_paths)/100, 1))

        os.chdir(data.directory)
        processed_path = f"{data.directory}/processed_images"
        if not os.path.exists(processed_path):
            os.mkdir(processed_path)

        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as Executor:
            executed = Executor.map(self.run_sequential, data.current_paths, chunksize=chunksize)
            processed_img = np.sum([1 for _ in executed if _])

            print(f"For {len(data.current_paths)} images, {processed_img} images were processed\n")

    def run_sequential(self, img_path: str) -> bool:
        try:
            bb = None
            cwd = os.getcwd()
            img = cv2.imread(f"{cwd}/{img_path}.png")
            for img_operation in self.operations:

                if img_operation == Operations.Resize:
                    img, bb = img_operation.run(img, bb)
                else:
                    img = img_operation.run(img)
            cv2.imwrite(f"{cwd}/processed_images/{img_path}", img)

            return True
        except TypeError:
            print(f"File: {img_path}, Error: {TypeError}")
            return False
