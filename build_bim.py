import sys
import bpy, math, json
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from pathlib import Path
out = Path(sys.argv[sys.argv.index('--') + 1]).resolve() if '--' in sys.argv else Path('output/bim').resolve()
out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene
s.name='MEP Clash Coordination'
s.unit_settings.system='METRIC'
s.render.engine='BLENDER_WORKBENCH'
s.render.resolution_x=1240
s.render.resolution_y=815
s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'
s.display.shading.light='STUDIO'
s.display.shading.color_type='MATERIAL'
s.display.shading.background_type='WORLD'
s.display.shading.show_shadows=True
s.display.shading.show_cavity=True
s.display.shading.cavity_type='BOTH'
s.display.shading.cavity_ridge_factor=1.25
s.display.shading.cavity_valley_factor=1.15
s.display.shading.show_specular_highlight=True
s.world=bpy.data.worlds.new('Coordination background')
s.world.color=(.63,.68,.72)
def mat(n,color):
 m=bpy.data.materials.new(n);m.diffuse_color=(*color,1);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*color,1);return m
blue=mat('HVAC Blue',(.065,.42,.73)); flange=mat('HVAC Flange',(.075,.235,.34))
green=mat('ELV Green',(.04,.61,.36)); cable=mat('ELV Cable Bundle',(.06,.24,.16))
gray=mat('Structure Gray',(.53,.59,.62)); graydark=mat('Supports Gray',(.26,.31,.35))
fire=mat('Fire Protection Red',(.71,.19,.18)); chilled=mat('Chilled Water Violet',(.42,.30,.65))
amber=mat('Mechanical Orange',(.86,.45,.12)); red=mat('Clash Marker Red',(.99,.04,.06))
def group(n):
 c=bpy.data.collections.new(n);s.collection.children.link(c);return c
struct=group('01_Structure')
mech=group('02_HVAC')
elv=group('03_ELV_movable_tray')
aux=group('04_Coordination_context')
mark=group('05_Clash_volume_annotation')
def assign(n,m,c):
 o=bpy.context.object;o.name=n;o.data.materials.append(m)
 for x in list(o.users_collection):x.objects.unlink(o)
 c.objects.link(o);return o
def box(n,loc,size,m,c):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
 o=bpy.context.object;o.dimensions=size
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 return assign(n,m,c)
def rod(n,a,b,r,m,c):
 a,b=Vector(a),Vector(b);delta=b-a
 bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=r,depth=delta.length,location=(a+b)/2)
 o=bpy.context.object;o.rotation_euler=delta.to_track_quat('Z','Y').to_euler()
 return assign(n,m,c)
for y in [-3.55,3.55]:
 box('Structural Beam',(0,y,4.04),(10.5,.30,.40),gray,struct)
for x in [-5.04,5.04]:
 box('Structural Edge Beam',(x,0,4.04),(.27,7.1,.40),gray,struct)
 for y in [-3.55,3.55]:
  box('Cutaway Column',(x,y,3.25),(.26,.28,1.5),gray,struct)
box('HVAC_Duct_M01',(0,0,2.60),(9.8,1.24,.64),blue,mech)
for x in [-4.85,-3.6,-2.4,-1.2,1.2,2.4,3.6,4.85]:
 box('HVAC_Duct_Flange',(x,0,2.60),(.045,1.31,.71),flange,mech)
for x in [-4.2,-2.2,2.2,4.2]:
 box('HVAC_Trapeze',(x,0,2.25),(.075,1.48,.055),graydark,mech)
 for y in [-.71,.71]:rod('Threaded Hanger',(x,y,2.24),(x,y,3.87),.019,graydark,mech)
