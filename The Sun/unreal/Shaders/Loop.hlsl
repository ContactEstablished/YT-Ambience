
int id=(int)floor(UV.x/2.);float u=UV.x-id*2.;float3 n,tang;float4 data;solar.loopData(id,n,tang,data);
float t=SolarTime*FlareActivity,phase=data.z;
float life=smoothstep(-.5,.7,.65*sin(t*data.w+phase)+.35*sin(t*data.w*1.713+phase*3.1))*saturate(FlareActivity*24.-id);
float profile=max(1.-abs(UV.y-.5)*2.,0.);float thread=pow(profile,2.5),core=pow(profile,12.);
float flow=.65+.35*sin(u*65.-t*3.+phase);
return float4(lerp(float3(2.,.10,.002),float3(3.8,1.1,.065),core)*life*thread*flow*FlareIntensity,1);
