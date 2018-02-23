k_size = 20;
i_size = 2;
j_size = 2;

generations = 10000;

H = zeros();
H_evol = zeros(i_size,j_size,k_size);

X{1} = x1;
X{2} = x2;
p1 = zeros();
p2 = zeros();


% u = H*x

for k=1:k_size
    for i=1:i_size
        for j=1:j_size
            H(i,j,k) = rand();
        end
    end
end


for g=1:generations

    for k=1:k_size
        HH = H(:,:,k);
        uu1{k} = zeros();
        uu2{k} = zeros();
        uu1{k} = (HH*X{1}')';
        uu2{k} = (HH*X{2}')';

        u_error1{k} = u1 - uu1{k};
        u_error2{k} = u2 - uu2{k};

        p1(k) = sum(sum( abs(u_error1{k}) + abs(u_error2{k}) ));
%         p2(k) = sum(sum(abs(u_error2{k})));
    end    

    p = p1;
    [s,i] = sort(p);

    H_king = H(:,:,i(1));
    H_evol(:,:,1) = H_king;
    
    disp(s(1));
    
    kking = i(1);

    for k=2:2:(k_size/2)
        if k ~= 2
            kk = k-1;
        else
            kk = k;
        end
        H_evol(1,:,kk) = H(1,:,i(k));
        H_evol(2,:,kk) = H(2,:,i(k+1));
    end

    for k=(k_size/2-1):k_size
        for i=1:i_size
            for j=1:j_size
                H_evol(i,j,k) = rand();
            end
        end
    end
    
    H = H_evol;

end

H_sk = H(:,:,kking);

u_result1 = (H_sk*x1')';
u_result2 = (H_sk*x2')';
