import unreal as ue
import xml.etree.ElementTree as ET
import os
import math
import numpy as np

SI_TO_UE = 100.0  # m -> cm

class Mesh:
    def __init__(self, mesh_name, uri, scale=(1.0, 1.0, 1.0)):
        self.mesh_name = mesh_name
        self.uri = uri
        self.scale = scale

class Geometry:
    def __init__(self, mesh: Mesh=None):
        self.mesh = mesh

class Visual:
    def __init__(self, pose, geometry: Geometry=None, transparency=0.0, cast_shadows=True):
        self.pose = pose
        self.geometry = geometry
        self.transparency = transparency
        self.cast_shadows = cast_shadows

class ODEParams:
    def __init__(self, mu=1.0, mu2=1.0, slip1=0.0, slip2=0.0, slip=0.0):
        self.mu = mu
        self.mu2 = mu2
        self.slip1 = slip1
        self.slip2 = slip2
        self.slip = slip

class Bounce:
    def __init__(self, restitution_coefficient=0.0, threshold=1e+06):
        self.restitution_coefficient = restitution_coefficient
        self.threshold = threshold

class Bullet:
    def __init__(self, split_impulse=1, split_impulse_penetration_threshold=-0.01, soft_cfm=0.0, soft_erp=0.2, kp=1e+13, kd=1.0):
        self.split_impulse = split_impulse
        self.split_impulse_penetration_threshold = split_impulse_penetration_threshold
        self.soft_cfm = soft_cfm
        self.soft_erp = soft_erp
        self.kp = kp
        self.kd = kd

class Contact:
    def __init__(self, collide_without_contact=0, collide_without_contact_bitmask=1, collide_bitmask=1, ode_params: ODEParams=None, bullet: Bullet=None):
        self.collide_without_contact = collide_without_contact
        self.collide_without_contact_bitmask = collide_without_contact_bitmask
        self.collide_bitmask = collide_bitmask
        self.ode = ode_params if ode_params is not None else ODEParams()
        self.bullet = bullet if bullet is not None else Bullet()

class Torsional:
    def __init__(self, coefficient=1.0, patch_radius=0.0, surface_radius=0.0, use_patch_radius=1, ode_params: ODEParams=None):
        self.coefficient = coefficient
        self.patch_radius = patch_radius
        self.surface_radius = surface_radius
        self.use_patch_radius = use_patch_radius
        self.ode = ode_params if ode_params is not None else ODEParams()

class Friction:
    def __init__(self, ode_params: ODEParams=None, torsional: Torsional=None):
        self.ode = ode_params if ode_params is not None else ODEParams()
        self.torsional = torsional if torsional is not None else Torsional()

class Surface:
    def __init__(self, friction: Friction=None, bounce: Bounce=None, contact: Contact=None):
        self.friction = friction if friction is not None else Friction()
        self.bounce = bounce if bounce is not None else Bounce()
        self.contact = contact if contact is not None else Contact()

class Collision:
    def __init__(self, name, pose, geometry: Geometry=None, surface: Surface=None):
        self.name = name
        self.pose = pose  # (x, y, z, roll, pitch, yaw)
        self.geometry = geometry
        self.surface = surface if surface is not None else Surface()

class Inertia:
    def __init__(self, ixx=1.0, ixy=0.0, ixz=0.0, iyy=1.0, iyz=0.0, izz=1.0):
        self.ixx = ixx
        self.ixy = ixy
        self.ixz = ixz
        self.iyy = iyy
        self.iyz = iyz
        self.izz = izz

class Inertial:
    def __init__(self, mass=1.0, pose=(0,0,0,0,0,0), inertia: Inertia=None):
        self.mass = mass
        self.pose = pose  # (x, y, z, roll, pitch, yaw) - center of mass offset
        self.inertia = inertia if inertia is not None else Inertia()

