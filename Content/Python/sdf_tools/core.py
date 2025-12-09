import unreal as ue
import os
from . import schema
from . import utils
from . import parser

def load_meshes_for_model(model: schema.Model, MESH_PATH):
    """
    Modeldeki mesh isimlerini bulur, Unreal Asset'i olarak YÜKLER ve bir sözlük döndürür.
    Dönen sözlük: { 'mesh_ismi': ue.StaticMeshObject }
    """
    mesh_dict = {}
    
    # Küpü baştan obje olarak yükle
    cube_mesh = ue.load_asset("/Engine/BasicShapes/Cube")
    
    for link in model.links.values():
        if not link.visuals: continue
        
        for visual in link.visuals:
            if not (visual and visual.geometry and visual.geometry.mesh):
                continue
            
            mesh_name = visual.geometry.mesh.mesh_name
            if mesh_name in mesh_dict:
                continue
            
            # Tam Asset Yolu: /Game/PlantLib/MeshLib/MeshAdi.MeshAdi
            full_path = f"{MESH_PATH}/{mesh_name}.{mesh_name}"
            
            if ue.EditorAssetLibrary.does_asset_exist(full_path):
                loaded_mesh = ue.load_asset(full_path)
                if loaded_mesh:
                    mesh_dict[mesh_name] = loaded_mesh
                else:
                    ue.log_warning(f"Asset var ama yuklenemedi: {full_path}")
                    mesh_dict[mesh_name] = cube_mesh
            else:
                ue.log_warning(f"Asset bulunamadi: {full_path}")
                mesh_dict[mesh_name] = cube_mesh
                
    return mesh_dict

