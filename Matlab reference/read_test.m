
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


nstd_data=zeros();
nstd_data2=zeros();
time_cont = zeros();
x1=zeros();
x2=zeros();

u1 = zeros();
u2 = zeros();


%% FFT STUFF

fftwindowsize = plotsize;

nfft = 2^nextpow2(fftwindowsize); % size of window on which to perform FFT

% Create a frequency axis for ploting
fy = Fs/nfft * (0:(nfft/2) -1);

Y=zeros(nfft,1);
Pyy=zeros(nfft/2,1);

Y_filtered=zeros(nfft,1);
Pyy_filtered=zeros(nfft/2,1);

%% Graph Stuff
plotTitle1 = 'Serial Data Log';  % plot title
xLabel1 = 'Ts';    % x-axis label
yLabel1 = 'Voltage';

plotTitle2 = 'FFT';  % plot title
xLabel2 = 'Freq';    % x-axis label
yLabel2 = 'Power';

plotTitle4 = 'Standard deviation NANSTD';  % plot title
xLabel4 = 'Time';    % x-axis label
yLabel4 = 'Nstd';

%Set up Plot
subplot(3,1,1);

%CHANNEL 1
plotGraph1 = plot(time,data(1,:),'-',...
    'LineWidth',2,...
    'MarkerFaceColor','w',...
    'MarkerSize',2);
hold on


%CHANNEL 2
plotGraph2 = plot(time,data(2,:),'--',...
    'LineWidth',1,...
    'MarkerFaceColor','w',...
    'MarkerSize',2);
hold on

grid();

title(plotTitle1,'FontSize',20);
xlabel(xLabel1,'FontSize',15);
ylabel(yLabel1,'FontSize',15);


subplot(3,1,2);
plotGraph3 = plot(fy,Pyy(1:nfft/2),'-',...
    'LineWidth',1,...
    'MarkerFaceColor','w',...
    'MarkerSize',2);
hold on
title(plotTitle2,'FontSize',20);
xlabel(xLabel2,'FontSize',15);
ylabel(yLabel2,'FontSize',15);


subplot(3,1,3);
plotGraph4 = plot(time_cont,nstd_data,'-',...
    'LineWidth',1,...
    'MarkerFaceColor','w',...
    'MarkerSize',2);
hold on
title(plotTitle4,'FontSize',20);
xlabel(xLabel4,'FontSize',15);
ylabel(yLabel4,'FontSize',15);

plotGraph5 = plot(time_cont,nstd_data2,'--r',...
    'LineWidth',1,...
    'MarkerFaceColor','w',...
    'MarkerSize',2);
hold on
title(plotTitle4,'FontSize',20);
xlabel(xLabel4,'FontSize',15);
ylabel(yLabel4,'FontSize',15);


% axis([0 10 min max]);
grid();

drawnow
%% Reading data setup

packetsize=17;
numread=20; %max 30 as 512 bytes inbuffer


%%
iSample = 1;
timeSample = 1;
time_cont(timeSample) = 1;
ii = 1;
jj = 1;
kk = 1;

while ishandle(plotGraph1) && ishandle(plotGraph2)
    
    if ard.BytesAvailable >= numread*packetsize
        
        for iRead = 1:numread
            
            [A,count] = fread(ard,packetsize,'uint8');
%             disp(A')
%             disp(A(5:6)')

            
            %     ByteOffSet=strfind(A',[Syncbyte1 Syncbyte2] );
            %
            %     if ByteOffSet > 1
            %         [B,count] = fread(ard,ByteOffSet-1,'uint8');
            %         A=[A(ByteOffSet:end); B];
            %     end
            
            %             Chn1= double(swapbytes(typecast(uint8(A(5:6)), 'uint16')));
            %             Chn2= double(swapbytes(typecast(uint8(A(7:8)), 'uint16')));
            
            data(1,iSample)=double(swapbytes(typecast(uint8(A(5:6)), 'uint16'))); % CH1 Channel 1 output HIGH - LOW byte
            data(2,iSample)=double(swapbytes(typecast(uint8(A(7:8)), 'uint16'))); %Channel 2 output
            
%             nstd_data(1,iSample) = nanstd(data(1,iSample));
%             
%             disp(nstd_data(1,iSample))
%             
            
            iSample = iSample + 1;
            if iSample > plotsize
                iSample = 1;
            end
            
        end
        
        %% Filterring OPTIONAL
        F_low = 10;
        F_high = 120;
        [b,a] = butter(3,[F_low,F_high]/(Fs/2));       
        data(1,:) = filtfilt(b,a,data(1,:));     
        data(2,:) = filtfilt(b,a,data(2,:));
        
        %% Fast Fourier transform
        Y = fft (data(1,:), nfft);
        % Convert value to obtain the power of the signal at
        % each frequency
        Pyy = abs(Y(1:nfft/2)).^2/fftwindowsize/Fs;
        
        %% Standard deviation NANSTD()
       
   
        nsdt_val = nanstd(data(1,:));
        nstd_data(timeSample) = nanstd(data(1,:));
        nsdt_val2 = nanstd(data(2,:));
        nstd_data2(timeSample) = nanstd(data(2,:));

      
        %%Sending to Arduino
%         if mod(timeSample,2`) == 0 
%             nstdToSend = int32(nsdt_val);
%             if nstdToSend > 140
%                 nstdToSend = int32(140);
%             end
%             fwrite(ard,nstdToSend);
%             disp(nstdToSend);
%         end
        
        try
            set(plotGraph1,'YData',data(1,:));
            set(plotGraph2,'YData',data(2,:));
            set(plotGraph3,'YData',10*log10(Pyy));
            set(plotGraph4,'YData',nstd_data);
            set(plotGraph4,'XData',time_cont);
            set(plotGraph5,'YData',nstd_data2);
            set(plotGraph5,'XData',time_cont);
        catch
        end
        
        
        if timeSample >= 100
            timeSample = 1;
            time_cont(timeSample) = 1;
        else
            timeSample = timeSample + 1;
            time_cont(timeSample) = time_cont(timeSample-1) + 1;
        end
        
        
        %Input for training model  

        ii = ii + 1;
        
        %% Training
        if mod(ii,2) == 0
            disp(ii)
        end    
        if ii > 50 && ii < 61
            disp('Первый палец');
            x1(jj,1) = nsdt_val;
            x1(jj,2) = nsdt_val2;
            u1(jj,1) = 1;
            u1(jj,2) = 0;
            jj = jj + 1;
        end
        if ii > 100 && ii < 111 
            disp('Второй палец');
            x2(kk,1) = nsdt_val;
            x2(kk,2) = nsdt_val2;
            u2(kk,1) = 0;
            u2(kk,2) = 1;
            kk = kk + 1;
        end
        
 

        drawnow
        
        packetsleft = floor(ard.BytesAvailable/packetsize);
        
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