class Link:
    def __init__(self, name, pose, visuals=None, collisions=None, inertial: Inertial=None):
        self.name = name
        self.pose = pose  # (x, y, z, roll, pitch, yaw)
        self.visuals = visuals if visuals is not None else []  # List of Visual objects
        self.collisions = collisions if collisions is not None else []  # List of Collision objects
        self.inertial = inertial if inertial is not None else Inertial()

class Limit:
    def __init__(self, lower=0.0, upper=0.0, effort=None, velocity=None):
        self.lower = lower
        self.upper = upper
        self.effort = effort
        self.velocity = velocity

class Dynamics:
    def __init__(self, damping=0.0, friction=0.0):
        self.damping = damping
        self.friction = friction

class Joint:
    def __init__(self, name, parent, child, joint_type, axis=(0,0,0), pose="0 0 0 0 0 0",
                 limit: Limit=None, dynamics: Dynamics=None):
        self.name = name
        self.parent = parent
        self.child = child
        self.joint_type = joint_type
        self.axis = axis
        self.pose = pose
        self.limit = limit if limit is not None else Limit()
        self.dynamics = dynamics if dynamics is not None else Dynamics()


class Model:
    def __init__(self, name, links=None, joints=None):
        self.name = name
        self.links = links if links is not None else {}
        self.joints = joints if joints is not None else {}

# ---------- POSE / MATRIX HELPERS ----------
def parse_pose_text(text):
    if not text or not text.strip():
        return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    vals = [float(v) for v in text.strip().split()]
    vals += [0.0] * (6 - len(vals))
    return tuple(vals[:6])


