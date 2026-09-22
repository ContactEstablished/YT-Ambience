
int id=(int)floor(UV.x/2.);float2 corner=float2(UV.x-id*2.,UV.y);
float3 seed=float3(solar.hash(float3(id,.71,2.31)),solar.hash(float3(id,1.17,5.1)),solar.hash(float3(id,3.19,7.3)));
float time=SolarTime*FlareActivity;float3 p;float light;float3 color;
if(id<5400){
 int loopId=id%72;float3 n,tang;float4 data;solar.loopData(loopId,n,tang,data);
 float life=frac(time*(.065+seed.y*.065)+seed.x);
 float eruption=smoothstep(.15,.90,sin(time*.23+floor(seed.x*9.)));
 float height=life*(.18+seed.z*.55);
 p=n*(1.005+height)+tang*((seed.y-.5)*.10+life*life*.22)+cross(n,tang)*(seed.z-.5)*life*.11;
 light=pow(1.-life,2.)*smoothstep(0.,.08,life)*eruption*saturate(FlareActivity*24.-loopId);
 color=float3(2.8,.58,.018);
}else{
 int eventId=(id-5400)/360;float4 a,b,c;float3 n,tang;solar.eventData(eventId,a,b,c,n,tang);
 float age=saturate((time-a.x)/a.y);float strength=solar.smooth(age/.12)*(1.-solar.smooth((age-.48)/.52))*saturate(FlareActivity*5.-a.z);
 float flight=saturate((age-seed.x*.20)/.65),distance=b.x*(.5+seed.y)*flight;
 float spread=b.y*(.4+flight*2.),angle=seed.z*6.28318+c.x*flight;
 float3 local=float3(b.w*flight*flight,0,1.+distance);
 local.xy+=float2(cos(angle),sin(angle))*spread*seed.x;local.y+=sin(c.y+flight*4.)*flight*.14;
 p=tang*local.x+cross(n,tang)*local.y+n*local.z;
 light=smoothstep(0.,.04,flight)*(1.-smoothstep(.35,1.,flight))*(1.-step(.5,a.w))*strength*c.z;
 color=float3(1.8,.14,.002)*.45;
}

float3 pos=solar.toUE(solar.rotate(p,SolarTime*RotationSpeed))*SunSize;
pos.yz+=(corner-.5)*(.8+seed.z*1.1);
return pos-World;
