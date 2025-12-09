# sdf_tools/utils.py
import subprocess
import os
import math
import numpy as np
import unreal as ue 
from . import schema

SI_TO_UE = 100.0  # m -> cm
BLENDER_EXE = "/home/veli/Documents/blender-4.5.5-linux-x64/blender" 

def convert_dae_to_fbx(dae_path, output_folder):
    if not os.path.exists(dae_path):
        print(f"Error: DAE file not found: {dae_path}")
        return None

    file_name = os.path.basename(dae_path)
    base_name = os.path.splitext(file_name)[0]
    fbx_name = f"{base_name}.fbx"
    fbx_path = os.path.join(output_folder, fbx_name)

    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blender_convert.py")

    # Check if the script file exists
    if not os.path.exists(script_path):
        print(f"Error: Helper script not found at {script_path}")
        return None

    cmd = [
        BLENDER_EXE,
        "-b",
        "-P", script_path,
        "--",
        dae_path,
        fbx_path
    ]

    print(f"Converting DAE to FBX: {file_name}...")

    result = subprocess.run(cmd, text=True, capture_output=True)

    if result.returncode != 0:
        print("--- BLENDER ERROR ---")
        print(result.stdout) 
        print(result.stderr)
        return None
    
    if not os.path.exists(fbx_path):
        print("--- ERROR: Blender finished but FBX file was not created. ---")
        print("Blender Log:")
        print(result.stdout)
        return None

    print("Conversion Done.")
    return fbx_path

def parse_pose_text(text):
    if not text or not text.strip():
        return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    vals = [float(v) for v in text.strip().split()]
    vals += [0.0] * (6 - len(vals))
    return tuple(vals[:6])

def rpy_to_matrix(r, p, y):
    cr, sr = math.cos(r), math.sin(r)
    cp, sp = math.cos(p), math.sin(p)
    cy, sy = math.cos(y), math.sin(y)
    # ZYX order
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    Ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    return Rz @ Ry @ Rx

def matrix_to_rpy(R):
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
    r_u = math.degrees(r)
    p_u = -math.degrees(p)
    y_u = -math.degrees(y)
    return p_u, y_u, r_u

def vec_gz_to_loc_ue(x, y, z):
    return ue.Vector(x*SI_TO_UE, -y*SI_TO_UE, z*SI_TO_UE)

def parse_scale_text(text):
    if not text or not text.strip():
        return (1.0, 1.0, 1.0)
    vals = [float(v) for v in text.strip().split()]
    vals += [1.0] * (3 - len(vals))
    return tuple(vals[:3])

def world_pose_of_joint_childed(model: schema.Model, joint: schema.Joint):
    child_link = model.links.get(joint.child)
    if child_link is None:
        return (0,0,0,0,0,0)
    return compose_pose(child_link.pose, joint.pose)