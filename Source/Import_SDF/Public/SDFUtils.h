#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SDFUtils.generated.h"


UCLASS()
class IMPORT_SDF_API USDFUtils : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:


	UFUNCTION(BlueprintCallable, Category = "SDF Tools | File IO")
	static bool OpenFileDialog(
		const FString& DialogTitle, 
		const FString& DefaultPath, 
		const FString& FileTypes, 
		TArray<FString>& OutFileNames
	);

	UFUNCTION(BlueprintCallable, Category = "SDF Tools | Python Integration")
	static FString ReadTextFromSavedDir(FString FileName = "python_temp_result.txt");
	
};