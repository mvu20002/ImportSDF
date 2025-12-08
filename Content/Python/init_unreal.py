import unreal

@unreal.uclass()
class SDFImporterCommand(unreal.ToolMenuEntryScript):
    @unreal.ufunction(override=True)
    def execute(self, context):
        # 1. Widget'ın yolunu belirle
        widget_path = "/Import_SDF/EUW_SDFImporter"
        
        # 2. Asset'i yükle
        if not unreal.EditorAssetLibrary.does_asset_exist(widget_path):
            unreal.log_warning(f"SDF Importer Widget bulunamadı: {widget_path}")
            return

        widget_asset = unreal.EditorAssetLibrary.load_asset(widget_path)
        
        # 3. Widget'ı aç
        subsystem = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
        subsystem.spawn_and_register_tab(widget_asset)

def add_sdf_toolbar_button():
    menus = unreal.ToolMenus.get()
    
    # --- 1. TOOLBAR (Play Butonunun Yanı) ---
    # Toolbar menüsünü bul
    toolbar = menus.find_menu("LevelEditor.LevelEditorToolBar.AssetsToolBar")
    if not toolbar:
        print("Toolbar bulunamadi")
        return

    # Toolbar için giriş oluştur
    entry = SDFImporterCommand()
    entry.init_entry(
        owner_name="Import_SDF_Plugin",
        menu="LevelEditor.LevelEditorToolBar",
        section="File", # "Settings" veya "Content" yanına ekler
        name="SDFToolbarButton",
        label="SDF Import",
        tool_tip="SDF Importer Aracını Açar"
    )
    
    # İkon Ayarı (Unreal'ın yerleşik ikonlarından birini kullanalım)
    # "SDFStyle" bizim özel stil setimiz. "SDFIcon" ise içe aktarma ikonumuz.
    entry.data.icon = unreal.ScriptSlateIcon("SDFStyle", "SDFIcon")
    
    # Butonu Toolbar'a ekle
    toolbar.add_menu_entry_object(entry)


    # --- 2. ANA MENÜ (Tools Altı - Opsiyonel, istersen kalabilir) ---
    main_menu = menus.find_menu("LevelEditor.MainMenu.Tools")
    if main_menu:
        menu_entry = SDFImporterCommand()
        menu_entry.init_entry(
            owner_name="Import_SDF_Plugin",
            menu="LevelEditor.MainMenu.Tools",
            section="Tools",
            name="SDFMenuButton",
            label="SDF Importer",
            tool_tip="SDF Importer Aracını Açar"
        )
        main_menu.add_menu_entry_object(menu_entry)

    # Menüleri yenile
    menus.refresh_all_widgets()

# Kodu çalıştır
add_sdf_toolbar_button()