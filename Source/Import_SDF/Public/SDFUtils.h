#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SDFUtils.generated.h" // Dosya adı SDFUtils olduğu için

/**
 * SDF import islemleri ve Python entegrasyonu icin genel yardimci kutuphane.
 */
UCLASS()
class IMPORT_SDF_API USDFUtils : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:

	// --- Dosya Diyalog İşlemleri ---

	UFUNCTION(BlueprintCallable, Category = "SDF Tools | File IO")
	static bool OpenFileDialog(
		const FString& DialogTitle, 
		const FString& DefaultPath, 
		const FString& FileTypes, 
		TArray<FString>& OutFileNames
	);

	// --- Python Entegrasyon İşlemleri ---

	/**
	 * Projenin 'Saved' klasorundeki belirtilen dosyayi okur.
	 */
	UFUNCTION(BlueprintCallable, Category = "SDF Tools | Python Integration")
	static FString ReadTextFromSavedDir(FString FileName = "python_temp_result.txt");
	
};