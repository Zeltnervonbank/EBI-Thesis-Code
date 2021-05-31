import math
import numpy as np
from robot_controller import Robot
from robot_sockets import MatlabSockets, VisualisationConnection
from sampler import Sampler
from model_definitions import FunctionalDenseModel
from util import Logger
from active_search import ActiveSearch, save_as_data, get_as_initial_points, plot_as_data
from robot_calibration import r1_calibration, r2_calibration, robot_1_ip, robot_2_ip, ur1_Rot, ur2_Rot, ur1_Org, ur2_Org, theta1, theta2, home_robots

# Classes

class SamplingInfo:
    def __init__(self, initial_d, step_size, sample_count, fixed_distances = None):
        self.initial_distance = initial_d
        self.step_size = step_size
        self.sample_count = sample_count
        self.fixed_distances = fixed_distances

class DepthInfo:
    def __init__(self, surface_height, sampling_depth, lift_height, lift_between):
        self.surface_height = surface_height
        self.sampling_depth = sampling_depth
        self.lift_height = lift_height
        self.lift_between = lift_between

    def InitialHeight(self):
        if self.lift_between:
            return self.surface_height - self.sampling_depth + self.lift_height
        self.surface_height - self.sampling_depth

# Functions

def generate_grid_positions(dimensions, x_samples, y_samples, add_indices = False):
    (x_start, y_start, x_end, y_end) = dimensions
    sampling_positions = []

    for x_index, x in enumerate(np.linspace(x_start, x_end, x_samples)):
        for y_index, y in enumerate(np.linspace(y_start, y_end, y_samples)):
            if add_indices:
                sampling_positions.append((round(x, 5), round(y, 5), x_index, y_index))
            else:
                sampling_positions.append((round(x, 5), round(y, 5)))
    return sampling_positions

def get_vme_sampling_positions(cse_pos, sampling_info):
    (c_x, c_y) = cse_pos
    vme_positions = []
    if sampling_info.fixed_distances is not None:
        for d in sampling_info.fixed_distances:
            m_x = c_x + (d / 1000)
            vme_positions.append((m_x, c_y))

        return vme_positions

    for i in range(sampling_info.sample_count):
        m_x = c_x + sampling_info.initial_distance + sampling_info.step_size * i
        vme_positions.append((m_x, c_y))
    
    return vme_positions

def sample_at_position(model, vme_robot, cse_robot, sampling_info, depth_info, sampling_position, height, matlab_conn = None, vis_conn = None, dry_run = False, safe_move_vme = False):
    (x, y, x_index, y_index) = (0, 0, None, None)

    if len(sampling_position) == 4:
        (x, y, x_index, y_index) = sampling_position
    elif len(sampling_position) == 2:
        (x, y) = sampling_position
    else:
        raise Exception('Sampling position wrong format')
    if safe_move_vme:
        vme_robot.Move(0.045, y, height)

    cse_robot.Move(x, y, height)
    
    vme_positions = get_vme_sampling_positions((x, y), sampling_info)
    output_prefix = [x, y, depth_info.surface_height, depth_info.sampling_depth]
    sampler = Sampler(
        model,
        vme_positions, 
        vme_robot, 
        depth_info,
        dry_run, 
        sampling_info,
        matlab_conn, 
        vis_conn,
        output_prefix,
        (x, y),
        (x_index, y_index))

    if depth_info.lift_between:
        cse_robot.Move(x, y, height - depth_info.lift_height)
    cse_robot.Disconnect()

    prediction = sampler.SampleAll()

    cse_robot.ConnectController()
    if depth_info.lift_between:
        cse_robot.Move(x, y, height)

    return prediction

def grid_sample(model, vme_robot, cse_robot, sampling_info, depth_info, sampling_positions, matlab_conn = None, vis_conn = None, dry_run = False):
    height = depth_info.InitialHeight()
    for i, pos in enumerate(sampling_positions):
        print("Position %d of %d | %s" % (i + 1, len(sampling_positions), str(pos)))
        sample_at_position(model, vme_robot, cse_robot, sampling_info, depth_info, pos, height, matlab_conn, vis_conn, dry_run)

