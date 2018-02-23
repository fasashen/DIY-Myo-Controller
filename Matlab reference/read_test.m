
com_p='COM3';

%sync sequence
Syncbyte1=hex2dec('a5');
Syncbyte2=hex2dec('5a');
ProtocolByte=2;


ard=ard_init(com_p,115200);
%%

Fs=256; % set on ard code

Twindow =1; % number of seconds to have on screen at once
plotsize=Twindow*Fs;
chn_num=2;

time=(0:plotsize-1)/Fs;
data=zeros(chn_num,plotsize);


%% FFT STUFF

fftwindowsize = plotsize;

nfft = 2^nextpow2(fftwindowsize); % size of window on which to perform FFT

% Create a frequency axis for ploting
fy = Fs/nfft * (0:(nfft/2) -1);

Y=zeros(nfft,1);
Pyy=zeros(nfft/2,1);

%% Graph Stuff
plotTitle1 = 'Serial Data Log';  % plot title
xLabel1 = 'Ts';    % x-axis label
yLabel1 = 'Voltage';

plotTitle2 = 'FFT';  % plot title
xLabel2 = 'Freq';    % x-axis label
yLabel2 = 'Power';

%Set up Plot
subplot(2,1,1);

plotGraph1 = plot(time,data(1,:),'-',...
    'LineWidth',2,...
    'MarkerFaceColor','w',...
    'MarkerSize',2);
hold on
plotGraph2 = plot(time,data(2,:),'-',...
    'LineWidth',1,...
    'MarkerFaceColor','w',...
    'MarkerSize',2);
hold on
title(plotTitle1,'FontSize',20);
xlabel(xLabel1,'FontSize',15);
ylabel(yLabel1,'FontSize',15);
subplot(2,1,2);
plotGraph3 = plot(fy,Pyy(1:nfft/2),'-',...
    'LineWidth',1,...
    'MarkerFaceColor','w',...
    'MarkerSize',2);
hold on
title(plotTitle2,'FontSize',20);
xlabel(xLabel2,'FontSize',15);
ylabel(yLabel2,'FontSize',15);

% axis([0 10 min max]);
% grid(plotGrid);

drawnow
%% Reading data setup

packetsize=17;
numread=20; %max 30 as 512 bytes inbuffer


%%
iSample =1;

while ishandle(plotGraph1) && ishandle(plotGraph2)
    
    if ard.BytesAvailable >= numread*packetsize
        
        for iRead = 1:numread
            
            [A,count] = fread(ard,packetsize,'uint8');
            
            %     ByteOffSet=strfind(A',[Syncbyte1 Syncbyte2] );
            %
            %     if ByteOffSet > 1
            %         [B,count] = fread(ard,ByteOffSet-1,'uint8');
            %         A=[A(ByteOffSet:end); B];
            %     end
            
            %             Chn1= double(swapbytes(typecast(uint8(A(5:6)), 'uint16')));
            %             Chn2= double(swapbytes(typecast(uint8(A(7:8)), 'uint16')));
            
            data(1,iSample)=double(swapbytes(typecast(uint8(A(5:6)), 'uint16')));
            data(2,iSample)=double(swapbytes(typecast(uint8(A(7:8)), 'uint16')));
            
            
            
            iSample = iSample +1;
            if iSample > plotsize
                iSample =1;
            end
            
        end
        
        Y = fft (data(1,:), nfft);
        % Convert value to obtain the power of the signal at
        % each frequency
        Pyy = abs(Y(1:nfft/2)).^2/fftwindowsize/Fs;
        
        
        try
            set(plotGraph1,'YData',data(1,:));
            set(plotGraph2,'YData',data(2,:));
            set(plotGraph3,'YData',10*log10(Pyy));
        catch
        end
        
        drawnow
        
        packetsleft=floor(ard.BytesAvailable/packetsize);
        
        if packetsleft > 20 %max is 30 but lets leave some room
            fprintf(2,'Update rate is too slow!: %d \n',packetsleft);
        end
        
        
        
    end
    
    
    
end


fclose(ard);



%%

% tic
% for ii=1:1000
%     %  Chn1= double(swapbytes(typecast(uint8(A(5:6)), 'uint16')));
%     set(plotGraph1,'XData',time,'YData',data(1,:));
%
% end
% tt=toc/1000;
% disp(tt)





