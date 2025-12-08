#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MyPythonUtils.generated.h"

/**
 * Python entegrasyonu icin yardimci fonksiyonlar
 */
UCLASS()
class IMPORT_SDF_API UMyPythonUtils : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	
	/**
	 * Projenin 'Saved' klasorundeki belirtilen dosyayi okur ve String olarak dondurur.
	 * @param FileName - Okunacak dosya adi (ornek: python_temp_result.txt)
	 * @return Dosya icerigi veya hata mesaji.
	 */
	UFUNCTION(BlueprintCallable, Category = "Python Integration")
	static FString ReadTextFromSavedDir(FString FileName = "python_temp_result.txt");
	
};