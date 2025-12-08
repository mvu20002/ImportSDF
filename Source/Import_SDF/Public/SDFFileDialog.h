#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SDFFileDialog.generated.h" // Bu satır en altta olmalı

// Plugin adı Import_SDF olduğu için API makrosu: IMPORT_SDF_API
UCLASS()
class IMPORT_SDF_API USDFFileDialog : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()
	
public:
	UFUNCTION(BlueprintCallable, Category = "SDF Tools")
	static bool OpenFileDialog(
        const FString& DialogTitle, 
        const FString& DefaultPath, 
        const FString& FileTypes, 
        TArray<FString>& OutFileNames
    );
};