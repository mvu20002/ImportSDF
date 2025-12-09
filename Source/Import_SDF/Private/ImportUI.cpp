#include "ImportUI.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Developer/DesktopPlatform/Public/IDesktopPlatform.h"
#include "Developer/DesktopPlatform/Public/DesktopPlatformModule.h"
#include "Framework/Application/SlateApplication.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Engine/Engine.h"
#include "IPythonScriptPlugin.h" 

#define LOCTEXT_NAMESPACE "ImportUI"

void ImportUI::Construct(const FArguments& InArgs)
{
    ChildSlot
    [
        SNew(SVerticalBox)
        + SVerticalBox::Slot().AutoHeight().Padding(5)
        [
            SNew(SHorizontalBox)
            + SHorizontalBox::Slot().AutoWidth().Padding(5).VAlign(VAlign_Center)[ SNew(STextBlock).Text(FText::FromString("SDF Path:")) ]
            + SHorizontalBox::Slot().FillWidth(1.0f).Padding(5)[ SAssignNew(SDFPathTextBox, SEditableTextBox).HintText(FText::FromString("Select a .sdf file...")) ]
            + SHorizontalBox::Slot().AutoWidth().Padding(5)[ SNew(SButton).Text(FText::FromString("Explore")).OnClicked(this, &ImportUI::OnBrowseClicked) ]
        ]
        + SVerticalBox::Slot().AutoHeight().Padding(5)
        [
            SNew(SHorizontalBox)
            + SHorizontalBox::Slot().AutoWidth().Padding(5).VAlign(VAlign_Center)[ SNew(STextBlock).Text(FText::FromString("Output Path:")) ]
            + SHorizontalBox::Slot().FillWidth(1.0f).Padding(5)[ SAssignNew(OutputPathTextBox, SEditableTextBox).Text(FText::FromString("/Game/SDF_Imports")) ]
        ]
        + SVerticalBox::Slot().FillHeight(1.0f).Padding(5)
        [
            SNew(SScrollBox) + SScrollBox::Slot()[ SAssignNew(ReportView, SMultiLineEditableTextBox).Text(FText::FromString("Report will appear here...")).IsReadOnly(true).AutoWrapText(true) ]
        ]
        + SVerticalBox::Slot().AutoHeight().Padding(10).HAlign(HAlign_Right)
        [
            SNew(SButton).Text(FText::FromString("Generate Asset")).OnClicked(this, &ImportUI::OnImportClicked).ContentPadding(FMargin(20, 5))
        ]
    ];
}

FReply ImportUI::OnBrowseClicked()
{
    IDesktopPlatform* DesktopPlatform = FDesktopPlatformModule::Get();
    if (!DesktopPlatform) return FReply::Handled();

    TArray<FString> OutFileNames;
    const void* ParentWindowHandle = FSlateApplication::Get().FindBestParentWindowHandleForDialogs(nullptr);

    bool bOpened = DesktopPlatform->OpenFileDialog(
        ParentWindowHandle, TEXT("Select SDF File"), FPaths::ProjectDir(), TEXT(""), TEXT("SDF Files (*.sdf)|*.sdf"), EFileDialogFlags::None, OutFileNames
    );

    if (bOpened && OutFileNames.Num() > 0)
    {
        if (SDFPathTextBox.IsValid()) SDFPathTextBox->SetText(FText::FromString(OutFileNames[0]));
        UpdateReportView(OutFileNames[0]);
    }
    return FReply::Handled();
}

void ImportUI::UpdateReportView(const FString& SDFPath)
{
    FString PluginPythonPath = FPaths::Combine(FPaths::ProjectPluginsDir(), TEXT("SDF_Import/Content/Python"));
    FString CleanPluginPath = FPaths::ConvertRelativePathToFull(PluginPythonPath);
    CleanPluginPath.ReplaceInline(TEXT("\\"), TEXT("/"));

    FString PythonCode = FString::Printf(
        TEXT("import sys\n"
             "sys.path.append(r'%s')\n"
             "import importlib\n"
             "import sdf_tools.core\n"
             "importlib.reload(sdf_tools.core)\n"
             "try:\n"
             "    sdf_tools.core.run(sdf_path_arg=r'%s', analyze_only=True)\n"
             "except Exception as e:\n"
             "    print(f'Python Error: {e}')"),
        *CleanPluginPath,
        *SDFPath
    );

    IPythonScriptPlugin* PythonPlugin = IPythonScriptPlugin::Get();
    if (PythonPlugin && PythonPlugin->IsPythonAvailable())
    {
        PythonPlugin->ExecPythonCommand(*PythonCode);
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("Python Plugin yuklu degil veya aktif degil!"));
    }

    FString SavedDir = FPaths::ProjectSavedDir();
    FString ReportFile = FPaths::Combine(SavedDir, TEXT("python_temp_result.txt"));
    FString ResultString;

    if (FFileHelper::LoadFileToString(ResultString, *ReportFile))
    {
        if (ReportView.IsValid()) ReportView->SetText(FText::FromString(ResultString));
    }
    else
    {
        if (ReportView.IsValid()) ReportView->SetText(FText::FromString("Error: Python execution failed. Check Output Log."));
    }

	bool bDeleted = IFileManager::Get().Delete(*ReportFile, false, true);

	if (bDeleted)
	{
		UE_LOG(LogTemp, Log, TEXT("Gecici rapor dosyasi temizlendi: %s"), *ReportFile);
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("UYARI: Gecici dosya silinemedi! Kilitli olabilir: %s"), *ReportFile);
	}
}

FReply ImportUI::OnImportClicked()
{
    FString SDFPath = SDFPathTextBox->GetText().ToString();
    FString OutPath = OutputPathTextBox->GetText().ToString();

    if (SDFPath.IsEmpty()) return FReply::Handled();

    FString PluginPythonPath = FPaths::Combine(FPaths::ProjectPluginsDir(), TEXT("SDF_Import/Content/Python"));
    FString CleanPluginPath = FPaths::ConvertRelativePathToFull(PluginPythonPath);
    CleanPluginPath.ReplaceInline(TEXT("\\"), TEXT("/"));

    FString PythonCode = FString::Printf(
        TEXT("import sys\n"
             "sys.path.append(r'%s')\n"
             "import importlib\n"
             "import sdf_tools.core\n"
             "importlib.reload(sdf_tools.core)\n"
             "try:\n"
             "    sdf_tools.core.run(sdf_path_arg=r'%s', dest_pkg_arg='%s', analyze_only=False)\n"
             "except Exception as e:\n"
             "    print(f'Python Error: {e}')"),
        *CleanPluginPath,
        *SDFPath, 
        *OutPath
    );

    IPythonScriptPlugin* PythonPlugin = IPythonScriptPlugin::Get();
    if (PythonPlugin && PythonPlugin->IsPythonAvailable())
    {
        UE_LOG(LogTemp, Log, TEXT("Executing Python Asset Generation..."));
        PythonPlugin->ExecPythonCommand(*PythonCode);
    }

    return FReply::Handled();
}

#undef LOCTEXT_NAMESPACE