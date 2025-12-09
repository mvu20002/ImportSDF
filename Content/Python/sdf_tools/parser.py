import xml.etree.ElementTree as ET
import os
from . import schema
from . import utils

def report(model: schema.Model):
    msg = f"Model: {model.name} readed from SDF\n"
    msg += f"Number of Links: {len(model.links)}\n"
    msg += f"Number of Joints: {len(model.joints)}\n"
    
    total_mass = 0.0
    msg += "\nMass information:\n"
    for link_name, link in model.links.items():
        mass = link.inertial.mass
        total_mass += mass
        msg += f"  - {link_name}: {mass:.3f} kg\n"
    msg += f"Total mass: {total_mass:.3f} kg\n"
    
    msg += "\nMandatory mesh files for creating process:\n"
    unique_meshes = set()
    for link in model.links.values():
        if link.visuals:
            for visual in link.visuals:
                if visual.geometry and visual.geometry.mesh:
                    unique_meshes.add(visual.geometry.mesh.mesh_name)
    for mesh_name in sorted(unique_meshes):
        msg += f"  - {mesh_name}\n"
    return msg

def parse_sdf(sdf_path):
    links = {}
    joints = {}
    model_name = "DefaultModel"

    try:
        if not os.path.exists(sdf_path):
            raise FileNotFoundError(f"SDF not found: {sdf_path}")
        tree = ET.parse(sdf_path)
        root = tree.getroot()
        model = root.find('model')
        if model is None:
            raise ValueError("No <model> element found in SDF.")
        model_name = model.get('name', 'UnnamedModel')
    except Exception as e:
        print(f"Error reading SDF: {e}")
        return None

    if model is not None:
        # --- LINKS ---
        for l in model.findall('link'):
            link_name = l.get('name', 'UnnamedLink')
            pose = utils.parse_pose_text(l.findtext('pose', default="0 0 0 0 0 0"))
            
            visuals = []
            collisions = []

            # Visuals Parsing
            for v in l.findall('visual'):
                v_pose = utils.parse_pose_text(v.findtext('pose', default="0 0 0 0 0 0"))
                transparency = float(v.findtext('transparency', default="0.0"))
                cast_shadows = v.findtext('cast_shadows', default="1") == "1"
                
                geometry = None
                geom_elem = v.find('geometry')
                if geom_elem is not None:
                    mesh_elem = geom_elem.find('mesh')
                    if mesh_elem is not None:
                        uri = mesh_elem.findtext('uri', default="")
                        scale = utils.parse_scale_text(mesh_elem.findtext('scale', default="1 1 1"))
                        
                        # Mesh ismini URI'den temizleyerek çıkar
                        mesh_name = os.path.basename(uri).replace('.dae', '').replace('.stl', '').replace('.obj', '').replace('.', '_')
                        
                        mesh = schema.Mesh(mesh_name, uri, scale)
                        geometry = schema.Geometry(mesh)
                
                visuals.append(schema.Visual(v_pose, geometry, transparency, cast_shadows))

            # Collisions Parsing
            for c in l.findall('collision'):
                c_name = c.get('name', 'UnnamedCollision')
                c_pose = utils.parse_pose_text(c.findtext('pose', default="0 0 0 0 0 0"))
                geometry = None
                geom_elem = c.find('geometry')
                if geom_elem is not None:
                    mesh_elem = geom_elem.find('mesh')
                    if mesh_elem is not None:
                        uri = mesh_elem.findtext('uri', default="")
                        scale = utils.parse_scale_text(mesh_elem.findtext('scale', default="1 1 1"))
                        
                        mesh_name = os.path.basename(uri).replace('.dae', '').replace('.stl', '').replace('.obj', '')
                        mesh = schema.Mesh(mesh_name, uri, scale)
                        geometry = schema.Geometry(mesh)
                
                collisions.append(schema.Collision(c_name, c_pose, geometry))

            # Inertial Parsing
            inertial = schema.Inertial()
            inertial_elem = l.find('inertial')
            if inertial_elem is not None:
                mass = float(inertial_elem.findtext('mass', default="1.0"))
                inertial_pose = utils.parse_pose_text(inertial_elem.findtext('pose', default="0 0 0 0 0 0"))
                
                inertia_elem = inertial_elem.find('inertia')
                if inertia_elem is not None:
                    ixx = float(inertia_elem.findtext('ixx', default="1.0"))
                    ixy = float(inertia_elem.findtext('ixy', default="0.0"))
                    ixz = float(inertia_elem.findtext('ixz', default="0.0"))
                    iyy = float(inertia_elem.findtext('iyy', default="1.0"))
                    iyz = float(inertia_elem.findtext('iyz', default="0.0"))
                    izz = float(inertia_elem.findtext('izz', default="1.0"))
                    inertia_obj = schema.Inertia(ixx, ixy, ixz, iyy, iyz, izz)
                else:
                    inertia_obj = schema.Inertia()
                
                inertial = schema.Inertial(mass, inertial_pose, inertia_obj)

            links[link_name] = schema.Link(link_name, pose, visuals, collisions, inertial)

        # --- JOINTS ---
        for j in model.findall('joint'):
            joint_name = j.get('name', 'UnnamedJoint')
            parent = j.findtext('parent', default="")
            child = j.findtext('child', default="")
            joint_type = j.get('type', 'fixed')
            pose = utils.parse_pose_text(j.findtext('pose', default="0 0 0 0 0 0"))
            
            # Axis
            axis_elem = j.find('axis')
            axis = (0, 0, 0)
            limit = schema.Limit()
            dynamics = schema.Dynamics()
            
            if axis_elem is not None:
                axis_text = axis_elem.findtext('xyz', default="0 0 0")
                vals = [float(v) for v in axis_text.strip().split()]
                vals += [0.0] * (3 - len(vals))
                axis = tuple(vals[:3])

                lim_elem = axis_elem.find('limit')
                if lim_elem is not None:
                    lower = float(lim_elem.findtext('lower', default="0.0"))
                    upper = float(lim_elem.findtext('upper', default="0.0"))
                    effort = lim_elem.findtext('effort')
                    velocity = lim_elem.findtext('velocity')
                    limit = schema.Limit(lower, upper, 
                                         float(effort) if effort else None, 
                                         float(velocity) if velocity else None)

                dyn_elem = axis_elem.find('dynamics')
                if dyn_elem is not None:
                    damping = float(dyn_elem.findtext('damping', default="0.0"))
                    friction = float(dyn_elem.findtext('friction', default="0.0"))
                    dynamics = schema.Dynamics(damping, friction)

            joints[joint_name] = schema.Joint(joint_name, parent, child, joint_type, axis, pose, limit, dynamics)

    return schema.Model(model_name, links, joints)