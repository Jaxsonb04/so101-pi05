from pathlib import Path
import numpy as np, trimesh, json
# Put the official Handle_SO101.stl (SO-ARM100, STL/SO101/Leader) next to this script.
root=out=Path(__file__).resolve().parent
m=trimesh.load(root/'Handle_SO101.stl',force='mesh')
v=m.vertices.copy(); y=np.abs(v[:,1])
# Increase dovetail clearance locally; preserve the screw bore at |Y| <= 2.1.
# Plateau covers mouth and upper dovetail; taper away from that interface.
w=np.interp(y,[0,2.2,4.4,6.1,12.5],[0,0,1,1,0])
xw=np.clip((v[:,0]+28.2)/0.3,0,1)
zw=np.clip((43.0-v[:,2])/0.25,0,1)
v[:,1]+=np.sign(v[:,1])*0.5*w*xw*zw
expanded=m.copy(); expanded.vertices=v
# Intersection guarantees no material is added to the original outer shape.
new=trimesh.boolean.intersection([m,expanded],engine='manifold')
assert new.is_watertight and new.is_volume
assert len(new.split())==1
added=trimesh.boolean.difference([new,m],engine='manifold').volume
assert abs(added)<0.005, added
assert np.allclose(new.bounds,m.bounds,atol=0.00002)
new.export(out/'Handle_SO101_Slot_Plus_1mm.stl')
R=np.array([[0,0,1],[0,1,0],[-1,0,0]])
posed=new.copy();posed.vertices=posed.vertices@R.T;posed.apply_translation(-posed.bounds[0])
posed.export(out/'Handle_SO101_Slot_Plus_1mm_Upright.stl')
report={'change':'1.0 mm total slot width, 0.5 mm per side','original_volume_mm3':float(m.volume),'revised_volume_mm3':float(new.volume),'removed_mm3':float(m.volume-new.volume),'added_mm3':float(added),'watertight':new.is_watertight,'components':len(new.split()),'upright_dimensions_mm':posed.extents.tolist(),'slot_sections':{}}
for x in [-10,-20]:
 for label,mesh in [('original',m),('revised',new)]:
  sec=trimesh.intersections.mesh_plane(mesh,plane_origin=[x,0,0],plane_normal=[1,0,0])
  # Intersect the section with heights through the dovetail's mouth and channel.
  vals={}
  for z in [38.1,40.0,41.7]:
   hits=[]
   for d in sec:
    for a,b in zip(d[:-1],d[1:]):
     if (a[2]-z)*(b[2]-z)<0:
      hits.append(float(a[1]+(b[1]-a[1])*(z-a[2])/(b[2]-a[2])))
   inner=sorted(y for y in hits if abs(y)<8)
   vals[str(z)]=inner
  report['slot_sections'][str(x)+'_'+label]=vals
(out/'geometry-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
