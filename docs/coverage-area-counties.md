# CNJ Mesh coverage area: counties and FIPS codes

Charlie's mesh Discord community (the Central and South New Jersey Meshtastic Discord, plus MeshCore NJ) covers **Central and South New Jersey**.
He asked on Nov 12 2026 to keep this list, because it is the area he cares about for alerts, forecasts and reports.
Home county is Middlesex; the rest is everything south of it, plus Somerset (his addition).

| County | FIPS | Position relative to Middlesex |
|---|---|---|
| Middlesex | 34023 | home county |
| Somerset | 34035 | west (added at Charlie's request) |
| Mercer | 34021 | southwest |
| Monmouth | 34025 | southeast |
| Ocean | 34029 | south and southeast |
| Burlington | 34005 | south |
| Camden | 34007 | south |
| Gloucester | 34015 | south |
| Salem | 34033 | far south |
| Cumberland | 34011 | far south |
| Atlantic | 34001 | far south and southeast |
| Cape May | 34009 | southern tip |

As a config-ready list (12 codes):

    34023,34035,34021,34025,34029,34005,34007,34015,34033,34011,34001,34009

Not on the list (the other nine NJ counties): Bergen 34003, Essex 34013, Hudson 34017, Hunterdon 34019, Morris 34027, Passaic 34031, Sussex 34037, Union 34039, Warren 34041.

Source for the codes: NWS's New Jersey county list, https://www.weather.gov/media/pimar/FIPS/nj_cnty.pdf (checked Nov 12 2026).
"South of Middlesex" is Claude's reading of the map, not an official grouping; Charlie confirmed the list by adding Somerset to it.

Where it is used or could be used:
- The Meshtastic bot's iPAWS list `myFIPSList` in `cnjmesh1/meshing-around-custom/config.ini` is currently just `34023` (Middlesex).
- The wide-area NWS alert patch (`cnjmesh1/meshing-around-custom/locationdata-alert-wide.diff`, on hold) would use the same codes as `alertFIPS`.