def run(sdf_path_arg=None, dest_pkg_arg="/Game/PlantLib", analyze_only=False):
    # --- AYARLAR ---
    if sdf_path_arg:
        SDF_PATH = sdf_path_arg
    else:
        # Test yolu
        SDF_PATH = r"/home/veli/btp_ws/Plant2SimDynamics-main/str_dyn_gen/models_out/test_model_small/model.sdf"

    DEST_PKG = dest_pkg_arg
    MESH_PATH = f"{DEST_PKG}/MeshLib"

    ue.log(f"Importing SDF from: {SDF_PATH}")

    # --- PARSING ---
    model = parser.parse_sdf(SDF_PATH)
    if not model:
        ue.log_error("SDF Parsing Failed!")
        return False

    # --- ANALYZE ONLY ---
    if analyze_only:
        register_path = ue.Paths.project_saved_dir()
        log_name = "python_temp_result.txt"
        tam_yol = os.path.join(register_path, log_name)
        with open(tam_yol, 'w') as f:
            f.write(parser.report(model))
        return True
    
    # --- ASSET LOADING ---
    # Küpü OBJE olarak yükle (String değil!)
    cube_mesh = ue.load_asset("/Engine/BasicShapes/Cube")
    if not cube_mesh:
        ue.log_error("BasicShapes/Cube bulunamadi!")

    # Meshleri yükle (Dictionary of Objects)
    mesh_assets = load_meshes_for_model(model, MESH_PATH)

    # --- PROCESS DATA ---
    model_name = model.name
    link_names = list(model.links.keys())
    root_link = link_names[0] if link_names else None

    # --- CLEAN OLD BP ---
    existing_bp_path = f"{DEST_PKG}/{model.name}"
    if ue.EditorAssetLibrary.does_asset_exist(existing_bp_path):
        ue.EditorAssetLibrary.delete_asset(existing_bp_path)

    # --- CREATE BP ---
    factory = ue.BlueprintFactory()
    factory.set_editor_property("parent_class", ue.Actor)
    bp = ue.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name=model.name, package_path=DEST_PKG, asset_class=ue.Blueprint, factory=factory
    )
    ue.log(f"BP Olusturuldu: {bp}")

    # --- SUBOBJECT API ---
    subsys = ue.get_engine_subsystem(ue.SubobjectDataSubsystem)
    BFL = ue.SubobjectDataBlueprintFunctionLibrary
    def h2o(h): return BFL.get_object(BFL.get_data(h))

    handles = subsys.k2_gather_subobject_data_for_blueprint(bp)
    root_handle = next((h for h in handles if h2o(h) and h2o(h).get_name()=="DefaultSceneRoot"), handles[0])

    # Scene Component
    sc_params = ue.AddNewSubobjectParams(
        parent_handle=root_handle, new_class=ue.SceneComponent, blueprint_context=bp
    )
    scene_handle, fail = subsys.add_new_subobject(sc_params)
    subsys.attach_subobject(root_handle, scene_handle)
    scene = h2o(scene_handle)
    try: scene.rename(f"Scene_{model_name}")
    except: pass
    scene.set_editor_property("mobility", ue.ComponentMobility.MOVABLE)
    
    # --- ADD SM INTERNAL FUNCTION ---
    def add_sm_internal(link: schema.Link):
        components = []

        if link.visuals:
            for idx, visual in enumerate(link.visuals):
                if not (visual and visual.geometry and visual.geometry.mesh):
                    continue
                
                params = ue.AddNewSubobjectParams(
                    parent_handle=scene_handle, new_class=ue.StaticMeshComponent, blueprint_context=bp
                )
                sm_handle, f = subsys.add_new_subobject(params)
                if not f.is_empty(): continue
                
                subsys.attach_subobject(scene_handle, sm_handle)

                # Rename
                new_name = f"{link.name}"
                new_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in new_name)
                try: subsys.rename_subobject(sm_handle, new_name)
                except: pass

                sm = h2o(sm_handle)

                # Assign Mesh (Dictionary'den Obje al)
                mesh_name = visual.geometry.mesh.mesh_name
                target_mesh = mesh_assets.get(mesh_name, cube_mesh) # Fallback to cube object
                
                sm.set_static_mesh(target_mesh)
                sm.set_editor_property("mobility", ue.ComponentMobility.MOVABLE)

                if visual.geometry.mesh.scale:
                    sm.set_editor_property("relative_scale3d", ue.Vector(*visual.geometry.mesh.scale))
                components.append(sm)

            if components:
                return components

        # Fallback (Görünmez Linkler için Küp)
        params = ue.AddNewSubobjectParams(
            parent_handle=scene_handle, new_class=ue.StaticMeshComponent, blueprint_context=bp
        )
        sm_handle, f = subsys.add_new_subobject(params)
        subsys.attach_subobject(scene_handle, sm_handle)
        sm = h2o(sm_handle)
        sm.set_static_mesh(cube_mesh)
        
        if link.name == root_link:
             sm.set_editor_property("relative_scale3d", ue.Vector(0.2, 0.4, 0.4))
        
        sm.set_editor_property("mobility", ue.ComponentMobility.MOVABLE)
        return [sm]

    # --- CREATE LINKS ---
    link_main_sm = {}

    for link in model.links.values():
        sms = add_sm_internal(link)
        if not sms: continue
        
        # İlk mesh'i ana fizik gövdesi yap
        main_sm = sms[0]
        link_main_sm[link.name] = main_sm

        # Pozisyonlama
        if link.visuals:
             x, y, z, roll, pitch, yaw = utils.compose_pose(link.pose, link.visuals[0].pose)
        else:
             x, y, z, roll, pitch, yaw = link.pose

        loc = utils.vec_gz_to_loc_ue(x, y, z)
        rot = utils.sdf_to_unreal(roll, pitch, yaw)
        main_sm.set_editor_property("relative_location", loc)
        main_sm.set_editor_property("relative_rotation", rot)

        # Fizik
        bi = ue.BodyInstance()
        bi.set_editor_property("position_solver_iteration_count", 255)
        bi.set_editor_property("velocity_solver_iteration_count", 255)
        main_sm.set_editor_property("body_instance", bi)

        main_sm.set_simulate_physics(True)
        main_sm.set_enable_gravity(True)
        main_sm.set_mass_override_in_kg("", link.inertial.mass * 1000, True)

        if link.name == "link_0" or (len(link.name) == 3 and link.name.endswith("1")):
            main_sm.set_simulate_physics(False)

    # --- CREATE JOINTS ---
    for joint in model.joints.values():
        parent_sm = link_main_sm.get(joint.parent)
        child_sm  = link_main_sm.get(joint.child)
        if not parent_sm or not child_sm:
            ue.log_warning(f"Joint '{joint.name}' icin Parent veya Child Link bulunamadi!")
            continue

        jx, jy, jz, jr, jp, jyaw = utils.world_pose_of_joint_childed(model, joint)
        j_loc = utils.vec_gz_to_loc_ue(jx, jy, jz)
        j_rot = utils.sdf_to_unreal(jr, jp, jyaw)

        params = ue.AddNewSubobjectParams(
            parent_handle=scene_handle, new_class=ue.PhysicsConstraintComponent, blueprint_context=bp
        )
        pc_handle, f = subsys.add_new_subobject(params)
        if not f.is_empty():
            continue
            
        subsys.attach_subobject(scene_handle, pc_handle)

        # 1. EKSİK OLAN KISIM: İsimlendirme (Rename)
        # Bunu yapmazsan Blueprint içinde hangi constraint hangisi anlayamazsın.
        new_name = f"{joint.name}"
        new_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in new_name)
        try:
            subsys.rename_subobject(pc_handle, new_name)
        except Exception as e:
            print(f"Warn: Joint SCS rename {joint.name}: {e}")

        pc = h2o(pc_handle)

        # 2. EKSİK OLAN KISIM: Constraint Instance Ayarları
        cpp = ue.ConstraintProfileProperties()
        cpp.set_editor_property("enable_projection", False)
        ci = ue.ConstraintInstance()
        ci.set_editor_property("profile_instance", cpp)
        pc.set_editor_property("constraint_instance", ci)

        pc.set_editor_property("mobility", ue.ComponentMobility.MOVABLE)
        pc.set_editor_property("relative_location", j_loc)
        pc.set_editor_property("relative_rotation", j_rot)

        # Constraint Bağlantıları
        cn1 = ue.ConstrainComponentPropName()
        cn1.set_editor_property("component_name", joint.child) # Unreal Link ismini string olarak bekler
        pc.set_editor_property("component_name1", cn1)
        
        cn2 = ue.ConstrainComponentPropName()
        cn2.set_editor_property("component_name", joint.parent)
        pc.set_editor_property("component_name2", cn2)
        
        # 3. EKSİK OLAN KISIM: Fizik Limitleri (Limits & Drives)
        # Eski kodundaki varsayılan ayarlar (Bitki simülasyonu için özel ayarların)
        pc.set_angular_swing1_limit(ue.AngularConstraintMotion.ACM_LOCKED, 0.1)
        pc.set_angular_swing2_limit(ue.AngularConstraintMotion.ACM_FREE, 0.1)
        pc.set_angular_twist_limit(ue.AngularConstraintMotion.ACM_LOCKED, 0.1)

        pc.set_linear_x_limit(ue.LinearConstraintMotion.LCM_LOCKED, 0.0)
        pc.set_linear_y_limit(ue.LinearConstraintMotion.LCM_LOCKED, 0.0)
        pc.set_linear_z_limit(ue.LinearConstraintMotion.LCM_LOCKED, 0.0)

        # Motor/Drive Ayarları
        pc.set_angular_drive_mode(ue.AngularDriveMode.TWIST_AND_SWING)
        pc.set_orientation_drive_twist_and_swing(True, True)
        pc.set_angular_velocity_drive_twist_and_swing(True, True)
        pc.set_angular_drive_params(100000.0, 100.0, 0.0)

        pc.set_disable_collision(True)

    # --- FINISH ---
    ue.BlueprintEditorLibrary.compile_blueprint(bp)
    ue.EditorAssetLibrary.save_loaded_asset(bp)
    bp_asset = ue.EditorAssetLibrary.load_asset(f"{DEST_PKG}/{model_name}")
    # ue.get_editor_subsystem(ue.AssetEditorSubsystem).open_editor_for_assets([bp_asset])

    ue.log("SDF Import Completed.")