#include "Import_SDF.h"
#include "Interfaces/IPluginManager.h"
#include "Styling/SlateStyleRegistry.h"
#include "Widgets/Docking/SDockTab.h"
#include "ImportUI.h" // Kendi widget'ımız
#include "Widgets/Docking/SDockTab.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"
#include "ToolMenus.h" // Menü işlemleri içi

#define LOCTEXT_NAMESPACE "FImport_SDFModule"

static const FName SDFTabName("SDFImportTab");

void FImport_SDFModule::StartupModule()
{
	// // 1. Stil Setini Oluştur (Adı: "SDFStyle")
	// StyleSet = MakeShareable(new FSlateStyleSet("SDFStyle"));

	// // 2. Resources Klasörünü Bul
	// FString BaseDir = IPluginManager::Get().FindPlugin("Import_SDF")->GetBaseDir();
	// StyleSet->SetContentRoot(BaseDir / TEXT("Resources"));

	// // 3. İkonu Tanımla (Adı: "SDFIcon", Dosya: Icon128.png, Boyut: 60x60)
	// // Toolbar ikonları genelde 20x20 veya 40x40 olur.
	// StyleSet->Set("SDFIcon", new FSlateImageBrush(StyleSet->RootToContentDir(TEXT("Icon128.png")), FVector2D(60.0f, 60.0f)));

	// 4. Sisteme Kaydet
	// FSlateStyleRegistry::RegisterSlateStyle(*StyleSet);

	FGlobalTabmanager::Get()->RegisterNomadTabSpawner(SDFTabName, FOnSpawnTab::CreateRaw(this, &FImport_SDFModule::OnSpawnPluginTab))
        .SetDisplayName(FText::FromString(TEXT("SDF Importer Tool")))
        .SetMenuType(ETabSpawnerMenuType::Enabled);

	UToolMenus::RegisterStartupCallback(FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FImport_SDFModule::RegisterMenus));
}

void FImport_SDFModule::ShutdownModule()
{
	// Temizlik
	UToolMenus::UnRegisterStartupCallback(this);
	UToolMenus::UnregisterOwner(this);
	// FImport_SDFStyle::Shutdown();
	FGlobalTabmanager::Get()->UnregisterNomadTabSpawner(SDFTabName);
}

TSharedRef<SDockTab> FImport_SDFModule::OnSpawnPluginTab(const FSpawnTabArgs& SpawnTabArgs)
{
    return SNew(SDockTab)
        .TabRole(ETabRole::NomadTab)
        [
            SNew(ImportUI) // Bizim oluşturduğumuz widget'ı içine koyuyoruz
        ];
}

void FImport_SDFModule::PluginButtonClicked()
{
	// SIHIRLI SATIR BURASI: TabManager'a "Bu isimdeki pencereyi bul ve aç" diyoruz.
	FGlobalTabmanager::Get()->TryInvokeTab(SDFTabName);
}

// --- Menü ve Buton Kayıt İşlemleri ---
void FImport_SDFModule::RegisterMenus()
{
	// Owner: Bu plugin
	FToolMenuOwnerScoped OwnerScoped(this);

	// Level Editor Toolbar'ını bul
	UToolMenu* ToolbarMenu = UToolMenus::Get()->ExtendMenu("LevelEditor.LevelEditorToolBar.PlayToolBar");
	
	// Yeni bir "Section" (bölüm) ekle
	FToolMenuSection& Section = ToolbarMenu->FindOrAddSection("SDFTools");

	// Butonu Ekle
	// Not: Entry.SetCommandList yerine basit bir Lambda veya fonksiyon bağlıyoruz.
	FToolMenuEntry& Entry = Section.AddEntry(FToolMenuEntry::InitToolBarButton(
		"SDFImporterBtn",
		FUIAction(
			FExecuteAction::CreateRaw(this, &FImport_SDFModule::PluginButtonClicked) // <--- TIKLANINCA BURAYA GİT
		),
		LOCTEXT("SDFButtonLabel", "SDF Import"),
		LOCTEXT("SDFButtonTooltip", "SDF Importer Penceresini Acar"),
		FSlateIcon(FAppStyle::GetAppStyleSetName(), "LevelEditor.ImportMesh") // Şimdilik standart bir ikon kullandım
	));
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FImport_SDFModule, Import_SDF)