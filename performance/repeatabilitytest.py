#!/usr/bin/env python3

import csv
from collections import OrderedDict
from os.path import join
import re

import cv2
from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
from scipy.spatial import distance

from performancetest import PerformanceTest

THRESHOLD = 2


class RepeatabilityTest(PerformanceTest):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.common = OrderedDict()
        self.repeating = OrderedDict()

    def run_tests(self):
        count = 0
        for detector in self.detectors:
            count += 1
            print("Running test {}/{} - {}".format(count, len(self.detectors), detector))

            det = self.create_detector(detector)
            self.run_test(detector, det)

    def run_test(self, label, detector):
        common = []
        repeat = []
        pattern = re.compile('(\w+)/img(\d).(\w+)')

        for file in self.files:
            match = pattern.match(file)
            (dir, num, ext) = match.groups()

            print("Processing file {}".format(num))
            image = cv2.imread(file, 0)
            keypoints = self.get_keypoints(image, detector)

            if num is '1':
                baseimg = image
                basepts = keypoints
                common.append(len(basepts))
                repeat.append(len(basepts))
                continue

            h = np.loadtxt(join(dir, 'H1to{}p'.format(num)))
            hi = np.linalg.inv(h)
            mask = self.create_mask(baseimg.shape, hi)

            # Only those that are common
            bpts = []
            for pt in basepts:
                if self.point_in_image(pt.pt, mask):
                    bpts.append(pt)
            bptst = np.vstack([pt.pt for pt in bpts])  # base points as array

            rep = 0
            for point in keypoints:
                tp = self.transform_point(point.pt, hi)
                if self.point_in_image(tp, mask):
                    dists = distance.cdist([tp], bptst)  # Distances from this point to all base points
                    if np.min(dists) < THRESHOLD:        # Smallest distance below threshold?
                        rep += 1

            common.append(len(bpts))
            repeat.append(rep)

        self.common[label] = common
        self.repeating[label] = repeat

    @staticmethod
    def _percent_format(y, position):
        s = str(y * 100)
        return s + '%'

    def show_plots(self):
        ytick = FuncFormatter(self._percent_format)
        fnames = [f.split('/')[1] for f in self.files[1:]]  # filenames

        for (ckey, cval), (tkey, tval) in zip(self.common.items(), self.repeating.items()):
            plt.plot(np.divide(tval[1:], cval[1:]), label=ckey)

        plt.title("2-Repeatability")
        plt.xticks(np.arange(len(fnames)), fnames)
        plt.xlabel("Image")
        plt.gca().yaxis.set_major_formatter(ytick)
        plt.ylim(0, 1)  # 0 % -- 100 %
        plt.legend(loc='best', framealpha=0.5)
        plt.draw()
        plt.savefig(join("results", "repeatability.pdf"))

    def save_data(self):
        with open(join('results', 'repeat-common.csv'), 'w') as f:
            writer = csv.writer(f)
            writer.writerow(list(self.common.keys()))
            writer.writerows(zip(*self.common.values()))

        with open(join('results', 'repeat-repeating.csv'), 'w') as f:
            writer = csv.writer(f)
            writer.writerow(list(self.repeating.keys()))
            writer.writerows(zip(*self.repeating.values()))

if __name__ == '__main__':
    dirs = PerformanceTest.get_dirs_from_argv()
    test = RepeatabilityTest(dirs=dirs, filexts=('pgm', 'ppm'))
    test.run_tests()
    test.show_plots()
    test.save_data()
