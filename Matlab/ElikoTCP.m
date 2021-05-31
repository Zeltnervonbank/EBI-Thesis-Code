server = tcpserver('0.0.0.0', 30002);

ElikoReconnect()

while 1
    % Read a byte from TCP
    data = read(server, 1, "string"); 
    if strcmp(data, "r")
        ElikoReconnect()
        disp("Reconnecting")
    end
    
    % If control character
    if strcmp(data, "c")
        ZSpectraCount = uint32.empty(0);
        ZModule = single.empty(0);
        ZPhase = single.empty(0);
        while 1
            output = ElikoSample();
            format shortG
            temp = string(mat2str(round(output, 4)));
            response = pad(temp, 30000, 'right', '?');
            disp(response)
            write(server, response, "string");
            break
        end
    end
    % End loop if end char received
    if strcmp(data, "e")
        break;
    end
end

% Cleanup
clear server
PicometerControl('Disconnect');
