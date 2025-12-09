#include "Import_SDF.h"
#include "Interfaces/IPluginManager.h"
#include "Styling/SlateStyleRegistry.h"
#include "Widgets/Docking/SDockTab.h"
#include "ImportUI.h" 
#include "Widgets/Docking/SDockTab.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"
#include "ToolMenus.h" 

#define LOCTEXT_NAMESPACE "FImport_SDFModule"

static const FName SDFTabName("SDFImportTab");

void FImport_SDFModule::StartupModule()
{
	FGlobalTabmanager::Get()->RegisterNomadTabSpawner(SDFTabName, FOnSpawnTab::CreateRaw(this, &FImport_SDFModule::OnSpawnPluginTab))
        .SetDisplayName(FText::FromString(TEXT("SDF Importer Tool")))
        .SetMenuType(ETabSpawnerMenuType::Enabled);

	UToolMenus::RegisterStartupCallback(FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FImport_SDFModule::RegisterMenus));
}

void FImport_SDFModule::ShutdownModule()
{
	UToolMenus::UnRegisterStartupCallback(this);
	UToolMenus::UnregisterOwner(this);
	FGlobalTabmanager::Get()->UnregisterNomadTabSpawner(SDFTabName);
}

TSharedRef<SDockTab> FImport_SDFModule::OnSpawnPluginTab(const FSpawnTabArgs& SpawnTabArgs)
{
    return SNew(SDockTab)
        .TabRole(ETabRole::NomadTab)
        [
            SNew(ImportUI) 
        ];
}

void FImport_SDFModule::PluginButtonClicked()
{
	FGlobalTabmanager::Get()->TryInvokeTab(SDFTabName);
}

void FImport_SDFModule::RegisterMenus()
{
	FToolMenuOwnerScoped OwnerScoped(this);

	UToolMenu* ToolbarMenu = UToolMenus::Get()->ExtendMenu("LevelEditor.LevelEditorToolBar.PlayToolBar");
	
	FToolMenuSection& Section = ToolbarMenu->FindOrAddSection("SDFTools");

	FToolMenuEntry& Entry = Section.AddEntry(FToolMenuEntry::InitToolBarButton(
		"SDFImporterBtn",
		FUIAction(
			FExecuteAction::CreateRaw(this, &FImport_SDFModule::PluginButtonClicked) 
		),
		LOCTEXT("SDFButtonLabel", "SDF Import"),
		LOCTEXT("SDFButtonTooltip", "SDF Importer Penceresini Acar"),
		FSlateIcon(FAppStyle::GetAppStyleSetName(), "LevelEditor.ImportMesh") 
	));
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FImport_SDFModule, Import_SDF)