def report(model: Model):
    msg = f"Model: {model.name} readed from SDF\n"
    msg += f"Number of Links: {len(model.links)}\n"
    msg += f"Number of Joints: {len(model.joints)}\n"
    
    # Report mass information
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
    """SDF içinden link ve joint bilgilerini oku."""
    links = {}
    joints = {}
    model_name = "DefaultModel"  # Initialize with default value

    # open the sdf file and parse it
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
        model = None
        model_name = "ErrorModel"

    if model is not None:
        for l in model.findall('link'):
            link_name = l.get('name', 'UnnamedLink')
            pose = parse_pose_text(l.findtext('pose', default="0 0 0 0 0 0"))
            visuals = []
            collisions = []
            mesh = None

            for v in l.findall('visual'):
                v_pose = parse_pose_text(v.findtext('pose', default="0 0 0 0 0 0"))
                transparency = float(v.findtext('transparency', default="0.0"))
                cast_shadows = v.findtext('cast_shadows', default="1") == "1"
                geometry = None
                geom_elem = v.find('geometry')
                if geom_elem is not None:
                    mesh_elem = geom_elem.find('mesh')
                    if mesh_elem is not None:
                        uri = mesh_elem.findtext('uri', default="")
                        scale_text = mesh_elem.findtext('scale', default="1 1 1")
                        scale_vals = [float(s) for s in scale_text.strip().split()]
                        scale_vals += [1.0] * (3 - len(scale_vals))
                        scale = tuple(scale_vals[:3])
                        mesh_name = os.path.basename(uri).replace('.dae', '').replace('.stl', '').replace('.obj', '').replace('.', '_')
                        mesh = Mesh(mesh_name, uri, scale)
                        geometry = Geometry(mesh)
                visuals.append(Visual(v_pose, geometry, transparency, cast_shadows))

            for c in l.findall('collision'):
                c_name = c.get('name', 'UnnamedCollision')
                c_pose = parse_pose_text(c.findtext('pose', default="0 0 0 0 0 0"))
                geometry = None
                geom_elem = c.find('geometry')
                if geom_elem is not None:
                    mesh_elem = geom_elem.find('mesh')
                    if mesh_elem is not None:
                        uri = mesh_elem.findtext('uri', default="")
                        scale_text = mesh_elem.findtext('scale', default="1 1 1")
                        scale_vals = [float(s) for s in scale_text.strip().split()]
                        mesh_name = os.path.basename(uri).replace('.dae', '').replace('.stl', '').replace('.obj', '')
                        mesh = Mesh(mesh_name, uri, scale)
                        geometry = Geometry(mesh)
                collisions.append(Collision(c_name, c_pose, geometry))

            # Parse inertial information
            inertial = Inertial()  # Default values
            inertial_elem = l.find('inertial')
            if inertial_elem is not None:
                mass = float(inertial_elem.findtext('mass', default="1.0"))
                inertial_pose = parse_pose_text(inertial_elem.findtext('pose', default="0 0 0 0 0 0"))
                
                # Parse inertia matrix
                inertia_elem = inertial_elem.find('inertia')
                if inertia_elem is not None:
                    ixx = float(inertia_elem.findtext('ixx', default="1.0"))
                    ixy = float(inertia_elem.findtext('ixy', default="0.0"))
                    ixz = float(inertia_elem.findtext('ixz', default="0.0"))
                    iyy = float(inertia_elem.findtext('iyy', default="1.0"))
                    iyz = float(inertia_elem.findtext('iyz', default="0.0"))
                    izz = float(inertia_elem.findtext('izz', default="1.0"))
                    inertia_obj = Inertia(ixx, ixy, ixz, iyy, iyz, izz)
                else:
                    inertia_obj = Inertia()
                
                inertial = Inertial(mass, inertial_pose, inertia_obj)

            links[link_name] = Link(link_name, pose, visuals, collisions, inertial)

        for j in model.findall('joint'):
            joint_name = j.get('name', 'UnnamedJoint')
            parent = j.findtext('parent', default="")
            child = j.findtext('child', default="")
            joint_type = j.get('type', 'fixed')
            limit = Limit()
            dyn   = Dynamics()
            axis_elem = j.find('axis')
            axis = (0, 0, 0)
            if axis_elem is not None:
                axis_text = axis_elem.findtext('xyz', default="0 0 0")
                axis_vals = [float(a) for a in axis_text.strip().split()]
                axis_vals += [0.0] * (3 - len(axis_vals))
                axis = tuple(axis_vals[:3])

                lim_elem = axis_elem.find('limit')
                if lim_elem is not None:
                    lower = float(lim_elem.findtext('lower', default="0.0"))
                    upper = float(lim_elem.findtext('upper', default="0.0"))
                    effort = lim_elem.findtext('effort')
                    velocity = lim_elem.findtext('velocity')
                    limit = Limit(lower, upper,
                                float(effort) if effort is not None else None,
                                float(velocity) if velocity is not None else None)

                dyn_elem = axis_elem.find('dynamics')
                if dyn_elem is not None:
                    damping  = float(dyn_elem.findtext('damping',  default="0.0"))
                    friction = float(dyn_elem.findtext('friction', default="0.0"))
                    dyn = Dynamics(damping, friction)

            pose = parse_pose_text(j.findtext('pose', default="0 0 0 0 0 0"))
            joints[joint_name] = Joint(joint_name, parent, child, joint_type, axis, pose, limit, dyn)


    return Model(model_name, links, joints)

def load_meshes_for_model(model: Model, MESH_PATH):
    """Load all unique meshes for the model from MESH_PATH (consider all visuals)."""
    mesh_dict = {}
    cube_mesh  = ue.load_asset("/Engine/BasicShapes/Cube")
    for link in model.links.values():
        for visual in (link.visuals or []):
            if not (visual and visual.geometry and visual.geometry.mesh):
                continue
            mesh_name = visual.geometry.mesh.mesh_name
            if mesh_name in mesh_dict:
                continue
            full_path = f"{MESH_PATH}/{mesh_name}.{mesh_name}"
            mesh_asset = ue.load_asset(full_path)
            if mesh_asset and isinstance(mesh_asset, ue.StaticMesh):
                mesh_dict[mesh_name] = mesh_asset
            else:
                print(f"Warn: Mesh not found or invalid: {full_path}")
                mesh_dict[mesh_name] = cube_mesh  # Fallback to cube
    return mesh_dict