box('HVAC_Branch',(-3.62,-1.60,2.66),(.61,2.03,.36),blue,mech)
for y in [-2.55,-1.68]:box('Branch Flange',(-3.62,y,2.66),(.68,.039,.4),flange,mech)
for n,y,z,r,material in [('Sprinkler',-2.40,3.22,.083,fire),('CHWS',1.67,3.38,.115,chilled),('CHWR',2.02,3.38,.115,chilled),('Service Pipe',2.79,2.55,.065,amber)]:
 rod(n,(-4.95,y,z),(4.95,y,z),r,material,aux)
 for x in [-4,-2,2,4]:
  rod(n+' Coupling',(x-.05,y,z),(x+.05,y,z),r*1.19,material,aux)
  rod(n+' Hanger',(x,y,z),(x,y,3.84),.019,graydark,aux)
for x in [-4.1,4.1]:
 for y in [-2.4,-1.35]:
  rod('Sprinkler Drop',(x,y,3.22),(x,y,2.82),.032,fire,aux)
  rod('Sprinkler Head',(x,y,2.82),(x,y,2.77),.075,fire,aux)
state=bpy.data.objects.new('ELV_Tray_E01_Height',None);elv.objects.link(state)
for x in [-.43,.43]:
 box('ELV_Side_Rail',(x,0,2.60),(.07,6.2,.20),green,elv).parent=state
for k in range(25):
 y=-3+k*.25
 box('ELV_Ladder_Rung',(0,y,2.52),(.84,.054,.051),green,elv).parent=state
for x in [-.23,-.14,-.04,.07,.17,.25]:
 rod('ELV_Cables',(x,-3.06,2.586),(x,3.06,2.586),.024,cable,elv).parent=state
for y in [-2.7,-1.42,1.5,2.68]:
 box('ELV_Trapeze',(0,y,2.47),(1.05,.060,.064),graydark,elv).parent=state
for x in [-.51,.51]:
 for y in [-2.7,-1.42,1.5,2.68]:
  o=rod('ELV_Threaded_Hanger',(x,y,2.47),(x,y,3.86),.016,graydark,elv)
  for f,d in [(1,0),(2,-.88)]:
   o.location.z=(2.47+d+3.86)/2;o.scale.z=(3.86-2.47-d)/(3.86-2.47)
   o.keyframe_insert('location',frame=f);o.keyframe_insert('scale',frame=f)
for f,d in [(1,0),(2,-.88)]:
 state.location.z=d;state.keyframe_insert('location',frame=f)
bounds=[(-.48,.48),(-.68,.68),(2.48,2.74)]
for a in range(3):
 o=[k for k in range(3) if k!=a]
 for x in bounds[o[0]]:
  for y in bounds[o[1]]:
   p=[0,0,0];q=[0,0,0];p[a],q[a]=bounds[a];p[o[0]]=q[o[0]]=x;p[o[1]]=q[o[1]]=y
   line=rod('CL01_Clash_outline',p,q,.024,red,mark)
   for f,vis in [(1,False),(2,True)]:
    line.hide_render=vis;line.hide_viewport=vis
    line.keyframe_insert('hide_render',frame=f);line.keyframe_insert('hide_viewport',frame=f)
# Matched cameras make the changed routing easy to compare.
bpy.ops.object.camera_add(location=(8,-10,11.5))
cam=bpy.context.object;cam.name='BIM Technical Axonometric'
cam.rotation_euler=(Vector((0,0,2.78))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=12.0;s.camera=cam
s.frame_start=1;s.frame_end=2
for f,n in [(1,'CL-01 Detected'),(2,'ELV lowered - review')]:s.timeline_markers.new(n,frame=f)
s.frame_set(1)
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.region_3d.view_perspective='CAMERA'
   area.spaces.active.shading.color_type='MATERIAL'
   area.spaces.active.overlay.show_overlays=False
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Velana_MEP_Clash_Node.blend'))
anchors={}
for f,n in [(1,'Clash'),(2,'Resolved')]:
 s.frame_set(f)
 for key,z in [('overlap',2.64),('tray',1.75)]:
  a=world_to_camera_view(s,cam,Vector((0,0,z)))
  anchors[key]=[float(a.x),1-float(a.y)]
 s.render.filepath=str(out/(n+'.png'));bpy.ops.render.render(write_still=True)
(out/'anchors.json').write_text(json.dumps(anchors))
