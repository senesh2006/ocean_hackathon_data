# What drives fish movement around Sri Lanka: a plain-language guide
Prepared 2026-10-16. The dataset was not changed. Bracketed numbers point to the sources at the bottom.

## The big picture
Sri Lanka's seas are run by the **two monsoons**. Between May and September the **southwest (SW) monsoon** winds push a strong eastward current past the south coast. They also drive **upwelling**: cold, nutrient-rich water rising to the surface along the south and southwest coasts. Plankton blooms on those nutrients, small fish follow the plankton, and tuna follow the small fish. East of the island a cold, nutrient-rich patch called the **Sri Lanka Dome** forms during the same months. From November to February the **northeast (NE) monsoon** reverses the currents, and upwelling is weaker but still present on the south coast [2][3]. Most of the factors below are pieces of this one seasonal machine.

## Factors
| # | Factor | How it affects fish (plain words) | Evidence |
|---|---|---|---|
| 1 | **Monsoon season** (SW May–Sep, inter-monsoon Mar–Apr and Oct–Nov, NE Dec–Feb) | Sets the timing of upwelling, currents and plankton. Off Sri Lanka, skipjack catches peak around Sep–Dec and around Mar and Oct; small pelagics follow the SW-monsoon bloom [2][3][4][9]. | Strong |
| 2 | **Upwelling** (south and southwest coast, Sri Lanka Dome) | Brings nutrients up and drives plankton blooms, often above 5 mg/m³ of chlorophyll in Jun–Aug. Shows up as a 2–3 °C drop in sea temperature. It creates rich feeding grounds for sardines and mackerel, and tuna gather at the edges [2][3][10]. | Strong |
| 3 | **Ocean currents** | Carry plankton and fish larvae and concentrate food. Sri Lankan yellowfin catches were highest where currents were slow to moderate (about 0.2–0.4 m/s) [1]. Strong monsoon currents move water and fish eastward. | Moderate |
| 4 | **Eddies / sea surface height** | Swirling water masses 50–200 km across trap food at their edges, and tuna gather there. A record yellowfin aggregation in the western Indian Ocean formed on an eddy edge [8]. Yellowfin off Sri Lanka favoured particular sea-height ranges [5]. | Moderate |
| 5 | **Thermocline and mixed-layer depth** | The thermocline is the boundary between warm surface water and cold deep water. Tuna mostly swim just above or in it (yellowfin about 100–180 m) [6]. When it is shallow, as in the Dome or during upwelling, fish are squeezed closer to the surface and are easier to catch. Skipjack catches were best where the mixed layer was shallow (about 10–28 m) [4]. | Moderate to strong |
| 6 | **Dissolved oxygen** | Tuna need a lot of oxygen. They avoid the low-oxygen layer at depth, which shrinks their usable habitat towards the surface. Yellowfin respond strongly to this; bigeye less so [6][7]. | Strong for vertical movement; weaker for map-based models |
| 7 | **Salinity / rainfall / river runoff** | Rain and river water freshen the coastal surface. That matters to coastal small pelagics: oil sardines mature in response to rainfall and do best in less salty years [9][10]. Tuna are much less affected [6]. | Moderate for coastal species, weak for tuna |
| 8 | **Wind** | Wind is what *drives* upwelling and mixing. Strong SW-monsoon winds give more upwelling and more food a few weeks later. It also limits where small boats can fish, which biases where records come from. | Moderate (indirect) |
| 9 | **Moon phase / moonlight** | Bright moonlit nights change where prey and predators sit in the water column. In the Indian Ocean, longline catches of bigeye, albacore and skipjack were highest around full moon, while swordfish peaked at the quarter moons [11][12][13]. Some reef fish time their spawning to the moon [14]. | Moderate; depends on species and fishing gear |
| 10 | **Tides** | Mostly matter near the coast. Tidal currents at reef channels and lagoon mouths gather fish and trigger spawning, often at outgoing tide around dusk [14]. Sri Lanka's tides are small (well under 1 m), so the effect is mostly local. | Moderate for reef and lagoon fish; weak offshore |
| 11 | **Time of day** | Many fish rise towards the surface at night and dive by day, following prey. Reef fish spawn at set times of day [14]. Point records often lack a time, so this is hard to use. | Strong biologically; hard to use as data |
| 12 | **Climate cycles** (Indian Ocean Dipole, El Niño) | Shift warm water, the thermocline and food across the ocean from year to year. Positive-Dipole years lower western Indian Ocean yellowfin catch rates [15]. The 2015 El Niño hurt sardine breeding [10]. | Moderate (year-to-year effect) |
| 13 | **Seafloor habitat** (reef, shelf edge, canyons) | Reef fish stay put on reefs. Shelf edges and canyons, such as the Trincomalee canyon and the narrow southern shelf, concentrate food and fish. | Strong for reef and demersal fish |
| 14 | **Larval drift and spawning season** | Sri Lankan west-coast fish larvae peak in March and again in Sep–Nov, tied to the monsoons [16]. Currents then carry the young fish. | Moderate |

