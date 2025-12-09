#include "SDFUtils.h"

// File Dialog icin gerekenler
#include "Developer/DesktopPlatform/Public/IDesktopPlatform.h"
#include "Developer/DesktopPlatform/Public/DesktopPlatformModule.h"
#include "Interfaces/IMainFrameModule.h"
#include "Framework/Application/SlateApplication.h"

// Dosya okuma icin gerekenler
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

// --- Dosya Diyalog Fonksiyonu ---
bool USDFUtils::OpenFileDialog(const FString& DialogTitle, const FString& DefaultPath, const FString& FileTypes, TArray<FString>& OutFileNames)
{
	IDesktopPlatform* DesktopPlatform = FDesktopPlatformModule::Get();
	if (!DesktopPlatform) return false;

	const void* ParentWindowHandle = nullptr;
	IMainFrameModule& MainFrameModule = FModuleManager::LoadModuleChecked<IMainFrameModule>(TEXT("MainFrame"));
	const TSharedPtr<SWindow>& MainFrameParentWindow = MainFrameModule.GetParentWindow();
	
	if (MainFrameParentWindow.IsValid() && MainFrameParentWindow->GetNativeWindow().IsValid())
	{
		ParentWindowHandle = MainFrameParentWindow->GetNativeWindow()->GetOSWindowHandle();
	}

	return DesktopPlatform->OpenFileDialog(
		ParentWindowHandle,
		DialogTitle,
		DefaultPath,
		TEXT(""),
		FileTypes,
		EFileDialogFlags::None,
		OutFileNames
	);
}

// --- Dosya Okuma Fonksiyonu ---
FString USDFUtils::ReadTextFromSavedDir(FString FileName)
{
	FString SavedDir = FPaths::ProjectSavedDir();
	FString FullPath = FPaths::Combine(SavedDir, FileName);

	if (!FPaths::FileExists(FullPath))
	{
		return FString::Printf(TEXT("Hata: Dosya bulunamadi -> %s"), *FullPath);
	}

	FString ResultString;
	if (FFileHelper::LoadFileToString(ResultString, *FullPath))
	{
		return ResultString;
	}
	
	return FString(TEXT("Hata: Dosya okunamadi."));
}