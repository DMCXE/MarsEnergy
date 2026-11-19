// CPU studio renderer for the authored triangle meshes. Linear-light shading,
// transparent primary rays, soft shadows, and short-range ambient occlusion.
#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <thread>
#include <vector>
using std::min;
using std::max;
struct V {
    float x,y,z;
    float operator[](int i) const {return i==0?x:i==1?y:z;}
    V operator+(V b) const {return {x+b.x,y+b.y,z+b.z};}
    V operator-(V b) const {return {x-b.x,y-b.y,z-b.z};}
    V operator*(V b) const {return {x*b.x,y*b.y,z*b.z};}
    V operator*(float b) const {return {x*b,y*b,z*b};}
};
float dot(V a,V b){return a.x*b.x+a.y*b.y+a.z*b.z;}
V cross(V a,V b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
V norm(V a){return a*(1.f/std::sqrt(max(dot(a,a),1e-22f)));}
V lower(V a,V b){return {min(a.x,b.x),min(a.y,b.y),min(a.z,b.z)};}
V upper(V a,V b){return {max(a.x,b.x),max(a.y,b.y),max(a.z,b.z)};}
float saturate(float x){return min(1.f,max(0.f,x));}
struct Triangle {V p,e1,e2,n0,n1,n2,lo,hi,center;int mat;};
struct Node {V lo,hi; int begin=0,end=0,left=0,right=0;};
struct Mat {V color;float metal,rough,opacity,emission,texture;};
struct Light {V p;float energy;};
std::vector<Triangle> tris;
std::vector<Node> nodes;
std::vector<Mat> mats;
std::vector<Light> lamps;
int build(int begin,int end){
    Node n;
    n.lo={1e20f,1e20f,1e20f};n.hi=n.lo*-1.f;
    V low=n.lo,high=n.hi;
    for(int i=begin;i<end;i++){
        auto &t=tris[i];n.lo=lower(n.lo,t.lo);n.hi=upper(n.hi,t.hi);
        low=lower(low,t.center);high=upper(high,t.center);
    }
    int id=nodes.size();nodes.push_back(n);
    if(end-begin<=6){nodes[id].begin=begin;nodes[id].end=end;return id;}
    V span=high-low;
    int axis=span.x>span.y?(span.x>span.z?0:2):(span.y>span.z?1:2);
    int mid=(begin+end)/2;
    std::nth_element(tris.begin()+begin,tris.begin()+mid,tris.begin()+end,[axis](const Triangle &a,const Triangle &b){return a.center[axis]<b.center[axis];});
    int left=build(begin,mid),right=build(mid,end);
    nodes[id].left=left;nodes[id].right=right;return id;
}
struct Ray {V o,d,inv;Ray(V o,V dir):o(o),d(dir),inv{1.f/(dir.x+1e-30f),1.f/(dir.y+1e-30f),1.f/(dir.z+1e-30f)}{}};
float entry(const Node &n,const Ray &r,float far){
    V a=(n.lo-r.o)*r.inv,b=(n.hi-r.o)*r.inv;
    V lo=lower(a,b),hi=upper(a,b);
    float near=max(0.f,max(lo.x,max(lo.y,lo.z)));
    return near<=min(far,min(hi.x,min(hi.y,hi.z)))?near:1e30f;
}
struct Hit {float t=1e20f,u=0,v=0;int id=-1;};
Hit trace(const Ray &r,float far=1e20f,bool shadow=false){
    Hit hit;hit.t=far;int stack[96],count=1;stack[0]=0;
    while(count){
        const Node &n=nodes[stack[--count]];
        if(entry(n,r,hit.t)>hit.t)continue;
        if(n.end){
            for(int i=n.begin;i<n.end;i++){
                auto &t=tris[i];
                if(shadow && mats[t.mat].opacity<.8f)continue;
                V p=cross(r.d,t.e2);float det=dot(p,t.e1);
                if(std::abs(det)<1e-12f)continue;
                float inv=1.f/det; V d=r.o-t.p;float u=dot(d,p)*inv;
                if(u<0||u>1)continue;
                V q=cross(d,t.e1);float v=dot(r.d,q)*inv;
                if(v<0||u+v>1)continue;
                float dist=dot(t.e2,q)*inv;
                if(dist<.00009f||dist>hit.t)continue;
                hit={dist,u,v,i};
                if(shadow)return hit;
            }
        }else{
            float a=entry(nodes[n.left],r,hit.t),b=entry(nodes[n.right],r,hit.t);
            if(a<b){if(b<=hit.t)stack[count++]=n.right;if(a<=hit.t)stack[count++]=n.left;}
            else {if(a<=hit.t)stack[count++]=n.left;if(b<=hit.t)stack[count++]=n.right;}
        }
    }
    return hit;
}
struct Random {
    uint32_t seed;
    float get(){seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;return (seed>>8)*(1.f/16777216.f);}
};
V hemisphere(V n,Random &rand){
    V u=norm(cross(std::abs(n.z)>.94f?V{0,1,0}:V{0,0,1},n)),v=cross(n,u);
    float z=std::sqrt(rand.get()),r=std::sqrt(1-z*z),a=6.283185f*rand.get();
    return u*(r*std::cos(a))+v*(r*std::sin(a))+n*z;
}
struct StudioLamp {V toward,tint;float power;};
std::vector<StudioLamp> studio={
    {norm({-.65f,-.61f,1.05f}),{1.f,.935f,.84f},1.32f},
    {norm({.91f,.66f,.74f}),{.48f,.89f,1.f},.70f}
};
float noise(int x,int y,int z){
    uint32_t h=uint32_t(x)*1597334677u ^ uint32_t(y)*3812015801u ^ uint32_t(z)*2798796415u;
    h^=h>>16;h*=2246822519u;h^=h>>13;return float(h>>8)/16777216.f;
}
float grain(V p,float scale){
    p=p*scale;
    int x=std::floor(p.x),y=std::floor(p.y),z=std::floor(p.z);
    float u=p.x-x,v=p.y-y,w=p.z-z,sum=0;
    for(int k=0;k<2;k++)for(int j=0;j<2;j++)for(int i=0;i<2;i++)
        sum+=noise(x+i,y+j,z+k)*(i?u:1-u)*(j?v:1-v)*(k?w:1-w);
    return sum-.5f;
}
V shade(const Ray &ray,const Hit &hit,Random &rand){
    auto &t=tris[hit.id]; auto &m=mats[t.mat];
    V n=norm(t.n0*(1-hit.u-hit.v)+t.n1*hit.u+t.n2*hit.v);
    if(dot(n,ray.d)>0)n=n*-1.f;
    V p=ray.o+ray.d*hit.t;
    V geom=norm(cross(t.e1,t.e2));
    if(dot(geom,n)<0)geom=geom*-1.f;
    V start=p+geom*.0007f;
    Hit occlusion=trace(Ray(start,hemisphere(n,rand)),.88f,true);
    float ao=occlusion.id<0?1.f:(.30f+.70f*std::sqrt(occlusion.t/.88f));
    V color=m.color;
    if(m.texture>0)color=color*(1+m.texture*(.32f*grain(p,12)+.25f*grain(p,54)+.17f*grain(p,210)));
    V light=V{.40f,.44f,.50f}*(ao*(.79f+.21f*n.z));
    V spec={0,0,0};
    for(size_t i=0;i<studio.size();i++){
        const auto &lamp=studio[i];
        V l=norm(lamp.toward+hemisphere(lamp.toward,rand)*(i==0?.26f:i==1?.19f:.65f));
        V tint=lamp.tint;
        float facing=max(0.f,dot(n,l));
        if(facing>.001f&&trace(Ray(start,l),32,true).id<0){
            light=light+tint*(facing*lamp.power);
            float exponent=7+66*(1-m.rough);
            float highlight=std::pow(max(0.f,dot(n,norm(l-ray.d))),exponent);
            spec=spec+tint*(highlight*(.07f+.43f*m.metal));
        }
    }
    for(auto &lamp:lamps){
        V delta=lamp.p-p;float dd=dot(delta,delta);
        if(delta.z<.008f||delta.z>.46f||dd>1.1f)continue;
        light=light+V{1,.88f,.60f}*(lamp.energy*.86f*max(0.f,dot(n,norm(delta)))/(.19f+2.8f*dd));
    }
    V reflected=ray.d-n*(2*dot(ray.d,n));
    float box=std::pow(max(0.f,dot(reflected,norm({-.6f,-.3f,.84f}))),5);
    float edge=std::pow(1-saturate(-dot(n,ray.d)),3);
    return color*(light*(1-.22f*m.metal)+V{1,1,1}*(m.metal*(.09f+.63f*box)*ao+m.emission*.72f))
            +spec+V{.70f,.84f,.89f}*(edge*(.027f+.09f*m.metal)*ao);
}
struct Sample{V rgb;float alpha;};
struct Guide{V normal;float depth;int material=-1;};
Sample sample(Ray r,Random &rand,Guide *guide){
    V color={0,0,0};float trans=1;
    for(int layer=0;layer<14&&trans>.009f;layer++){
        Hit h=trace(r);if(h.id<0)break;
        auto &surface=tris[h.id];
        auto &m=mats[surface.mat];
        if(guide && layer==0){
            guide->normal=norm(surface.n0*(1-h.u-h.v)+surface.n1*h.u+surface.n2*h.v);
            guide->depth=h.t;guide->material=surface.mat;
        }
        float a=m.opacity<1?m.opacity*.51f:1.f;
        color=color+shade(r,h,rand)*(a*trans);
        trans*=1-a;
        r=Ray(r.o+r.d*(h.t+.00035f),r.d);
    }
    return {color,1-trans};
}
unsigned char encode(float x){
    // Gentle highlight shoulder keeps warm emitters and white enamel distinct.
    if(x>.72f)x=.72f+.28f*(1-std::exp(-3.57f*(x-.72f)));
    float s=x<=.0031308f?x*12.92f:1.055f*std::pow(x,1/2.4f)-.055f;
    return static_cast<unsigned char>(saturate(s)*255+.5f);
}
template<typename T> void read(FILE *f,T *ptr,size_t count){
    if(count&&fread(ptr,sizeof(T),count,f)!=count){std::fprintf(stderr,"Invalid scene data\n");std::exit(2);}
}
int main(int argc,char **argv){
    if(argc!=5)return 1;
    FILE *f=fopen(argv[1],"rb");if(!f)return 2;
    uint32_t h[4];read(f,h,4);V eye,axes[3];read(f,&eye,1);read(f,axes,3);
    uint32_t count=0;read(f,&count,1);
    if(count){studio.resize(count);read(f,studio.data(),count);}
    mats.resize(h[1]);lamps.resize(h[2]);read(f,mats.data(),mats.size());read(f,lamps.data(),lamps.size());
    tris.reserve(h[0]);
    for(unsigned i=0;i<h[0];i++){
        V a[6];float material;read(f,a,6);read(f,&material,1);
        V lo=lower(a[0],lower(a[1],a[2])),hi=upper(a[0],upper(a[1],a[2]));
        tris.push_back({a[0],a[1]-a[0],a[2]-a[0],a[3],a[4],a[5],lo,hi,(lo+hi)*.5f,int(material)});
    }
    fclose(f);nodes.reserve(tris.size());build(0,tris.size());
    int width=std::atoi(argv[3]),height=std::atoi(argv[4]),spp=h[3];
    std::vector<unsigned char> pixels(width*height*4);
    std::vector<Guide> guides(width*height);
    std::atomic<int> row{0};
    auto worker=[&](){
        for(int y;(y=row.fetch_add(1))<height;){
            for(int x=0;x<width;x++){
                V color{0,0,0};float alpha=0;
                Random rng{(uint32_t(y*width+x)+1)*2654435761u};
                for(int s=0;s<spp;s++){
                    float jx=(s+rng.get())/spp,jy=(std::fmod(s*.61803399f+rng.get()/spp,1.f));
                    float u=((x+jx)/width-.5f)*.60f,v=(.5f-(y+jy)/height)*.40f;
                    Sample p=sample(Ray(eye,norm(axes[0]*u+axes[1]*v-axes[2])),rng,s==0?&guides[y*width+x]:nullptr);
                    color=color+p.rgb;alpha+=p.alpha;
                }
                size_t i=(y*width+x)*4;
                if(alpha>0){
                    color=color*(1/alpha);pixels[i]=encode(color.x);pixels[i+1]=encode(color.y);pixels[i+2]=encode(color.z);
                    pixels[i+3]=static_cast<unsigned char>(saturate(alpha/spp)*255+.5f);
                }
            }
        }
    };
    std::vector<std::thread> threads;
    for(unsigned i=0;i<max(1u,min(10u,std::thread::hardware_concurrency()));i++)threads.emplace_back(worker);
    for(auto &thread:threads)thread.join();
    // Filter Monte Carlo noise only across nearby samples of the same surface.
    // Alpha stays untouched so comparison plates keep precisely the same silhouette.
    auto filtered=pixels;
    constexpr float kernel[5]={1,4,6,4,1};
    for(int y=2;y<height-2;y++)for(int x=2;x<width-2;x++){
        int i=y*width+x;
        const auto &g=guides[i];
        if(g.material<0 || pixels[i*4+3]!=255)continue;
        float sum=0,channels[3]={0,0,0};
        for(int dy=-2;dy<=2;dy++)for(int dx=-2;dx<=2;dx++){
            int j=i+dy*width+dx;auto &other=guides[j];
            if(other.material!=g.material || pixels[j*4+3]!=255 ||
               std::abs(other.depth-g.depth)>.065f || dot(g.normal,other.normal)<.97f)continue;
            int diff=0;
            for(int c=0;c<3;c++)diff=max(diff,std::abs(int(pixels[i*4+c])-pixels[j*4+c]));
            float weight=kernel[dx+2]*kernel[dy+2]/(1+diff*diff*.0014f);
            sum+=weight;
            for(int c=0;c<3;c++)channels[c]+=weight*pixels[j*4+c];
        }
        if(sum>0)for(int c=0;c<3;c++)filtered[i*4+c]=static_cast<unsigned char>(channels[c]/sum+.5f);
    }
    pixels.swap(filtered);
    f=fopen(argv[2],"wb");if(!f)return 2;
    size_t bytes=fwrite(pixels.data(),1,pixels.size(),f);fclose(f);
    return bytes==pixels.size()?0:3;
}
