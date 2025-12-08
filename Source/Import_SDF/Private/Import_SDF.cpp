#include "Import_SDF.h"
#include "Interfaces/IPluginManager.h"
#include "Styling/SlateStyleRegistry.h"

#define LOCTEXT_NAMESPACE "FImport_SDFModule"

void FImport_SDFModule::StartupModule()
{
	// 1. Stil Setini Oluştur (Adı: "SDFStyle")
	StyleSet = MakeShareable(new FSlateStyleSet("SDFStyle"));

	// 2. Resources Klasörünü Bul
	FString BaseDir = IPluginManager::Get().FindPlugin("Import_SDF")->GetBaseDir();
	StyleSet->SetContentRoot(BaseDir / TEXT("Resources"));

	// 3. İkonu Tanımla (Adı: "SDFIcon", Dosya: Icon128.png, Boyut: 60x60)
	// Toolbar ikonları genelde 20x20 veya 40x40 olur.
	StyleSet->Set("SDFIcon", new FSlateImageBrush(StyleSet->RootToContentDir(TEXT("Icon128.png")), FVector2D(60.0f, 60.0f)));

	// 4. Sisteme Kaydet
	FSlateStyleRegistry::RegisterSlateStyle(*StyleSet);
}

void FImport_SDFModule::ShutdownModule()
{
	// Kapanışta temizle
	if (StyleSet.IsValid())
	{
		FSlateStyleRegistry::UnRegisterSlateStyle(*StyleSet);
		ensure(StyleSet.IsUnique());
		StyleSet.Reset();
	}
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FImport_SDFModule, Import_SDF)