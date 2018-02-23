
if ~isempty(instrfind)
    fclose(instrfind);
end

s = serial('COM3');
set(s,'BaudRate',115200);
fopen(s);

j = 200;
i = 0;

% fprintf(s,0);

while i < j
%     fwrite(s,i);
    disp(i)
    fwrite(s,i);
%     in = fread(s);
    pause(0.5);
    if i < (j - 10)
        i = i + 10;
    else
        i = 0;
    end
end

i=0;
fwrite(s,i);
fclose(s);