def run_active_search(model, vme_robot, cse_robot, sampling_info, depth_info, possible_positions, bounds, num_samples, matlab_conn = None, vis_conn = None):
    height = depth_info.InitialHeight()    
    a_search = ActiveSearch(possible_positions)

    initial_positions = get_as_initial_points(bounds)
    print("Initial sampling positions")
    print(initial_positions)

    values = []
    for pos in initial_positions:
        vis_conn.send('A[%f;%f]' % (pos[0], pos[1]))
        prediction = sample_at_position(model, vme_robot, cse_robot, sampling_info, depth_info, (pos[0] / 1000, pos[1] / 1000), height, matlab_conn, vis_conn, False, safe_move_vme=True)
        save_as_data([pos[0], pos[1], prediction])
        values.append((prediction, pos[0], pos[1]))
        a_search.TryRemovePoint(pos, exclusion_radius=3)

    a_search.Setup(values)
    plot_as_data(values, 5)

    for i in range(num_samples - 5):
        new_position = a_search.GetNewPos()
        vis_conn.send('A[%f;%f]' % (new_position[0], new_position[1]))
        print('Iteration %d at %f, %f' % (i + 6, new_position[0], new_position[1]))
        prediction = sample_at_position(model, vme_robot, cse_robot, sampling_info, depth_info, (new_position[0] / 1000, new_position[1] / 1000), height, matlab_conn, vis_conn, False, safe_move_vme=True)
        save_as_data([new_position[0], new_position[1], prediction])
        a_search.TeachModel(new_position, prediction)
        values.append((prediction, new_position[0], new_position[1]))
        plot_as_data(values, i+6)


def do_work(mode, surface_level, dry_run=False):
    robot1 = Robot(robot_1_ip, ur1_Rot, theta1 - (math.pi/2) , ur1_Org, r1_calibration, Logger('r1_log.log'))
    robot1.ConnectController()

    robot2 = Robot(robot_2_ip, ur2_Rot, theta2 - (math.pi/2), ur2_Org, r2_calibration, Logger('r2_log.log'))
    robot2.ConnectController()

    home_robots(robot1, robot2)

    conn = None
    matlab_conn = None

    if not dry_run:
        conn = VisualisationConnection('127.0.0.1', 5005)
        conn.connect()
        matlab_conn = MatlabSockets('127.0.0.1', 30007)
        matlab_conn.Connect()

    sampling_info = SamplingInfo(
        initial_d = 0.004, 
        step_size = 0.001, 
        sample_count = 10, 
        fixed_distances=[6, 7, 9, 11, 15, 21] # Overrides above
    )

    depth_info = DepthInfo(
        surface_height = surface_level, 
        sampling_depth = 0.002, 
        lift_height = 0.01, 
        lift_between = True
    )

    model = FunctionalDenseModel('asmodel/model', 75)
    model.load()
    
    if mode == 'grid':
        grid_positions = generate_grid_positions((-0.015, -0.015, 0.015, 0.015), 7, 7, add_indices=True)
        grid_sample(model, robot1, robot2, sampling_info, depth_info, grid_positions, matlab_conn, conn, dry_run=dry_run)

    if mode == 'search':
        bounds = (-0.02, -0.02, 0.02, 0.02)
        grid_positions = generate_grid_positions(bounds, 100, 100)
        run_active_search(model, robot1, robot2, sampling_info, depth_info, grid_positions, bounds, 49, matlab_conn, conn)

    home_robots(robot1, robot2)

    if not dry_run:
        matlab_conn.Disconnect()
    
    robot1.Disconnect()
    robot2.Disconnect()

if __name__ == "__main__":       
    do_work(mode='grid', surface_level=0.046, dry_run=False)