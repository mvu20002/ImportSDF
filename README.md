# Import_SDF – Unreal Engine 5 Plugin

A work-in-progress Unreal Engine 5 plugin for importing Signed Distance Field (SDF) data into Unreal Editor.

## Status
Early development. APIs, file formats, and UX may change.

## Features
- Parse and import SDF data via native C++ module
- Utilities for SDF processing in `Content/Python/sdf_tools`
- Optional Blender-assisted conversion (`blender_convert.py`)

## Requirements
- Unreal Engine 5 (tested on Linux; Windows/Mac untested)
- A C++ toolchain compatible with UE5
- Optional: Blender (for Python-based conversion)

## Installation
1. Clone or copy this repository into your UE project at:
   `YourProject/Plugins/SDF_Import`
2. Open the project in Unreal Editor and enable the plugin if prompted.
3. Rebuild the project if Unreal requests a recompile.

## Usage (early)
1. Prepare SDF data in a compatible format (e.g., `.sdf` files).
2. Once the plugin is enabled, you can use Plugin's UI for importing SDF files.
<img src="media/plugin_location.png" width="600">
3. Specify your sdf path. When you specify it UI will show some info about the SDF file.
<img src="media/rl_video.gif" width="600">
4. Click "Generate Asset" to import the SDF data into your project. Plugin will automatically convert collada files to fbx files and import them to your project. You can find the imported assets in the Content Browser under `SDF_Importings/[Your Model Name]/Assets/`. And generated bluprint actor in `SDF_Importings/[Your Model Name]/[Your Model Name]`.
<img src="media/rl_video.gif" width="600">





## Contributing
Issues and pull requests are welcome. Please keep changes small and focused.

## License
TBD.
