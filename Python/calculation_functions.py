import math
import numpy as np

# Classes

class ConductivitySet:
    def __init__(self, connection, cse_position, vme_positions):
        self.data = []
        self.raw_data = []
        self.conductivity_series = []
        self.conductivities = []
        self.connection = connection
        self.cse_position = cse_position
        self.vme_positions = vme_positions

    def Reset(self):
        self.data = []
        self.raw_data = []
        self.conductivity_series = []
        self.conductivities = []

    def ScaleData(self, data):
        return [(val[0] * 0.001, val[1] * 0.001) for val in data]

    def AddData(self, data, index = None):
        median_data = get_complex_medians_from_rectangular(data)

        # Convert to voltage
        scaled_data = self.ScaleData(median_data)

        if index is None:
            self.data.append(scaled_data)
            self.raw_data.append(data)
        else:
            self.data[index] = scaled_data
            self.raw_data[index] = data

        self.connection.send(self.StringifyData(self.data, 'R'))

        if not len(self.data) > 1: return

        distances = [euclid_distance(self.cse_position, p) for p in self.vme_positions]

        conductivity_series = calculate_conductivity_series(self.data, distances)
        self.conductivities = conductivity_series
        self.connection.send(self.StringifyData(conductivity_series, 'C'))    

    def StringifyData(self, data, prefix):
        joined_series = []
        for series in data:
            joined_series.append(';'.join([str(val) for val in series]))
        stringified = prefix + '[' + '|'.join(joined_series) + ']'
        return stringified

# Functions

def euclidean_distance(x1, y1, x2, y2):
    return math.sqrt(pow(x1 - x2, 2) + pow(y1 - y2, 2))

def euclid_distance(p1, p2):
    (x1, y1) = p1
    (x2, y2) = p2
    return euclidean_distance(x1, y1, x2, y2)

def euclid_dist_nd(p1, p2):
    return math.sqrt(sum([pow(v1 - v2, 2) for v1, v2 in zip(p1, p2)]))        

def calc_k(am, an):
    return 1/am - 1/an

def get_complex_medians_from_rectangular(data, format_vals = False):
    medians = []
    for fbin in data.values():
        sorted_bin = sorted(fbin, key=lambda x: x[0])
        med_i = int(len(fbin)/2)

        selected_val = None
        if len(fbin) % 2 == 0:
            med1 = sorted_bin[med_i-1]
            med2 = sorted_bin[med_i]

            selected_val = ((med1[0] + med2[0]) / 2, (med1[1] + med2[1]) / 2)
        else:
            selected_val = sorted_bin[med_i]
        medians.append(selected_val)
    
    if format_vals:
        medians = ["%f %f" % (val[0], val[1]) for val in medians]

    return medians

def get_means(data, format_vals = False):
    means = []
    for fbin in data.values():
        sorted_bin = list(sorted(fbin, key=lambda x: x[0]))
        reduced = sorted_bin[50:-50]

        total_real = sum([v[0] for v in reduced])
        total_imag = sum([v[1] for v in reduced])
        real_mean = total_real/len(reduced)
        imag_mean = total_imag/len(reduced)
        means.append((real_mean, imag_mean))

    if format_vals:
        means = ["%f %f" % (val[0], val[1]) for val in means]

    return means

def calc_conductivity(real_diff, imag_diff, k):
    return (k / (2 * np.pi)) * real_diff / (pow(real_diff, 2) + pow(imag_diff, 2))

def calculate_conductivity_series_meters(data, distances, offset = 0.5):
    return calculate_conductivity_series(data, [d * 1000 for d in distances], offset)

def calculate_conductivity_series(data, distances, offset = 0.5, digits = 4):
        conductivity_series = []

        for i in range(1, len(data), 1):
            am = distances[i-1] + offset
            an = distances[i] + offset

            k = calc_k(am, an)

            conductivities = []
            # For each frequency
            for prev, curr in zip(data[i-1], data[i]):
                real_diff = curr[0] - prev[0]
                imag_diff = curr[1] - prev[1]                

                sigma = calc_conductivity(real_diff, imag_diff, k)
                sigma = round(sigma, digits)

                conductivities.append(sigma)

            conductivity_series.append(conductivities)

        return conductivity_series

def lymph_equation(x, y, mid, lymph_x, lymph_y, l_type):
    var = 1 if l_type == 1 else 2
    if mid > -25:
        cor_x = x-lymph_x
        cor_y = y-lymph_y
        if var:
            p = pow(cor_x,2)/pow(10,2)+pow(cor_y,2)/pow(5,2)
            if p > 1:
                return 0
            else:
                return 1
            #((1/2) * (math.sqrt(25 - math.pow(cor_x,2) - (4*math.pow(cor_y,2))))) - 5 + mid
            #((1/2) * (math.sqrt(100 - math.pow(cor_x,2) - (4*math.pow(cor_y,2))))) - 5 + mid           #Accurate ground truth for 10x5x5 node
            #(1/12 * (math.sqrt(7056 - (49 * math.pow(cor_x,2)) - (144 * math.pow(cor_y,2))))) - 5 + mid               #Extended to 12x7x7
            #(1/8 * (math.sqrt(576 - (9 * math.pow(cor_x,2)) - (64 * math.pow(cor_y,2))))) - 5 + mid                     #Extended to 8x4x4
        else:
            p = pow(x,2)/pow(25,2)+pow(y,2)/pow(10,2)
            if p > 1:
                return 0
            else:
                return 1
            #((1/5)*(math.sqrt(625-(4*math.pow(cor_x,2))-(25*math.pow(cor_y,2))))) - 10 + mid
            #((1/5)*(math.sqrt(2500-(4*math.pow(cor_x,2))-(25*math.pow(cor_y,2))))) - 10 + mid           #Accurate ground truth for 25x10x10 node
            #((1/9)*(math.sqrt(11664-(16*math.pow(cor_x,2))-(81*math.pow(cor_y,2))))) - 10 + mid         #Extended to 27x12x12
            #((1/23)*(math.sqrt(33856-(64*math.pow(cor_x,2))-(529*math.pow(cor_y,2))))) - 10 + mid         #Extended to 23x8x8
        return 1
    else:
        return 0

def normalise_freq(data):
    freq_max = 349
    freq_min = 1

    output = []
    for val in data:
        output.append((val[3] - freq_min)/(freq_max - freq_min))

    return data

def add_noise_point(data, mean = 1, std_dev = 0.001):
    return float(data * np.random.normal(mean, std_dev))
