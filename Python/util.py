import inspect, math, uuid, re
from datetime import datetime

# Classes

# Found on stackoverflow
class progress_bar:
    def __init__(self, total):
        self.total = total
        self.iteration = 0
    
    def step(self):
        self.iteration += 1
        self.printProgressBar(self.iteration, self.total)

    # Print iterations progress
    def printProgressBar (self, iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
        """
        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
            printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
        """
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
        # Print New Line on Complete
        if iteration == total: 
            print()


class Logger:
    def __init__(self, path):
        self.path = path

    def LogData(self, data):
        caller = inspect.stack()[1].function
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

        flat_list = [str(item) for item in data]
        str_data = '; '.join(flat_list)
        output_str = '%s | %s | %s\r\n' % (timestamp, caller, str_data)

        with open(self.path, 'a+') as f:
            f.write(output_str)

# Functions

def reshape_data_set_tuples(data, n):
    if isinstance(data, list):
        return reshape_data_tuples(data, n)

    if isinstance(data, dict):
        return [item for sublist in [reshape_data_tuples(sample, n) for sample in data.values()] for item in sublist]

def reshape_data_tuples(data, n):
    if len(data) < n:
        raise IndexError('n can\'t be larger than length of data list')

    data_points = []
    for i in range(len(data) - n + 1):
        data_point = [data[0]['frequency']]
        vals = []
        for x in range(n):
            vals.append((
                data[i + x]['distance'], 
                data[i + x]['real_potential'], 
                data[i + x]['imaginary_potential']
            ))
        data_point.append(vals)

        if 'x_dist' in data[i].keys():
            if'lymph_x' in data[i].keys():
                data_point.append([float(data[i]['x_dist']), float(data[i]['y_dist'])])
                data_point.append([float(data[i]['lymph_x']), float(data[i]['lymph_y'])])
            else:
                data_point.append([float(data[i]['x_dist']), float(data[i]['y_dist'])])
                    

        data_points.append(data_point)

    return data_points  

def save_measurement(data):
    timestamp = datetime.now().strftime("%d-%b-%Y %H:%M:%S.%f")
    val = '; '.join([str(round(v, 4)) for v in data[0]])
    data_vals = ['%s; %s' % (timestamp, val)]
    for freq in data[1].values():
        freq_vals = '; '.join([stringify_complex(v) for v in freq])
        data_vals.append(freq_vals)

    measurement_data = '; '.join(data_vals) + '\r\n'

    with open('data.txt', 'a+') as f:
        f.write(measurement_data)

def select_n_vals(data, n):
    v = sorted(data, key=lambda x: x[0])
    midpoint = math.floor(len(v)/2)
    if n == 1:
        return [v[midpoint]]
    half_n = math.floor(n/2)
    vals = v[midpoint - half_n : midpoint + half_n]
    return vals

def stringify_complex(comp):
    val = f"{(comp[0] * 0.001):.9f}"
    if comp[1] >= 0:
        val += '+'
    val += f"{(comp[1] * 0.001):.9f}"
    val += 'i'
    return val

def get_unique_name(position):
    file_id = uuid.uuid4().hex
    return '%s %s.txt' % (position, file_id)

def stringify_complex_noscale(comp):
    val = f"{comp[0]:.9f}"
    if comp[1] >= 0:
        val += '+'
    val += f"{comp[1]:.9f}"
    val += 'i'
    return val

def flatten_list(l):
    return [item for sublist in l for item in sublist]

def parse_string_to_complex(string_val):
    # Trim end
    string_val = string_val.replace('\n','')

    # Find imaginary part using regex
    m = re.search('[+-][^-+]*i', string_val)
    imag_string = m.group(0)
    imag = float(imag_string.replace('i',''))

    # Find real part by removing imaginary part
    real_string = string_val.replace(imag_string, '')
    real = float(real_string)

    return (real, imag)

def transpose_list_of_lists(l):
    t = []
    for x in range(len(l[0])):
        t.append([v[x] for v in l])

    return t