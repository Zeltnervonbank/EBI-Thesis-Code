import socket
from util import parse_string_to_complex

class MatlabSockets:
    def __init__(self, ip_address: str, port: int):
        # Basic setup
        self.ip_addr = ip_address
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Make a huge buffer (There's potentially a lot of data coming from the sensor)
        self.buffer_size = 75000
        self.connected = False

    def Connect(self):
        '''Connect to previously defined connection'''
        self.sock.connect((self.ip_addr, self.port))
        self.connected = True

    def IsConnected(self):
        return self.connected

    def Reset(self):
        self.sock.send(b'r')        

    def GetComplexData(self, retry_no = 0):
        '''
        Get some data from TCP connection

        Args:
            retry_no (int): Retry number, will throw a runtimerror if greater than or equal to 10

        Returns:
            list: a list of dictionaries one for Module and one for Phase angle. Each key is the frequency index (not in kHz), each value is a list of sampled values at that frequency

        '''
        try:
            if not self.connected:
                raise RuntimeError('Socket not connected')

            #if retry_no >= 20:
            #    raise RuntimeError('Too many retries')

            # Send command byte
            self.sock.send(b'c')

            # Get response and format it
            response = self.sock.recv(self.buffer_size).decode('utf-8')
            if not response:
                raise ValueError('No data received, retrying')

            response = response.replace('?', '')
            if response[0] != '[' or response[-1] != ']':
                raise ValueError('Data misshapen, retrying')

            response = response.replace('[', '').replace(']','')

            data_dict = {}
            
            # Split into individual values
            values = response.replace(';', ' ').split(' ')


            # Raise error and try again if lists are not of equal length

            for index, value in enumerate(values):   
                imag = 0
                real = 0
                if 'i' not in value:
                    real = float(value)
                
                else:
                    (imag, real) = parse_string_to_complex(value)

                if real == 0:
                    raise ValueError('Real component was zero, retrying')
               
                # Convert from string
                comp = (real, imag)

                # Determine which bin to place value in based on number of sampled frequencies
                freqbin = index % 15

                # Place value in that bin
                if freqbin not in data_dict.keys():
                    data_dict[freqbin] = []
                data_dict[freqbin].append(comp)
                    
            return data_dict

        except RuntimeError as err:
            print(err)
            raise err

        except ValueError as err:
            print(err)
            self.sock.recv(self.buffer_size)
            return self.GetComplexData(retry_no = retry_no + 1)    
                
        except AttributeError as err:
            print(err)
            return self.GetComplexData(retry_no = retry_no + 1)

        except IndexError as err:
            print(err)
            return self.GetComplexData(retry_no = retry_no + 1)

        except Exception as err:
           raise err

class VisualisationConnection:
    def __init__(self, host, port):
        self.ip = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.sock.connect((self.ip, self.port))

    def send(self, msg):
        msg = msg.encode()
        totalsent = 0
        while totalsent < len(msg):
            sent = self.sock.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent  