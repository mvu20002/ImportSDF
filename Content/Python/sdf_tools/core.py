import unreal as ue
import os
from . import schema
from . import utils
from . import parser

def load_meshes_for_model(model: schema.Model, ASSET_PKG_PATH):
    mesh_dict = {}
    cube_mesh = ue.load_asset("/Engine/BasicShapes/Cube")
    
    uri_cache = {} 

    temp_import_dir = os.path.join(ue.Paths.project_saved_dir(), "TempImportFBX")
    if not os.path.exists(temp_import_dir):
        os.makedirs(temp_import_dir)

    total_links = len(model.links)
    
    with ue.ScopedSlowTask(total_links, "Models processing..") as slow_task:
        slow_task.make_dialog(True)
        
        for link in model.links.values():
            if slow_task.should_cancel(): break
            slow_task.enter_progress_frame(1, f"Link: {link.name}")

            if not link.visuals: continue
            
            for visual in link.visuals:
                if not (visual and visual.geometry and visual.geometry.mesh):
                    continue
                
                uri = visual.geometry.mesh.uri
                if uri.startswith("file://"): uri = uri.replace("file://", "")
                
                mesh_name = visual.geometry.mesh.mesh_name
                
                if uri in uri_cache:
                    mesh_dict[mesh_name] = uri_cache[uri]
                    continue
                
                # --- CONVERSION ---
                fbx_disk_path = None
                if uri.endswith(".dae"):
                    slow_task.enter_progress_frame(0, f"Blender: {os.path.basename(uri)}")
                    fbx_disk_path = utils.convert_dae_to_fbx(uri, temp_import_dir)
                elif uri.endswith(".fbx"):
                    fbx_disk_path = uri

                if not fbx_disk_path or not os.path.exists(fbx_disk_path):
                    mesh_dict[mesh_name] = cube_mesh
                    uri_cache[uri] = cube_mesh 
                    continue

                # --- IMPORT ---
                destination_name = mesh_name
                asset_path = f"{ASSET_PKG_PATH}/{destination_name}.{destination_name}"

                if ue.EditorAssetLibrary.does_asset_exist(asset_path):
                    loaded_asset = ue.load_asset(asset_path)
                    mesh_dict[mesh_name] = loaded_asset
                    uri_cache[uri] = loaded_asset 
                    continue

                task = ue.AssetImportTask()
                task.set_editor_property("filename", fbx_disk_path)
                task.set_editor_property("destination_path", ASSET_PKG_PATH)
                task.set_editor_property("destination_name", destination_name)
                task.set_editor_property("replace_existing", True)
                task.set_editor_property("automated", True)
                task.set_editor_property("save", True)

                options = ue.FbxImportUI()
                options.set_editor_property("import_mesh", True)
                options.set_editor_property("import_textures", True)
                options.set_editor_property("import_materials", True)
                options.set_editor_property("original_import_type", ue.FBXImportType.FBXIT_STATIC_MESH)

                sm_data = options.static_mesh_import_data
                sm_data.set_editor_property("combine_meshes", True) 
                sm_data.set_editor_property("remove_degenerates", True)
                
                task.set_editor_property("options", options)
                ue.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
                
                if ue.EditorAssetLibrary.does_asset_exist(asset_path):
                    loaded_asset = ue.load_asset(asset_path)
                    mesh_dict[mesh_name] = loaded_asset
                    uri_cache[uri] = loaded_asset
                    ue.log(f"Imported: {mesh_name}")
                else:
                    mesh_dict[mesh_name] = cube_mesh
                    uri_cache[uri] = cube_mesh

    return mesh_dict