# --- Rotation / Pose utilities for correct composition ---
def rpy_to_matrix(r, p, y):
    cr, sr = math.cos(r), math.sin(r)
    cp, sp = math.cos(p), math.sin(p)
    cy, sy = math.cos(y), math.sin(y)
    # ZYX order: R = Rz(yaw) * Ry(pitch) * Rx(roll)
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    Ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    return Rz @ Ry @ Rx

def matrix_to_rpy(R):
    # Inverse of ZYX decomposition
    sy = math.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
    singular = sy < 1e-6
    if not singular:
        roll = math.atan2(R[2, 1], R[2, 2])
        pitch = math.atan2(-R[2, 0], sy)
        yaw = math.atan2(R[1, 0], R[0, 0])
    else:
        roll = math.atan2(-R[1, 2], R[1, 1])
        pitch = math.atan2(-R[2, 0], sy)
        yaw = 0.0
    return roll, pitch, yaw

def compose_pose(parent_pose, child_pose):
    px, py, pz, pr, pp, pyaw = parent_pose
    cx, cy, cz, cr, cp, cyaw = child_pose
    Rp = rpy_to_matrix(pr, pp, pyaw)
    Rc = rpy_to_matrix(cr, cp, cyaw)
    R = Rp @ Rc
    t = np.array([px, py, pz]) + Rp @ np.array([cx, cy, cz])
    r, p, y = matrix_to_rpy(R)
    return t[0], t[1], t[2], r, p, y


def sdf_to_unreal(r, p, y):
    # Use the original conversion (this was already correct):
    # roll -> degrees, pitch -> -degrees, yaw -> -degrees
    r_u = math.degrees(r)
    p_u = -math.degrees(p)
    y_u = -math.degrees(y)
    return p_u, y_u, r_u

def vec_gz_to_loc_ue(x, y, z):
    # meters -> centimeters and Y flip
    return ue.Vector(x*SI_TO_UE, -y*SI_TO_UE, z*SI_TO_UE)

def get_link_pose(link: Link):
    #combine link pose and first visual pose if exists
    x, y, z, roll, pitch, yaw = link.pose
    if link.visuals:
        vx, vy, vz, vroll, vpitch, vyaw = link.visuals[0].pose
        x += vx
        y += vy
        z += vz
        roll += vroll
        pitch += vpitch
        yaw += vyaw
    return x, y, z, roll, pitch, yaw

def world_pose_of_joint_childed(model: Model, joint: Joint):
    """Joint <pose> parent link frame'inde varsayımıyla dünya pozunu döndürür."""
    child_link = model.links.get(joint.child)
    if child_link is None:
        return (0,0,0,0,0,0)
    return compose_pose(child_link.pose, joint.pose)


