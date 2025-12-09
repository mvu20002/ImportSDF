import bpy
import sys
import os

# Çıktıların anında terminale düşmesi için
def log(msg):
    print(msg)
    sys.stdout.flush()

def convert():
    # 1. Argümanları al
    argv = sys.argv
    try:
        if "--" in argv:
            args = argv[argv.index("--") + 1:]
        else:
            args = []
        
        if len(args) < 2:
            log("HATA: Eksik argüman. Kullanım: -- <input_dae> <output_fbx>")
            sys.exit(1)
            
        dae_path = args[0]
        fbx_path = args[1]

    except Exception as e:
        log(f"HATA: Argüman hatası: {e}")
        sys.exit(1)

    # 2. Blender Sahnesini Temizle
    log("Cleaning scene...")
    bpy.ops.wm.read_factory_settings(use_empty=True) # Tamamen boş sahne aç

    # 3. DAE Dosyasını İçe Aktar (Import)
    if not os.path.exists(dae_path):
        log(f"HATA: Dosya bulunamadı -> {dae_path}")
        sys.exit(1)

    log(f"Importing DAE: {dae_path}")
    
    try:
        # Çökme riskini azaltmak için texture aramayı kapatıyoruz (sadece mesh lazım bize)
        # find_chains ve auto_connect bazen karmaşık bitkilerde çökmeye neden olur.
        bpy.ops.wm.collada_import(
            filepath=dae_path, 
            auto_connect=False, 
            find_chains=False, 
            fix_orientation=True
        )
    except Exception as e:
        log(f"HATA: Import sırasında Python hatası: {e}")
        sys.exit(1)

    # Import sonrası obje var mı kontrol et
    if not bpy.context.selected_objects and not bpy.data.objects:
        log("HATA: Import işlemi bitti ama sahnede obje yok!")
        sys.exit(1)

    # 4. FBX Olarak Dışa Aktar (Export)
    log(f"Exporting FBX: {fbx_path}")
    
    try:
        bpy.ops.export_scene.fbx(
            filepath=fbx_path,
            use_selection=False,
            axis_forward='-Z',
            axis_up='Y',
            global_scale=1.0,
            apply_unit_scale=True,
            # Texture/Material hatalarını azaltmak için:
            use_custom_props=False,
            add_leaf_bones=False, 
            bake_anim=False 
        )
    except Exception as e:
        log(f"HATA: FBX Export başarısız: {e}")
        sys.exit(1)

    log("--- CONVERSION SUCCESSFUL ---")

if __name__ == "__main__":
    convert()