# sdf_tools/schema.py

class Mesh:
    def __init__(self, mesh_name, uri, scale=(1.0, 1.0, 1.0)):
        self.mesh_name = mesh_name
        self.uri = uri
        self.scale = scale

class Box:
    def __init__(self, size=(1.0, 1.0, 1.0)):
        self.size = size # (x, y, z)

class Cylinder:
    def __init__(self, radius=0.5, length=1.0):
        self.radius = radius
        self.length = length

class Sphere:
    def __init__(self, radius=0.5):
        self.radius = radius

class Geometry:
    # Mesh'in yanına diğerlerini de ekliyoruz (hepsi opsiyonel)
    def __init__(self, mesh: Mesh=None, box: Box=None, cylinder: Cylinder=None, sphere: Sphere=None):
        self.mesh = mesh
        self.box = box
        self.cylinder = cylinder
        self.sphere = sphere

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