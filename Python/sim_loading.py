import math, os
from calculation_functions import add_noise_point, lymph_equation, normalise_freq
from util import reshape_data_set_tuples, parse_string_to_complex
from calculation_functions import calc_conductivity, calc_k

def parse_loaded_data(vals, filepath = None, noise = None, distance_filter = None, invert_imag = True):
    """Formats the loaded data into a generic dictionary structure and splits up the complex potential

    Args:
        vals (list<dict>): Loaded values based on used header
        filepath (str): File name including extension of processed file (optional)
        noise (bool): Whether to add noise to the loaded data
        distance_filter (list<int>): List of distances to skip

    Returns:
        list<dict>: A collection of parsed loaded data
    """

    data = []
    for val in vals:
        this_val = {}

        # Handle distance d
        distance = int(val['distance'])
        if distance_filter and distance in distance_filter:
            continue
        this_val['distance'] = distance

        # Load frequency
        this_val['frequency'] = int(val['frequency'])

        (real, imag) = parse_string_to_complex(val['potential'])
        if invert_imag:
            imag = -imag
        this_val['imaginary_potential'] = imag
        this_val['real_potential'] = real

        # Load various integer values if present in data
        optional_int_keys = ['x_dist', 'y_dist', 'lymph_x', 'lymph_y', 'depth']
        for key in optional_int_keys:
            if key in val.keys():
                this_val[key] = int(val[key])

        if 'lymph_size' in val.keys():
            this_val['lymph_size'] = val['lymph_size']

        # Get angle and determine x and y position from it, append angle in degrees
        if 'angle' in val.keys():
            angle_rad = float(val['angle']) * math.pi/180
            this_val['x_dist'] = distance * math.cos(angle_rad)
            this_val['y_dist'] = distance * math.sin(angle_rad)
            this_val['angle'] = int(round(float(val['angle'])))

        # Get coordinates for the data given file path
        if filepath:
            file_name = os.path.splitext(os.path.basename(filepath))[0]
            coordinates = [float(c) for c in file_name.split('_')]
            this_val['position'] = 'X: %d Y: %d Z: %d' % (coordinates[0], coordinates[1], coordinates[2])

        # Add noise to potential if needed
        if noise:
            this_val['imaginary_potential'] = add_noise_point(this_val['imaginary_potential'])
            this_val['real_potential'] = add_noise_point(this_val['real_potential'])

        # Add position of lymph node
        if 'lymph_x' in this_val.keys() and 'lymph_y' in this_val.keys():
            this_val['lymph_key'] = '%d %d' % (this_val['lymph_x'], this_val['lymph_y'])

        if 'lymph_size' in val.keys():
            a = ' s' if val['lymph_size'] == 'small' else ' l'
            this_val['lymph_key'] += a

        data.append(this_val)

    return data


def split_comsol_line(line):
    return list(map(lambda y: y.strip(), filter(lambda x: x != '', line.split('  '))))
    
def load_comsol_with_header(file_path, header, skip_line_count = 5):
    if not os.path.exists(file_path):
        return

    data = []
    with open(file_path, newline='\r\n') as f:
        for index, row in enumerate(f.readlines()):
            if (skip_line_count and index < skip_line_count):
                 continue
            this_line = {}
            split_line = split_comsol_line(row)
            for column in header:
                this_line[column] = split_line[header[column]]
                
            file_name = os.path.split(file_path)
            if file_name[-1][0] == 'D':
                this_line['lymph_size'] = 'small'
            else:
                this_line['lymph_size'] = 'large'

            data.append(this_line)

    return data


def get_data(file_path, header, noise, distance_filter = None):
    """Gets a set of data from a file path given a header format

    Args:
        file_path (str): Path to data file
        header (dict): A dictionary over keys and their column numbers in the data file
        noise (bool) opt: Whether to add noise to the loaded data
        distance_filter (list<int>): List of distances to skip

    Returns:
        list<dict<keys, values>>: A collection of parsed loaded data
    """
    vals = load_comsol_with_header(file_path, header, skip_line_count=5)
    invert_imag = False if 'real' in file_path else True
    
    data = parse_loaded_data(vals, noise = noise, distance_filter = distance_filter, invert_imag=invert_imag)

    return data

def get_data_grid(file_path, header, noise = None, distance_filter = None):
    """Gets a set of grid based data from a file path given a header format

    Args:
        file_path (str): Path to data file
        header (dict): A dictionary over keys and their column numbers in the data file
        noise (bool) opt: Whether to add noise to the loaded data
        distance_filter (list<int>): List of distances to skip

    Returns:
        list<dict<position, dict<keys, values>>>: A collection of parsed loaded data
    """

    data = get_data(file_path, header, noise, distance_filter)
    
    data_dict = {}

    # Depths for lymph equation
    depths = []

    for val in data:
        depths.append(val['depth'])

        # Generate a key to uniquely identify probe position
        key = '%s %s' % (val['x_dist'], val['y_dist'])

        # Add lymph position to key if present
        if 'lymph_key' in val.keys():
            key = '%s %s' % (key, val['lymph_key'])

        # Sort the data into bins based on key
        if key in data_dict.keys():
            data_dict[key].append(val)
        else:
            data_dict[key] = [val]

    # Deduplicate depths
    depths = set(depths)
    if len(depths) > 1:
        raise Exception('Same data set can\'t have more than one depth')

    return data_dict, list(depths)[0]


def calc_conductivities(data):
    conductivities = []
    for i, (an, real, imag) in enumerate(data):
        if i == 0: continue
        
        (am, prev_real, prev_imag) = data[i-1]

        real_diff = prev_real - real
        imag_diff = prev_imag - imag

        k = calc_k(am, an)
        sigma = calc_conductivity(real_diff, imag_diff, k)

        conductivities.append(sigma)
    return conductivities


def load_data(file_path, header, data_type, samples_to_group, noise = False):
    X_grid, depth_ground = get_data_grid(file_path, header, noise)

    data = reshape_data_set_tuples(X_grid, samples_to_group)

    for index, vals in enumerate(data):
        conductivities = calc_conductivities(vals[1])
        
        data[index].append(conductivities)

        data[index].append(sum(vals[4])/len(vals[4]))

    if data_type == 'training':
        l_type = 0
        if 's' in list(X_grid.keys())[0]:
            l_type = 1

        ret = [[val[3], lymph_equation(val[1][0], val[1][1], depth_ground, val[2][0]-8, val[2][1], l_type)] for val in data]
        return ret

    elif data_type == 'test':
        return data

    raise Exception('Could not parse meaning of data')
    

def load_training_data(headers, paths, samples_to_group, augment=True, normalise_frequency=True):
    training_data = []
    for header, folder_path in zip(headers, paths):

        if not os.path.exists(folder_path):
            raise FileNotFoundError('Folder does not exist')

        dirlist = os.listdir(folder_path)

        for filename in dirlist:
            print('Loading %s' % filename)
            training_data.extend(load_data(os.path.join(folder_path, filename), header, 'training', samples_to_group))
            if augment:
                print('Augmenting...\n')
                for _ in range(15):
                    training_data.extend(load_data(os.path.join(folder_path, filename), header, 'training', samples_to_group, noise = True))

    x_train = [val[0] for val in training_data]
    if normalise_frequency:
        x_train = normalise_freq(x_train)

    y_train = [val[1] for val in training_data]

    return x_train, y_train