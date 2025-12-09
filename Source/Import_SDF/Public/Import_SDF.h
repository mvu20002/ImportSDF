// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "Modules/ModuleManager.h"
#include "Styling/SlateStyle.h"

class FImport_SDFModule : public IModuleInterface
{
public:

	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

	void PluginButtonClicked();

private:
	TSharedPtr< FSlateStyleSet > StyleSet;
	TSharedRef< class SDockTab > OnSpawnPluginTab(const class FSpawnTabArgs& SpawnTabArgs);
	void RegisterMenus();
};
