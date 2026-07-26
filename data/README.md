# Building & Weather Data

This directory stores EnergyPlus model and weather input files used for smart building simulation.

## File Formats

- **`.idf` (Input Data File)**: Defines the building geometry, construction materials, HVAC systems, thermal zones, and occupancy schedules.
  - Example: `building.idf` (e.g., standard 1ZoneUncontrolled or 5ZoneSmallOffice model).
- **`.epw` (EnergyPlus Weather File)**: Contains hourly weather data (dry-bulb temp, relative humidity, solar radiation, wind speed) for specific locations.
  - Example: `USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw`.

## Usage Instructions

1. Place your target `.idf` building model file in this directory.
2. Place your target `.epw` weather file in this directory.
3. Update `.env` to point `IDF_FILE_PATH` and `EPW_FILE_PATH` to your selected files.
