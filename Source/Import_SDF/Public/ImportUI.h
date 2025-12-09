#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Input/SMultiLineEditableTextBox.h" 

class ImportUI : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(ImportUI) {}
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

private:
	TSharedPtr<SEditableTextBox> SDFPathTextBox;
	TSharedPtr<SEditableTextBox> OutputPathTextBox;
	
	TSharedPtr<SMultiLineEditableTextBox> ReportView; 

	FReply OnBrowseClicked();
	FReply OnImportClicked();
	
	void UpdateReportView(const FString& SDFPath);
};