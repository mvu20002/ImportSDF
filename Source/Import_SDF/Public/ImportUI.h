#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Input/SMultiLineEditableTextBox.h" // <--- DÜZELTİLEN HEADER

class ImportUI : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(ImportUI) {}
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

private:
	// Arayüz Elemanları
	TSharedPtr<SEditableTextBox> SDFPathTextBox;
	TSharedPtr<SEditableTextBox> OutputPathTextBox;
	
	// BURASI DEĞİŞTİ: Text yerine TextBox (Daha şık görünür)
	TSharedPtr<SMultiLineEditableTextBox> ReportView; 

	// Fonksiyonlar
	FReply OnBrowseClicked();
	FReply OnImportClicked();
	
	void UpdateReportView(const FString& SDFPath);
};