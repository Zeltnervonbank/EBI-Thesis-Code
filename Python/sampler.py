from calculation_functions import ConductivitySet
import time
from datetime import datetime
from util import stringify_complex, transpose_list_of_lists

class Sampler:
    def __init__(self, model, sampling_positions, vme_robot, depth_info, dry_run, sampling_info, measurement_conn, visualiser_conn, output_prefix, cse_position, position_indices, cse=None, cse_height=None):
        self.model = model
        self.vme = vme_robot
        self.cse_position = cse_position
        self.sampling_positions = sampling_positions
        self.lift_between = depth_info.lift_between
        self.lift_height = depth_info.lift_height
        self.height = depth_info.InitialHeight()
        self.dry_run = dry_run
        self.sampled_positions = {}
        self.initial_distance = sampling_info.initial_distance
        self.step_size = sampling_info.step_size
        self.measurement_conn = measurement_conn
        self.visualiser_conn = visualiser_conn
        self.cs = ConductivitySet(self.visualiser_conn, self.cse_position, self.sampling_positions)
        self.output_prefix = output_prefix
        self.position_indices = position_indices

        self.cse = cse
        self.cse_height = cse_height

    def Sample(self, index):
        pos = self.sampling_positions[index]       
        vme_height = self.height

        self.vme.Move(pos[0], pos[1], vme_height)

        if self.lift_between:
            self.vme.Move(pos[0], pos[1], vme_height - self.lift_height)

        time.sleep(0.1)

        data = None
        if not self.dry_run:
            for _ in range(10):
                data = self.measurement_conn.GetComplexData()

        if self.lift_between:
            self.vme.Move(pos[0], pos[1], vme_height)
        
        return data

    def SaveData(self, data):
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        val = '; '.join([str(round(v, 4)) for v in data[0]])
        data_vals = ['%s; %s' % (timestamp, val)]
        for freq in data[1].values():
            freq_vals = '; '.join([stringify_complex(v) for v in freq])
            data_vals.append(freq_vals)

        measurement_data = '; '.join(data_vals) + '\r\n'

        with open('data.txt', 'a+') as f:
            f.write(measurement_data)
        pass

    def SampleAll(self):
        self.cs.Reset()
        for i in range(len(self.sampling_positions)):
            data = self.Sample(i)
            if not self.dry_run:
                self.cs.AddData(data)
                if len(self.cs.conductivities) > 0:
                    lastvals = self.cs.conductivities[-1]
                    if max(lastvals) > 20 or min(lastvals) < -20:
                        print("Strange data detected, resetting")
                        self.SampleAll()
                        return
                    pass
        if self.dry_run:
            return

        c_max = max([item for sublist in self.cs.conductivities for item in sublist])
        c_min = min([item for sublist in self.cs.conductivities for item in sublist])
        if c_max > 20 or c_min < -20:
            print("Strange data detected, resetting")
            self.SampleAll()
            return

        for i, val in enumerate(self.sampling_positions):
            data_set = self.cs.raw_data[i]
            pos_data = [v for v in self.output_prefix]
            d = val[0] - self.cse_position[0]
            pos_data.extend([val[0], val[1], d, self.step_size])
            save_data = [pos_data, data_set]
            self.SaveData(save_data)

        cond_data = transpose_list_of_lists(self.cs.conductivities)
        flattened_cond_data = [item for sublist in cond_data for item in sublist]
        prediction = float(self.model.predict([flattened_cond_data])[0])
        print('Confidence: %f' % (prediction))

        if self.position_indices[0] is not None and self.position_indices[1] is not None:
            vis_data = "P[%d;%d;%f]" % (self.position_indices[0], self.position_indices[1], prediction)
            self.visualiser_conn.send(vis_data)

        return prediction