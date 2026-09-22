
int id=(int)floor(UV.x/8.);float rem=UV.x-id*8.;int sheet=(int)floor(rem/2.);
float u=rem-sheet*2.,v=UV.y*2.-1.;float4 a,b,c;float3 n,tang;solar.eventData(id,a,b,c,n,tang);
float time=SolarTime*FlareActivity,age=saturate((time-a.x)/a.y);
float strength=solar.smooth(age/.12)*(1.-solar.smooth((age-.48)/.52))*saturate(FlareActivity*5.-a.z);
float growth=.16+.84*(1.-pow(1.-age,3.));float mode=a.w,eventSeed=c.y;

float angle=sheet*3.14159265/3.+u*c.x;
float ripple=sin(u*19.-age*9.+eventSeed)*.12+sin(u*37.+eventSeed)*.045;
float width=b.y*(.36+u*.9)*(1.+ripple);float3 p;
if(mode<.5){
 p=float3(b.w*u*u*growth,sin(u*3.+eventSeed)*u*u*.12,.995+u*b.x*growth);
 p+=float3(cos(angle),sin(angle),0)*v*width;p.z+=sin(v*5.+u*22.-age*6.)*u*.018;
}else{
 float angleU=u*3.14159265;
 p=float3(cos(angleU)*b.z,b.w*sin(angleU)*.22,sqrt(max(1.-b.z*b.z,0.))-.012+sin(angleU)*b.x*growth);
 float3 outward=normalize(float3(b.x*growth*cos(angleU),0,b.z*sin(angleU)));
 p+=(float3(0,1,0)*cos(angle)+outward*sin(angle))*v*b.y*(.45+.55*sin(angleU));p.y+=ripple*sin(angleU)*.08;
}
p=tang*p.x+cross(n,tang)*p.y+n*p.z;
return solar.toUE(solar.rotate(p,SolarTime*RotationSpeed))*SunSize-World;