# ---------- MAIN EXECUTION FUNCTION ----------
def run(sdf_path_arg=None, dest_pkg_arg="/Game/PlantLib",analyze_only=False):
    # ---------- SETTINGS ----------
    # Eğer dışarıdan argüman gelmezse (örneğin test için) varsayılan bir yol kullanabilirsin
    # Ama Widget'tan gönderdiğimizde sdf_path_arg dolu gelecek.
    
    if sdf_path_arg:
        SDF_PATH = sdf_path_arg
    else:
        # Fallback (Eski hardcoded yolun)
        SDF_PATH = r"/home/veli/btp_ws/Plant2SimDynamics-main/str_dyn_gen/models_out/test_model_small/model.sdf"

    DEST_PKG = dest_pkg_arg
    MESH_PATH = f"{DEST_PKG}/MeshLib" # Mesh path'i de dinamik yapıyoruz

    ue.log(f"Importing SDF from: {SDF_PATH}")
    ue.log(f"Destination Package: {DEST_PKG}")

    # ---------- READ SDF (Buradan sonrası senin orijinal kodunla aynı) ----------
    model = parse_sdf(SDF_PATH)
    # ... (Kodun geri kalanı tamamen aynı devam edecek) ...
    if analyze_only:
        register_path = ue.Paths.project_saved_dir()
        log_name = "python_temp_result.txt"
        tam_yol = os.path.join(register_path, log_name)
        with open(tam_yol, 'w') as f:
            f.write(report(model))
        return True

    # load assets
    cube_mesh  = ue.load_asset("/Engine/BasicShapes/Cube")
    mesh_assets = load_meshes_for_model(model, MESH_PATH)

    # ---------- PROCESS MODEL DATA ----------
    model_name = model.name
    link_names = list(model.links.keys())
    root_link = link_names[0] if link_names else None


    # ---------- CLEAN OLD BP ----------
    existing_bp_path = f"{DEST_PKG}/{model.name}"
    if ue.EditorAssetLibrary.does_asset_exist(existing_bp_path):
        print(f"Deleting existing: {existing_bp_path}")
        ue.EditorAssetLibrary.delete_asset(existing_bp_path)

    # ---------- CREATE BP ----------
    factory = ue.BlueprintFactory()
    factory.set_editor_property("parent_class", ue.Actor)
    bp = ue.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name=model.name, package_path=DEST_PKG, asset_class=ue.Blueprint, factory=factory
    )
    print("BP oluşturuldu:", bp)

    # ---------- SUBOBJECT API ----------
    subsys = ue.get_engine_subsystem(ue.SubobjectDataSubsystem)
    BFL = ue.SubobjectDataBlueprintFunctionLibrary
    def h2o(h): return BFL.get_object(BFL.get_data(h))

    handles = subsys.k2_gather_subobject_data_for_blueprint(bp)
    if not handles:
        raise RuntimeError("Subobject handles alınamadı.")

    root_handle = next((h for h in handles if h2o(h) and h2o(h).get_name()=="DefaultSceneRoot"), handles[0])

    # Anchor scene
    sc_params = ue.AddNewSubobjectParams(
        parent_handle=root_handle,
        new_class=ue.SceneComponent,
        blueprint_context=bp
    )
    scene_handle, fail = subsys.add_new_subobject(sc_params)
    if not fail.is_empty():
        raise RuntimeError(f"SceneComponent eklenemedi: {fail}")
    subsys.attach_subobject(root_handle, scene_handle)
    scene = h2o(scene_handle)
    try:
        scene.rename(f"Scene_{model_name}")
    except Exception as e:
        print(f"Warn: scene rename: {e}")
    scene.set_editor_property("mobility", ue.ComponentMobility.MOVABLE)
    
    # Internal helper for SM inside run()
    def add_sm_internal(link: Link):
        # Create a StaticMeshComponent for each visual that has a mesh.
        components = []

        if link.visuals:
            for idx, visual in enumerate(link.visuals):
                if not (visual and visual.geometry and visual.geometry.mesh):
                    continue
                params = ue.AddNewSubobjectParams(
                    parent_handle=scene_handle,
                    new_class=ue.StaticMeshComponent,
                    blueprint_context=bp,
                )
                sm_handle, f = subsys.add_new_subobject(params)
                if not f.is_empty():
                    raise RuntimeError(f"SM add failed for {link.name}: {f}")
                subsys.attach_subobject(scene_handle, sm_handle)

                new_name = f"{link.name}"
                # Unreal isim sınırlamalarına karşı güvenli hale getir (boşluk vs.)
                new_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in new_name)
                try:
                    subsys.rename_subobject(sm_handle, new_name)
                except Exception as e:
                    print(f"Warn: SCS rename {link.name} v{idx}: {e}")

                sm = h2o(sm_handle)

                mesh_asset = mesh_assets.get(visual.geometry.mesh.mesh_name, cube_mesh)
                sm.set_static_mesh(mesh_asset)
                sm.set_editor_property("mobility", ue.ComponentMobility.MOVABLE)

                if visual.geometry.mesh.scale:
                    sm.set_editor_property("relative_scale3d", ue.Vector(*visual.geometry.mesh.scale))
                components.append(sm)

            if components:
                return components

        # Fallback: no visuals with meshes; create a single anchor SM (cube), sizing root as before.
        params = ue.AddNewSubobjectParams(
            parent_handle=scene_handle,
            new_class=ue.StaticMeshComponent,
            blueprint_context=bp,
        )
        sm_handle, f = subsys.add_new_subobject(params)
        if not f.is_empty():
            raise RuntimeError(f"SM add failed for {link.name}: {f}")
        subsys.attach_subobject(scene_handle, sm_handle)

        sm = h2o(sm_handle)
        
        new_name = f"{link.name}"
        # Unreal isim sınırlamalarına karşı güvenli hale getir (boşluk vs.)
        new_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in new_name)
        try:
            subsys.rename_subobject(sm_handle, new_name)
        except Exception as e:
            print(f"Warn: SCS rename fallback {link.name}: {e}")

        sm.set_static_mesh(cube_mesh)
        if link.name == root_link:
            # set box size to 20x20x40 for root as before
            sm.set_editor_property("relative_scale3d", ue.Vector(0.2, 0.4, 0.4))
        sm.set_editor_property("mobility", ue.ComponentMobility.MOVABLE)
        return [sm]


    # ---------- CREATE COMPONENT PER LINK ----------
    link_main_sm = {}  # <--- EKLENDİ: her link için ilk SM referansı

    for link in model.links.values():
        sms = add_sm_internal(link)

        if link.visuals and sms:
            for i, sm in enumerate(sms):
                if i < len(link.visuals):
                    x, y, z, roll, pitch, yaw = compose_pose(link.pose, link.visuals[i].pose)
                else:
                    x, y, z, roll, pitch, yaw = link.pose

                loc = vec_gz_to_loc_ue(x, y, z)
                rot = sdf_to_unreal(roll, pitch, yaw)

                sm.set_editor_property("relative_location", loc)
                sm.set_editor_property("relative_rotation", rot)


                
                # Create body instance to set iteration counts
                bi = ue.BodyInstance()
                bi.set_editor_property("position_solver_iteration_count", 255)
                bi.set_editor_property("velocity_solver_iteration_count", 255)
                sm.set_editor_property("body_instance", bi)

                # set enable physics with parsed mass from SDF
                sm.set_editor_property("mobility", ue.ComponentMobility.MOVABLE)
                if len(link.name) == 3 and link.name.endswith("1"):
                    sm.set_simulate_physics(False)
                else:
                    sm.set_simulate_physics(True)
                sm.set_enable_gravity(True)
                
                # Use mass from SDF inertial data
                # mass_kg = link.inertial.mass if link.inertial.mass > 0 else 0.1
                sm.set_mass_override_in_kg("", link.inertial.mass * 1000, True)

                # Optional: Set damping based on inertial properties
                sm.set_linear_damping(0.1)
                sm.set_angular_damping(0.1)

                if link.name == "link_0":
                    sm.set_simulate_physics(False)

            # ilk SM'i ana bileşen olarak kaydet
            if sms:
                link_main_sm[link.name] = sms[0]   # <--- EKLENDİ
        else:
            x, y, z, roll, pitch, yaw = link.pose
            loc = vec_gz_to_loc_ue(x, y, z)
            rot = sdf_to_unreal(roll, pitch, yaw)
            if sms:
                sms[0].set_editor_property("relative_location", loc)
                sms[0].set_editor_property("relative_rotation", rot)
                

                
                # set iteration counts
                bi = ue.BodyInstance()
                bi.set_editor_property("position_solver_iteration_count", 255)
                bi.set_editor_property("velocity_solver_iteration_count", 255)
                sms[0].set_editor_property("body_instance", bi)

                # Apply physics and mass to fallback component too
                sms[0].set_editor_property("mobility", ue.ComponentMobility.MOVABLE)
                sms[0].set_simulate_physics(True)
                sms[0].set_enable_gravity(True)
                
                # Use mass from SDF inertial data
                sms[0].set_mass_override_in_kg("", link.inertial.mass * 1000, True)

                if link.name == "link_0":
                    sms[0].set_simulate_physics(False)
                
                link_main_sm[link.name] = sms[0]   # <--- EKLENDİ


    # ---------- CREATE JOINTS ----------
    for joint in model.joints.values():
        # Parent ve child SM'leri bul
        parent_sm = link_main_sm.get(joint.parent)
        child_sm  = link_main_sm.get(joint.child)
        if not parent_sm or not child_sm:
            print(f"Warn: joint '{joint.name}' için SM bulunamadı (parent={joint.parent}, child={joint.child})")
            continue

        jx, jy, jz, jr, jp, jyaw = world_pose_of_joint_childed(model, joint)

        j_loc = vec_gz_to_loc_ue(jx, jy, jz)
        j_rot = sdf_to_unreal(jr, jp, jyaw)

        # PhysicsConstraintComponent ekle ve sahneye ata
        params = ue.AddNewSubobjectParams(
            parent_handle=scene_handle,
            new_class=ue.PhysicsConstraintComponent,
            blueprint_context=bp,
        )
        pc_handle, f = subsys.add_new_subobject(params)
        if not f.is_empty():
            print(f"Warn: Joint '{joint.name}' eklenemedi: {f}")
            continue
        subsys.attach_subobject(scene_handle, pc_handle)

        pc = h2o(pc_handle)

        cpp = ue.ConstraintProfileProperties()
        cpp.set_editor_property("enable_projection", False)
        ci = ue.ConstraintInstance()
        ci.set_editor_property("profile_instance", cpp)
        pc.set_editor_property("constraint_instance", ci)

        new_name = f"{joint.name}"
        # Unreal isim sınırlamalarına karşı güvenli hale getir (boşluk vs.)
        new_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in new_name)
        try:
            subsys.rename_subobject(pc_handle, new_name)
        except Exception as e:
            print(f"Warn: Joint SCS rename {joint.name}: {e}")

        pc.set_editor_property("mobility", ue.ComponentMobility.MOVABLE)
        pc.set_editor_property("relative_location", j_loc)
        pc.set_editor_property("relative_rotation", j_rot)
        

        # Set constraint components - use direct component references
        constraint_name1 = ue.ConstrainComponentPropName()
        constraint_name1.set_editor_property("component_name", joint.child)
        pc.set_editor_property("component_name1", constraint_name1)
        
        constraint_name2 = ue.ConstrainComponentPropName()
        constraint_name2.set_editor_property("component_name", joint.parent)
        pc.set_editor_property("component_name2", constraint_name2)


        pc.set_angular_swing1_limit(ue.AngularConstraintMotion.ACM_LOCKED, 0.1)
        pc.set_angular_swing2_limit(ue.AngularConstraintMotion.ACM_FREE, 0.1)
        pc.set_angular_twist_limit(ue.AngularConstraintMotion.ACM_LOCKED, 0.1)

        pc.set_linear_x_limit(ue.LinearConstraintMotion.LCM_LOCKED, 0.0)
        pc.set_linear_y_limit(ue.LinearConstraintMotion.LCM_LOCKED, 0.0)
        pc.set_linear_z_limit(ue.LinearConstraintMotion.LCM_LOCKED, 0.0)

        pc.set_angular_drive_mode(ue.AngularDriveMode.TWIST_AND_SWING)
        pc.set_orientation_drive_twist_and_swing(True,True)
        pc.set_angular_velocity_drive_twist_and_swing(True,True)
        pc.set_angular_drive_params(100000.0, 100.0, 0.0)


        pc.set_disable_collision(True)

    # ---------- COMPILE & OPEN ----------
    ue.BlueprintEditorLibrary.compile_blueprint(bp)
    ue.EditorAssetLibrary.save_loaded_asset(bp)
    bp_asset = ue.EditorAssetLibrary.load_asset(f"{DEST_PKG}/{model_name}")
    ue.get_editor_subsystem(ue.AssetEditorSubsystem).open_editor_for_assets([bp_asset])

    # ... (Mevcut kodların aynen kalsın, dosyanın EN ALTINA şunu ekle) ...

    print(f"Done.")