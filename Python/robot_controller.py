import rtde_control, math

class Robot:
    def __init__(self, ip, rot, theta, orig, calibration, logger):
        """Initialises new robot controller object.

        Args:
            ip (string): IPv4 address of robot to manage
            rot (list<double>): Reprensentation of TCP rotation in radians
            theta (double): Rotation angle around Z for transformation
            orig (list<double>): Origin of robot
            calibration (list<double>): List of offsets to x, y, z positions for minor calibrations
            logger (Logger): Logger object 

        Returns:
            New Robot object
        """

        # Define controller and connection IP
        self.controller = None
        self.ip_addr = ip

        # Set transformation parameters
        self.rot = rot
        self.theta = theta
        self.orig = orig
        self.calibration = calibration

        # Internal command logger
        self.logger = logger

    def ConnectController(self):
        """Connects controller to robot using previously defined values.
        Will disconnect first if connection is already estabished

        Returns:
            None
        """

        # Disconnect from any previous connection
        if self.controller is not None and self.controller.isConnected():
            self.Disconnect()

        # Establish connection
        self.controller = rtde_control.RTDEControlInterface(self.ip_addr)

        # Log action
        self.logger.LogData(['Info', 'Robot connected'])
    
    def Disconnect(self):
        """Disconnects controller from robot

        Returns:
            None
        """

        # Disconnect and delete existing controller
        self.controller.disconnect()
        self.controller = None

        # Log action
        self.logger.LogData(['Info', 'Robot disconnected'])
        
    def TransformCoordinates(self, X, Y, Z):
        """Converts given set of coordinates in workspace frame to robot frame.
        Args:
            X (double): X position in workspace frame (in meters)
            Y (double): Y position in workspace frame (in meters)
            Z (double): Z position in workspace frame (in meters)

        Returns:
            Tuple (double, double, double): Set of positions in robot's frame
        """

        # Add any calibration offsets
        X += self.calibration[0]
        Y += self.calibration[1]
        Z += self.calibration[2]

        # Rotate around z axis
        x = X * math.cos(self.theta) + Y * math.sin(self.theta)
        y = X * -math.sin(self.theta) + Y * math.cos(self.theta)
        z = Z

        # Translate positions given robot's origin
        x = self.orig[0] + x
        y = self.orig[1] + y
        z = self.orig[2] + z

        # Log transformation
        self.logger.LogData([x, y, z])

        return (x, y, z)

    def Move(self, X, Y, Z, rotation = None):
        """Moves robot to given position in workspace frame
        Args:
            X (double): X position in workspace frame (in meters)
            Y (double): Y position in workspace frame (in meters)
            Z (double): Z position in workspace frame (in meters)
            rotation (list<double> default None): Expected TCP rotation, will override with defaults if None

        Returns:
            None
        """

        # Determine which rotation to use
        rotation = self.rot if rotation == None else rotation

        # Transform to workspace frame        
        (x, y, z) = self.TransformCoordinates(X, Y, Z)

        # Log move
        self.logger.LogData([x, y, z, rotation])

        # Ensure connection
        if not self.controller.isConnected():
            print("Trying to reestablish robot connection")
            self.ConnectController()

        # Perform move
        self.controller.moveL([x, y, z, rotation[0], rotation[1], rotation[2]], 0.5, 0.5)