import os
from util import progress_bar, flatten_list, parse_string_to_complex, transpose_list_of_lists
from calculation_functions import calculate_conductivity_series, euclidean_distance

# Classes

class Sample:
    def __init__(self, l_x, l_y, depth, c_x, c_y):
        self.gt_x = l_x - 8
        self.gt_y = l_y
        self.depth = depth
        self.x = c_x
        self.y = c_y
        self.raw_data = []
        self.distances = []
        self.conductivities = []
        self.ground_truth = self.CalculateGroundTruthLine()

    def CalculateConductivity(self):
        conductivities = calculate_conductivity_series(self.raw_data, self.distances, offset=0.5, digits=8)
        self.conductivities = flatten_list(transpose_list_of_lists(conductivities))
    
    def CalculateGroundTruth(self):
        return euclidean_distance(self.gt_x, self.gt_y, self.x, self.y) < 5.5

    def CalculateGroundTruthLine(self):
        gt = self.y > -18 and self.y < -2
        return gt

# Functions

def load_real_data(file_path):
    data = None

    # Read all lines in file
    with open(file_path, 'r+') as f:
        data = f.readlines()

    sample = None

    for i, line in enumerate(data):
        # Split line into values and separate header info from measurements
        split_data = line.split('; ')
        header_data = split_data[0:6]
        freq_data = split_data[6:]
        if i == 0:            
            l_x = int(header_data[0])
            l_y = int(header_data[1])
            
            depth = int(header_data[2])

            c_x = float(header_data[3])
            c_y = float(header_data[4])
            sample = Sample(l_x, l_y, depth, c_x, c_y)

        sample.distances.append(float(header_data[5]))
        sample.raw_data.append([parse_string_to_complex(freq_data[freq]) for freq in range(15)])

    return sample

def load_real_model_data(folder_path, data_type):
    files = os.listdir(folder_path)
    p = progress_bar(len(files))
    samples = []
    for path in files:
        file_path = os.path.join(folder_path, path)
        s = load_real_data(file_path)
        s.CalculateConductivity()
        samples.append(s)
        p.step()

    if data_type == 'Train':
        return [(val.ground_truth, val.conductivities) for val in samples]
    else:
        return samples
