#include "MyPythonUtils.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

FString UMyPythonUtils::ReadTextFromSavedDir(FString FileName)
{
	// 1. Projenin Saved klasorunun yolunu al
	FString SavedDir = FPaths::ProjectSavedDir();

	// 2. Klasor yolu ile dosya adini birlestir (Platforma uygun slash ekler)
	FString FullPath = FPaths::Combine(SavedDir, FileName);

	// 3. Dosyanin varligini kontrol et (Opsiyonel ama guvenli)
	if (!FPaths::FileExists(FullPath))
	{
		return FString::Printf(TEXT("Hata: Dosya bulunamadi -> %s"), *FullPath);
	}

	// 4. Dosyayi oku
	FString ResultString;
	bool bSuccess = FFileHelper::LoadFileToString(ResultString, *FullPath);

	if (bSuccess)
	{
		return ResultString;
	}
	else
	{
		return FString(TEXT("Hata: Dosya var ama okunamadi (Izin sorunu olabilir)."));
	}
}