def run(sdf_path_arg=None, dest_pkg_arg="/Game/SDF_Imports", analyze_only=False):
    # --- SETTINGS ---
    SDF_PATH = sdf_path_arg if sdf_path_arg else r"/tmp/model.sdf"
    
    ue.log(f"Importing SDF: {SDF_PATH}")

    # --- PARSING ---
    model = parser.parse_sdf(SDF_PATH)
    if not model:
        ue.log_error("SDF Parsing Failed!")
        return False

    if analyze_only:
        register_path = ue.Paths.project_saved_dir()
        log_name = "python_temp_result.txt"
        tam_yol = os.path.join(register_path, log_name)
        with open(tam_yol, 'w') as f: f.write(parser.report(model))
        return True

    # Create target package paths
    MODEL_PKG_PATH = f"{dest_pkg_arg}/{model.name}"
    ASSET_PKG_PATH = f"{MODEL_PKG_PATH}/Assets"

    ue.log(f"Target Model Path: {MODEL_PKG_PATH}")
    ue.log(f"Target Assets Path: {ASSET_PKG_PATH}")

    # --- ASSET IMPORTING ---
    shape_cube = ue.load_asset("/Engine/BasicShapes/Cube")
    shape_sphere = ue.load_asset("/Engine/BasicShapes/Sphere")
    shape_cylinder = ue.load_asset("/Engine/BasicShapes/Cylinder")
    
    # Import meshes and get a dictionary
    mesh_assets = load_meshes_for_model(model, ASSET_PKG_PATH)

    # --- BLUEPRINT CREATION ---
    model_name = model.name
    
    # If BP already exists, delete it first
    bp_asset_path = f"{MODEL_PKG_PATH}/{model_name}"
    if ue.EditorAssetLibrary.does_asset_exist(bp_asset_path):
        ue.EditorAssetLibrary.delete_asset(bp_asset_path)

    factory = ue.BlueprintFactory()
    factory.set_editor_property("parent_class", ue.Actor)

    # Create the BP inside the Model Folder
    bp = ue.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name=model.name, 
        package_path=MODEL_PKG_PATH, 
        asset_class=ue.Blueprint, 
        factory=factory
    )
    
    if not bp:
        ue.log_error("BP Creation Failed!")
        return

    # --- SUBOBJECT API ---
    subsys = ue.get_engine_subsystem(ue.SubobjectDataSubsystem)
    BFL = ue.SubobjectDataBlueprintFunctionLibrary
    def h2o(h): return BFL.get_object(BFL.get_data(h))

    handles = subsys.k2_gather_subobject_data_for_blueprint(bp)
    root_handle = next((h for h in handles if h2o(h) and h2o(h).get_name()=="DefaultSceneRoot"), handles[0])

    sc_params = ue.AddNewSubobjectParams(parent_handle=root_handle, new_class=ue.SceneComponent, blueprint_context=bp)
    scene_handle, _ = subsys.add_new_subobject(sc_params)
    subsys.attach_subobject(root_handle, scene_handle)
    scene = h2o(scene_handle)
    try: scene.rename(f"Scene_{model_name}")
    except: pass
    scene.set_editor_property("mobility", ue.ComponentMobility.MOVABLE)
    
    def add_sm_internal(link: schema.Link):
        components = []

        if link.visuals:
            for idx, visual in enumerate(link.visuals):
                if not (visual and visual.geometry): 
                    continue
                
                params = ue.AddNewSubobjectParams(parent_handle=scene_handle, new_class=ue.StaticMeshComponent, blueprint_context=bp)
                sm_handle, f = subsys.add_new_subobject(params)
                if not f.is_empty(): continue
                subsys.attach_subobject(scene_handle, sm_handle)

                new_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in f"{link.name}")
                try: subsys.rename_subobject(sm_handle, new_name)
                except: pass

                sm = h2o(sm_handle)
                geom = visual.geometry
                
                target_mesh = None
                target_scale = ue.Vector(1, 1, 1)

                # --- MESH CHECK ---
                if geom.mesh:
                    # Try to find it in the mesh dictionary, otherwise use the cube
                    target_mesh = mesh_assets.get(geom.mesh.mesh_name, shape_cube)
                    if geom.mesh.scale:
                        target_scale = ue.Vector(*geom.mesh.scale)

                # --- BOX CHECK ---
                elif geom.box:
                    target_mesh = shape_cube
                    # SDF size (metre) -> Unreal Scale (1.0 = 1m = 100cm)
                    if geom.box.size:
                        target_scale = ue.Vector(*geom.box.size)

                # --- SPHERE CHECK ---
                elif geom.sphere:
                    target_mesh = shape_sphere
                    # Radius -> Scale 
                    if geom.sphere.radius:
                        d = geom.sphere.radius * 2.0
                        target_scale = ue.Vector(d, d, d)

                # --- CYLINDER CHECK ---
                elif geom.cylinder:
                    target_mesh = shape_cylinder
                    if geom.cylinder.radius and geom.cylinder.length:
                        d = geom.cylinder.radius * 2.0
                        l = geom.cylinder.length
                        target_scale = ue.Vector(d, d, l)

                # --- SETTING MESH & PROPERTIES ---
                if target_mesh:
                    sm.set_static_mesh(target_mesh)
                    sm.set_editor_property("relative_scale3d", target_scale)
                else:
                    sm.set_static_mesh(shape_cube)
                    sm.set_editor_property("relative_scale3d", ue.Vector(0.1, 0.1, 0.1))
                
                sm.set_editor_property("mobility", ue.ComponentMobility.MOVABLE)

                components.append(sm)

            if components: return components

        # --- FALLBACK CUBE ---
        params = ue.AddNewSubobjectParams(parent_handle=scene_handle, new_class=ue.StaticMeshComponent, blueprint_context=bp)
        sm_handle, _ = subsys.add_new_subobject(params)
        subsys.attach_subobject(scene_handle, sm_handle)
        sm = h2o(sm_handle)
        sm.set_static_mesh(shape_cube)
        sm.set_editor_property("relative_scale3d", ue.Vector(0.1, 0.1, 0.1))
        sm.set_editor_property("mobility", ue.ComponentMobility.MOVABLE)
        return [sm]

    link_main_sm = {}
    for link in model.links.values():
        sms = add_sm_internal(link)
        if not sms: continue
        main_sm = sms[0]
        link_main_sm[link.name] = main_sm

        if link.visuals: x, y, z, roll, pitch, yaw = utils.compose_pose(link.pose, link.visuals[0].pose)
        else: x, y, z, roll, pitch, yaw = link.pose

        main_sm.set_editor_property("relative_location", utils.vec_gz_to_loc_ue(x, y, z))
        main_sm.set_editor_property("relative_rotation", utils.sdf_to_unreal(roll, pitch, yaw))

        bi = ue.BodyInstance()
        bi.set_editor_property("position_solver_iteration_count", 255)
        bi.set_editor_property("velocity_solver_iteration_count", 255)
        main_sm.set_editor_property("body_instance", bi)
        main_sm.set_simulate_physics(True)
        main_sm.set_enable_gravity(True)
        main_sm.set_mass_override_in_kg("", link.inertial.mass * 1000, True)
        if link.name == "link_0" or (len(link.name) == 3 and link.name.endswith("1")):
            main_sm.set_simulate_physics(False)

    for joint in model.joints.values():
        parent_sm = link_main_sm.get(joint.parent)
        child_sm  = link_main_sm.get(joint.child)
        if not parent_sm or not child_sm: continue

        jx, jy, jz, jr, jp, jyaw = utils.world_pose_of_joint_childed(model, joint)
        params = ue.AddNewSubobjectParams(parent_handle=scene_handle, new_class=ue.PhysicsConstraintComponent, blueprint_context=bp)
        pc_handle, _ = subsys.add_new_subobject(params)
        subsys.attach_subobject(scene_handle, pc_handle)
        
        new_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in f"{joint.name}")
        try: subsys.rename_subobject(pc_handle, new_name)
        except: pass
        
        pc = h2o(pc_handle)
        pc.set_editor_property("mobility", ue.ComponentMobility.MOVABLE)
        pc.set_editor_property("relative_location", utils.vec_gz_to_loc_ue(jx, jy, jz))
        pc.set_editor_property("relative_rotation", utils.sdf_to_unreal(jr, jp, jyaw))
        
        cn1 = ue.ConstrainComponentPropName()
        cn1.set_editor_property("component_name", joint.child)
        pc.set_editor_property("component_name1", cn1)
        cn2 = ue.ConstrainComponentPropName()
        cn2.set_editor_property("component_name", joint.parent)
        pc.set_editor_property("component_name2", cn2)
        
        pc.set_disable_collision(True)
        pc.set_angular_swing1_limit(ue.AngularConstraintMotion.ACM_LOCKED, 0.1)
        pc.set_angular_swing2_limit(ue.AngularConstraintMotion.ACM_FREE, 0.1)
        pc.set_angular_twist_limit(ue.AngularConstraintMotion.ACM_LOCKED, 0.1)
        pc.set_linear_x_limit(ue.LinearConstraintMotion.LCM_LOCKED, 0.0)
        pc.set_linear_y_limit(ue.LinearConstraintMotion.LCM_LOCKED, 0.0)
        pc.set_linear_z_limit(ue.LinearConstraintMotion.LCM_LOCKED, 0.0)
        pc.set_angular_drive_mode(ue.AngularDriveMode.TWIST_AND_SWING)
        pc.set_orientation_drive_twist_and_swing(True, True)
        pc.set_angular_velocity_drive_twist_and_swing(True, True)
        pc.set_angular_drive_params(100000.0, 100.0, 0.0)

    ue.BlueprintEditorLibrary.compile_blueprint(bp)
    ue.EditorAssetLibrary.save_loaded_asset(bp)
    
    ue.log("SDF Import Completed.")