from robot_controller import Robot
import math, time
from util import Logger

robot_1_ip = 'xxx.xxx.xxx.xxx'
robot_2_ip = 'xxx.xxx.xxx.xxx'

theta1 = 2.3549
theta2 = 1.179

ur1_Org = [-0.32676, -0.08233, 0.3335]
ur2_Org = [0.18957, -0.29132, 0.304]

ur1_Rot = [1.92689, 0.90666, -2.179858]
ur2_Rot = [1.764, -1.176, 2.106]


r1_calibration = [0.046, 0.002, 0.0024]
r2_calibration = [0.0535, 0, 0.0015]

def home_robots(robot1, robot2):
    robot1.Move(0.05, 0, 0.15)
    robot2.Move(-0.05, 0, 0.15)
    time.sleep(2)

def calibration(robot, calibration_height = 0.002):
    robot.Move(0, 0, calibration_height)
    input()

def level_step(robot1, robot2):
    last_input = None

    height = 0.06

    while last_input != 'q':
        robot1.Move(0, 0, height)
        robot2.Move(-0.01, 0, height)
        print(height)
        last_input = input()
        if last_input == '-':
            height -= 0.0001
        elif last_input == '+':
            height += 0.0001
        else:
            height -= 0.001

def calibrate_robots(robot1, robot2):    
    calibration(robot1)
    home_robots(robot1, robot2)
    calibration(robot2)

if __name__ == "__main__":             
    robot1 = Robot(robot_1_ip, ur1_Rot, theta1 - (math.pi/2) , ur1_Org, r1_calibration, Logger('r1_log.log'))#, (0.05, 0, 0.15))
    robot1.ConnectController()
    
    robot2 = Robot(robot_2_ip, ur2_Rot, theta2 - (math.pi/2), ur2_Org, r2_calibration, Logger('r2_log.log'))#, (-0.05, 0, 0.15))
    robot2.ConnectController()
    
    home_robots(robot1, robot2)
    #calibrate_robots(robot1, robot2)
    level_step(robot1, robot2)
    home_robots(robot1, robot2)
