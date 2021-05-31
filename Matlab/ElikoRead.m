function [ZModule, ZPhase] = ElikoRead()
    ZModule = single.empty(0);
    ZPhase = single.empty(0);
    try
        PicometerControl('Start');
    catch exception
        PicometerControl('Stop');
        PicometerControl('Start');
    end

    Data = PicometerControl('GetData', 99);
    
    ZModule = vertcat(ZModule, Data.ImpedanceModule);
    ZPhase = vertcat(ZPhase, Data.ImpedancePhase);

    PicometerControl('Stop');
end