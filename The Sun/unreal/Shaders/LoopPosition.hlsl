
int id=(int)floor(UV.x/2.);float u=UV.x-id*2.,v=UV.y*2.-1.;
float3 n,tang;float4 data;solar.loopData(id,n,tang,data);float3 side=cross(n,tang);
float t=SolarTime*FlareActivity;float phase=data.z;
float life=smoothstep(-.5,.7,.65*sin(t*data.w+phase)+.35*sin(t*data.w*1.713+phase*3.1));
life*=saturate(FlareActivity*24.-id);
float thick=.012+.026*pow(.5+.5*sin(phase*7.3),3.);
float3 p=n*(.985+sin(u*3.14159265)*data.x)+tang*cos(u*3.14159265)*data.y+side*v*thick;
float h=max(length(p)-1.,0.);p+=normalize(p)*h*(life-.5)*.32;
p+=normalize(p)*sin(u*24.-t*1.1+phase)*.004*sin(u*3.14159265);
return solar.toUE(solar.rotate(p,SolarTime*RotationSpeed))*SunSize-World;
