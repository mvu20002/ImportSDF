import bpy
import sys
import os

# to ensure immediate output to the terminal
def log(msg):
    print(msg)
    sys.stdout.flush()

def convert():
    # get command line arguments after "--"
    argv = sys.argv
    try:
        if "--" in argv:
            args = argv[argv.index("--") + 1:]
        else:
            args = []
        
        if len(args) < 2:
            log("ERROR: Missing arguments. Usage: blender --background --python blender_convert.py -- <input.dae> <output.fbx>")
            sys.exit(1)
            
        dae_path = args[0]
        fbx_path = args[1]

    except Exception as e:
        log(f"ERROR: Argument error: {e}")
        sys.exit(1)

    # clean the scene
    log("Cleaning scene...")
    bpy.ops.wm.read_factory_settings(use_empty=True) # Tamamen boş sahne aç

    # import DAE file
    if not os.path.exists(dae_path):
        log(f"ERROR: File not found -> {dae_path}")
        sys.exit(1)

    log(f"Importing DAE: {dae_path}")
    
    try:
        # Collada import işlemi
        bpy.ops.wm.collada_import(
            filepath=dae_path, 
            auto_connect=False, 
            find_chains=False, 
            fix_orientation=True
        )
    except Exception as e:
        log(f"ERROR: Python DAE import failed: {e}")
        sys.exit(1)

    # check if any objects were imported
    if not bpy.context.selected_objects and not bpy.data.objects:
        log("ERROR: No objects imported from DAE file.")
        sys.exit(1)

    #    --- YENI EKLENECEK KISIM BASLANGICI ---
    # Materyal isimlerini Mesh ismine göre unique yap
    # Bu sayede Unreal'da "Material", "Material.001" çakışması olmaz.
    input_filename = os.path.splitext(os.path.basename(dae_path))[0]
    
    for mat in bpy.data.materials:
        original_name = mat.name
        # Materyal ismini "DosyaAdi_MateryalAdi" yap
        mat.name = f"{input_filename}_{original_name}"
        log(f"Renamed Material: {original_name} -> {mat.name}")

    # export to FBX
    log(f"Exporting FBX: {fbx_path}")
    
    try:
        bpy.ops.export_scene.fbx(
            filepath=fbx_path,
            use_selection=False,
            axis_forward='-Z',  # Unreal icin standart: -Z Forward
            axis_up='Z',        # Unreal icin standart: Z Up (Blender varsayilani Y'dir ama Z denemek bazen kaymayi duzeltir, oncekini bozma dersen Y kalsin)
            # NOT: Senin onceki ayarin axis_up='Y' idi. Unreal Z-up oldugu icin Blender'in bunu cevirmesi gerekir.
            # Eger model yan yatiyorsa burayi degistiririz. Standart Blender->UE5: Forward:-Z, Up:Y 'dir.
            
            global_scale=1.0,
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_ALL', # Scale sorunlarini cozer
            
            use_custom_props=True,
            add_leaf_bones=False, 
            bake_anim=False,
            
            # --- KRITIK DUZELTMELER ---
            mesh_smooth_type='FACE',  # "No smoothing group" hatasini bu cozer!
            path_mode='COPY',         # Texturelari kopyalar
            embed_textures=True       # Texturelari FBX icine gomer
        )
    except Exception as e:
        log(f"ERROR: FBX export failed: {e}")
        sys.exit(1)

    log("--- CONVERSION SUCCESSFUL ---")

if __name__ == "__main__":
    convert()