## Most useful to add later (brief)
These are open data with no login. Not added yet.
1. **Monsoon-season label.** Derived from the date, no download needed.
2. **Moon phase / moon brightness.** Calculated from the date (for example with the `ephem` Python library).
3. **Sea surface height, eddy strength and currents.** Copernicus Marine has these, but it requires a free login. NOAA CoastWatch ERDDAP has open sea-level data.
4. **Mixed-layer depth, salinity and oxygen.** Copernicus ocean-model products (free login), or the World Ocean Atlas 2023 monthly averages (open, from NOAA NCEI).
5. **Wind / upwelling index.** NOAA ERDDAP has open satellite wind data, or ERA5 (free Copernicus login).
6. **Rainfall.** CHIRPS or GPM IMERG monthly, both open.
7. **Dipole / El Niño indices.** NOAA PSL monthly index text files, open.
Tides and time of day: skip for now, because most records have no time.

## Sources
1. Effect of ocean circulation and chlorophyll-a on yellowfin catch rates in the Sri Lankan longline fishery. Ceylon J. Sci. 52(3). https://doi.org/10.4038/cjs.v52i3.8208
2. Vinayachandran et al. 2004. Biological response of the sea around Sri Lanka to summer monsoon. Geophys. Res. Lett. https://doi.org/10.1029/2003GL018533
3. de Vos et al. 2014. Surface circulation and upwelling patterns around Sri Lanka. Biogeosciences 11:5909. https://doi.org/10.5194/bg-11-5909-2014
4. Skipjack tuna fishing grounds and oceanographic variables, southern coast of Sri Lanka (conference proceedings, Univ. of Sri Jayewardenepura; the page was unavailable when checked, not peer-reviewed).
5. Environmental preferences of yellowfin tuna in the NE Indian Ocean from Sri Lankan longline catches (FAO copy). https://openknowledge.fao.org/server/api/core/bitstreams/aa4420b8-11f3-4143-890d-83a8a7fd6f13/content
6. Song et al. 2009. Environmental preferences of longlining for yellowfin tuna in the tropical high seas of the Indian Ocean. Fish. Oceanogr. https://doi.org/10.1111/j.1365-2419.2008.00476.x
7. Bigeye and yellowfin responses to oxygen minimum zones (2024). https://pmc.ncbi.nlm.nih.gov/articles/PMC10787700/
8. Mesoscale exploitation of a major tuna concentration in the Indian Ocean. Aquat. Living Resour. https://doi.org/10.1051/alr:2008028
9. Climate impacts on the landings of Indian oil sardine, SE Arabian Sea. Fish and Fisheries 2020. https://eprints.cmfri.org.in/14827/1/Fish%20and%20Fisheries_2020_Grinson%20George_Climate%20impacts%20on%20the%20landings%20of%20Indian%20oil%20sardine.pdf
10. Overfishing and climate drive changes in Indian oil sardine. Front. Mar. Sci. 2018. https://doi.org/10.3389/fmars.2018.00443
11. Jatmiko et al. 2016. Effect of moon phase on bigeye tuna catch, Eastern Indian Ocean. https://doi.org/10.14710/ik.ijms.21.3.101-106
12. Poisson et al. Effects of lunar cycle on longline-caught pelagic fish (Réunion). https://archimer.ifremer.fr/doc/00011/12237/
13. Lunar cycle and monsoon effects on skipjack around Andaman & Nicobar Islands (regional journal). https://keralamarinelife.in/Journals/Vol3-12/05%20Sajeevan%20and%20Rajashree.pdf
14. Environmental influences on the diel timing of spawning in coral reef fishes. Mar. Ecol. Prog. Ser. 206:193. https://doi.org/10.3354/meps206193
15. Effects of climate variability on yellowfin tuna in the western Indian Ocean. Climatic Change. https://doi.org/10.1007/s10584-012-0637-8
16. Seasonal and spatial distribution of ichthyoplankton, west coast of Sri Lanka. Asian Fish. Sci. 2021. https://doi.org/10.33997/j.afs.2021.34.4.001
Also: Interannual variability of chlorophyll over the Sri Lanka Dome. Int. J. Remote Sens. 2020. https://doi.org/10.1080/01431161.2020.1727057
