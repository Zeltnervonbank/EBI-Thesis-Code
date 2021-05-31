import os
from util import select_n_vals, stringify_complex, get_unique_name, parse_string_to_complex

class DataPoint:
    def __init__(self, cse_x, cse_y, vme_x) -> None:
        self.cse_x = cse_x
        self.cse_y = cse_y
        self.vme_x = vme_x

        self.distance = cse_x - vme_x
        self.cse_key = '%f %f' %(cse_x, cse_y)
    
    def SetData(self, contents, samples_taken):
        data_dict = {}
        iterator = 0

        for freq in range(15):
            if freq not in data_dict.keys():
                data_dict[freq] = []

            for _ in range(samples_taken):
                # Get value
                string_val = contents[iterator]

                data_dict[freq].append(parse_string_to_complex(string_val))
                iterator += 1
        self.data = list(data_dict.values())


def parse_to_datapoints(data, samples_taken):
    groups = []
    points = []

    for line in data:
        split_data = line.split('; ')
        header_data = split_data[0:9]
        freq_data = split_data[9:]

        point = DataPoint(
            float(header_data[1])*1000,
            float(header_data[2])*1000,
            float(header_data[5])*1000
        )
        point.SetData(freq_data, samples_taken)
        
        points.append(point)
        
        if len(points) == 6:
            groups.append(points)
            points = []

    return groups

def select_frequency_values(point, num_vals):
    vals = [select_n_vals(point_data, num_vals) for point_data in point.data]
    return vals

def select_values(data, num_vals):
    return [select_frequency_values(point, num_vals) for point in data]

if __name__ == "__main__":  
    folder_path = 'E:/Tissue data in'
    output_path = 'E:/Tissue training data'

    files = os.listdir(folder_path)

    for path in files:
        file_path = os.path.join(folder_path, path)

        data = None

        with open(file_path, 'r+') as f:
            data = f.readlines()

        groups = parse_to_datapoints(data, 200)

            
        num_vals = 1


        l_x = 0
        l_y = 0

        for position_data in groups:
            vals = select_values(position_data, num_vals)

            for n in range(num_vals):
                lines = []
                for i, d in enumerate(position_data):
                    complex_vals = [stringify_complex(vals[i][freq_i][n]) for freq_i in range(15)]

                    new_point = [l_y, l_x, 10, d.cse_x, d.cse_y, d.distance]
                    new_point.extend(complex_vals)

                    l = '; '.join([str(x) for x in new_point]) + '\n'
                    lines.append(l)

                with open(os.path.join(output_path, get_unique_name(position_data[0].cse_key)), 'w+') as f:
                    f.writelines(lines)                    
            