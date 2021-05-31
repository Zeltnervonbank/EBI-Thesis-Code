from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern
from modAL.models import BayesianOptimizer
from modAL.acquisition import max_EI
from calculation_functions import euclid_distance
from matplotlib import pyplot
import numpy as np
import random

def get_as_initial_points(bounds):
    (left, bottom, right, top) = bounds
    left *= 1000
    bottom *= 1000
    right *= 1000
    top *= 1000

    p1 = (left * 0.9, bottom * 0.9)
    p2 = (left * 0.9, top * 0.9)
    p3 = (right * 0.9, top * 0.9)
    p4 = (right * 0.9, bottom * 0.9)
    p5 = (0, 0)

    return [p1, p2, p3, p4, p5]

def save_as_data(data):
    with open('as-log.txt', 'a+') as f:
        line = '; '.join([str(v) for v in data]) + '\n'
        f.write(line)

def plot_as_data(data, file_number):
    zs = [v[0] for v in data]
    xs = [v[1] for v in data]
    ys = [v[2] for v in data]

    fig = pyplot.figure()
    ax = fig.add_subplot()
    ax.set_xlabel('x (mm)', labelpad=10)
    ax.set_ylabel('y (mm)', labelpad=10)
    ax.set_aspect(1)
    ax.set_title("Confidence")

    surf = ax.tricontourf(xs, ys, zs, cmap='coolwarm', antialiased=False)
    pyplot.scatter(xs, ys, c='r')
    fig.colorbar(surf, shrink=0.5, aspect=5)

    pyplot.savefig('as images/AL %d.png' % (file_number))
    pyplot.close('all')

class AreaSearch:
    def __init__(self, positions):
        positions = [(x*1000, y*1000) for x, y in positions]
        
        self.possible_positions = set(positions)
        self.optimizer = None

    def GetNPositions(self, n = 3):
        vals = random.sample(self.possible_positions, n)
        for val in vals:
            self.TryRemovePoint(val)
        return vals

    def TryRemovePoint(self, point, exclusion_radius = None):
        if point in self.possible_positions:
            self.possible_positions.remove(point)

        if exclusion_radius is not None:
            for p in [v for v in self.possible_positions]:
                if euclid_distance(point, p) < exclusion_radius:
                    self.possible_positions.remove(p)

        print('%d positions remaining' % (len(self.possible_positions)))

    def Setup(self, initial_vals):
        kernel = Matern(length_scale=1.0)
        regressor = GaussianProcessRegressor(kernel=kernel)

        val_init = [v[0] for v in initial_vals]
        pos_init = [[v[1], v[2]] for v in initial_vals]

        self.optimizer = BayesianOptimizer(estimator=regressor, X_training=pos_init, y_training=val_init, query_strategy=max_EI)

    def GetNewPos(self):
        xy_vals = [[x, y] for x, y in self.possible_positions]
        _, query_inst = self.optimizer.query(xy_vals)
        (n_x, n_y) = query_inst[0]
        self.TryRemovePoint((n_x, n_y), exclusion_radius = 3)

        return (n_x, n_y)

    def TeachModel(self, position, confidence):
        pos = np.array([position[0], position[1]])        
        self.optimizer.teach(pos.reshape(1, -1), [confidence])