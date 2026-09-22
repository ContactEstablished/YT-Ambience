
float r=length(UV-.5)*2.;float light=pow(max(1.-r,0.),2.);
return float4(float3(.75,.48,.25)*light*Stars,1);
