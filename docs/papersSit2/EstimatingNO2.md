Estimating Surface NO2 in Mexico City Using Sentinel-5P and Machine Learning

Abstract
This study presents a methodological framework for estimating surface nitrogen dioxide (NO2) concentrations in Mexico City during 2024. Sentinel-5P satellite observations, ERA5 meteorological variables, and ground measurements from the RAMA were integrated to generate high-resolution estimates through a Random Forest model combined with statistical downscaling. After data cleaning, 3246 aligned records were retained. The model achieved robust performance (R2 = 0.9196; RMSE = 6.80 µg/m3; MAE = 4.55 µg/m3), demonstrating its ability to reproduce both spatial and temporal variations in NO2 across the metropolitan area. These results confirm that machine-learning-based downscaling effectively enhances satellite-derived pollution estimates and provides a reliable tool for urban air quality assessment.
Keywords: nitrogen dioxide; Sentinel-5P; RAMA; Random Forest; statistical downscaling; bilinear interpolation; air pollution; Mexico City


Graphical Abstract
1. Introduction
Nitrogen dioxide (NO2) is one of the main atmospheric criteria pollutants and acts as a key indicator of the intensity of urban emissions. It is mainly produced by combustion processes from mobile, thermoelectric, and industrial sources [1,2]. Its environmental and health relevance is high, as it contributes to the formation of tropospheric ozone and secondary particulate matter, and is associated with adverse respiratory effects and increased mortality from chronic diseases [3].
The interest in measuring and modeling NO2 stems from the fact that its spatial and temporal behavior directly reflects urban mobility patterns and vehicular emissions, making it an effective tracer of combustion-derived pollution. Unlike other pollutants, such as PM2.5 or SO2, NO2 has a well-defined, quantifiable satellite signal, as detected by sensors like Sentinel-5P/TROPOMI, allowing integration of remote observations and ground-based data for the validation and calibration of atmospheric models [4,5,6].
Mexico City (CDMX) was selected as the study area for three main reasons:
Data availability and density: CDMX’s Automatic Atmospheric Monitoring Network (RAMA) records hourly concentrations of criteria gases at multiple stations across the metropolitan area [7,8]. In contrast, cities like Manzanillo or Veracruz lack sufficient coverage to validate downscaling models.
Complex urban and topographic context: CDMX has high vehicular density and topographic features that hinder pollutant dispersion, which supports the use of high-resolution techniques [2,9].
Air quality management relevance: As Mexico’s most monitored city, CDMX enables validation of methodologies transferable to other Mexican cities [10].
The use of statistical downscaling techniques and machine learning models (Random Forest) enables the transition from satellite scale (10–100 km) to urban scale (1 km or less), capturing the local variability of NO2 and improving the spatial resolution of satellite products [11,12]. This approach contributes to strengthening artificial intelligence-based tools for environmental management and to the design of emission mitigation policies in complex metropolitan areas.
Remote sensing instruments such as Sentinel-5P retrieve tropospheric NO2 by measuring backscattered solar radiation and applying inversion algorithms that incorporate atmospheric absorption, surface reflectance, and scattering corrections [4,5,6]. These retrievals represent column densities rather than surface-level concentrations, which necessitates the use of statistical downscaling techniques or chemical transport modeling to obtain near-surface estimates [10,11,12]. Furthermore, atmospheric processes, including boundary layer height dynamics, vertical mixing, and photochemical transformations, affect the relationship between columnar and ground-level NO2, introducing variability that must be considered when interpreting satellite observations [1,6,13]. Integrating these physical and algorithmic principles provides a robust theoretical basis for combining satellite retrievals with machine learning approaches to enhance urban-scale air pollution estimation and monitoring [14,15,16].
2. Materials and Methods
2.1. Study Area
The study was conducted in Mexico City (Ciudad de México, CDMX), located in the Valley of Mexico between 19°20′ and 19°30′ N latitude and 99°00′ and 99°15′ W longitude, at an average altitude of approximately 2240 m above sea level. The city is surrounded by mountain ranges that restrict horizontal air circulation, creating meteorological conditions favorable to pollutant accumulation. The urban area covers approximately 1485 km2 and has an estimated population of 9.2 million inhabitants, increasing to more than 21 million when considering the entire metropolitan area [2].
The regional climate is classified as temperate sub-humid, with a well-defined rainy season from May to October and a dry season from November to April. These climatic characteristics strongly influence the dispersion, vertical mixing, and photochemical transformation of nitrogen dioxide (NO2), particularly during periods characterized by temperature inversions and low wind speeds.
2.2. Data Sources
The study integrates satellite, meteorological reanalysis, and ground-based observations by first filtering and preprocessing each dataset, as described below.
The datasets were then temporally and spatially aligned to enable joint analysis: Sentinel-5P/TROPOMI: Daily tropospheric NO2 column densities (in mol/m2) were obtained for the period January–December 2024 from the Sentinel-5P satellite mission operated by the European Space Agency (ESA, Paris, France). The TROPOspheric Monitoring Instrument (TROPOMI) was developed by Airbus Defence and Space (Toulouse, France) and is operated within the Copernicus Earth Observation Programme of the European Commission (Brussels, Belgium).
Data were accessed through the Copernicus Open Access Hub (European Commission and ESA, Brussels, Belgium/Paris, France). Satellite observations were filtered using a cloud fraction threshold below 20% and a quality assurance (QA) value greater than 0.75, following recommended validation practices [14]. Data were filtered for cloud cover below 20% and a quality assurance (QA) value greater than 0.75.
In addition to satellite-based NO2 observations, meteorological variables, including 2-m air temperature, surface pressure, wind speed, relative humidity, and planetary boundary layer height (PBLH), were obtained from the ERA5 global reanalysis produced by the European Centre for Medium-Range Weather Forecasts (ECMWF, Reading, United Kingdom). ERA5 data were retrieved at a spatial resolution of 0.25° × 0.25° and hourly temporal resolution [5,6]. To complement the satellite and meteorological information, surface-level NO2 concentrations were obtained from the Automatic Atmospheric Monitoring Network (Red Automática de Monitoreo Atmosférico, RAMA), operated by the Secretaría del Medio Ambiente (SEDEMA), Mexico City, Mexico. Hourly NO2 measurements (ppb) were downloaded from the Mexico City Atmospheric Monitoring System portal [8], and daily mean concentrations were computed for comparison with satellite observations.
(A)
Conversion of Station Data (ppb → µg/m3)
The concentrations of NO2 measured by the stations of the Automatic Atmospheric Monitoring Network (RAMA) are reported in parts per billion (ppb). To convert them to micrograms per cubic meter (µg/m3), the equation derived from the ideal gas law was applied:
C(µgm3)=C(ppb)×(M×PR×T)
(1)
where
C(μgm3)
 is the concentration in micrograms per cubic meter,
C(ppb)
 is the concentration in parts per billion,
M
 is the molecular weight of NO2 (46 g/mol),
P
 is the atmospheric pressure (hPa),
R
 is the universal gas constant (8.314 J·mol−1·K−1), and
T
 is the temperature in Kelvin (K).
This relationship is frequently used in air quality studies [1,11] to convert atmospheric NO2 measurements into mass units, facilitating comparisons between ground stations and satellite observations.
For standard conditions (1 atm, 298 K), the approximation used was:
C(µgm3)≈C(ppb)×1.88
(2)
This conversion allows direct comparison between surface measurements and concentrations derived from satellite products, expressed in units of mass per volume. This method is widely accepted in the literature on urban air pollution [1,17,18].
(B)
Conversion of Satellite Data (mol/m2 → µg/m3)
The tropospheric NO2 columns provided by Sentinel-5P/TROPOMI represent the number of moles per square meter (mol/m2).
First, to convert moles per square meter (mol/m2) to parts per million (ppm) of nitrogen dioxide (NO2), the molar concentration must be converted into a mass concentration (g/m3) and then into ppm. The conversion from mol/m2 to ppm of NO2 is not direct, since mol/m2 represents a molar concentration over an area, while ppm refers to a volumetric concentration.
Equation (3) converts mol/m2 to mol/m3 by multiplying the molar concentration by the height of the volume being considered. For example, if an air column of height h meters is considered, the molar concentration in mol/m3 would be (mol/m2) × h (m).
In this study, the column height is 7 km (i.e., 7000 m), as TROPOMI performs spatial sampling at a 7 km × 7 km resolution, since NO2 is primarily located within the troposphere [14,15].
For tropospheric NO2 or tropospheric ozone, Sentinel-5P specifically retrieves concentrations limited to the troposphere (approximately from the surface to altitudes of 8–15 km, depending on latitude and season). Tropospheric NO2 is the focus of air quality monitoring because it is more closely associated with human activities, such as traffic and industry. Therefore, in this study, the column height of 7 km is derived from the operation 15 − 8 = 7.
molm3=molm2×𝑐𝑜𝑙𝑢𝑚𝑛 ℎ𝑒𝑖𝑔ℎ𝑡
(3)
The next step was to calculate the mass concentration (g/m3) using the following equation:
gm3=molm3×molar mass of NO2
(4)
where the molar mass of NO2 is 46.005 g/mol [16].
Finally, the ppm value was calculated using the density of NO2 at standard conditions (0 °C [273.15 K] and 1 atm), which is approximately 1.697 g/m3.
For the above, the ideal gas law in its density form was used as a reference [19]:
PV=nRT
(5)
However, the density p (in g/m3) is given by:
p=mv=nMV
(6)
Therefore, the formula for the density of a gas is:
p=PMRT
(7)
where
p: density (g/m3)
P: pressure (in Pa = pascals)
M: molar mass (g/mol)
R: gas constant = 8.314 J/mol·K
T: absolute temperature (K)
Data:
P = 1 atm = 101,325 Pa
T = 0 °C = 273.15 K
M = 46.0055 g/mol
R = 8.314 J/mol·K
Substituting into the formula:
p=(101,325Pa)(46.0055gmol)(8.314Jmol·K)(273.15K)
p=4,664,865.2882271.0951≈1.697gm3
The formula for calculating ppm is:
ppm=⎛⎝⎜⎜⎜⎜concentration massgm3density NO2(p)⎞⎠⎟⎟⎟⎟(106)
(8)
Then, the conversion from ppm to µg/m3 was performed using the equation derived from the ideal gas law, which allows expressing the mass of a gas as a function of its volumetric concentration, temperature, and atmospheric pressure:
C(µgm3)=C(ppm)×(M×PR×T)
(9)
where
C(μgm3)
 is the concentration in micrograms per cubic meter,
C(ppm)
 is the concentration in parts per million,
M
 is the molar mass of NO2 (46 g·mol−1),
P
 is the atmospheric pressure (in hPa or Pa),
R
 is the gas constant (8.314 J·mol−1·K−1), and
T
 is the temperature in Kelvin (K).
For standard conditions (1 atm = 1013.25 hPa, 298 K), the equation simplifies to the following empirical form, commonly used in air quality studies:
C(µgm3)≈C(ppm)×1.88×103
(10)
Therefore, 1 ppm of NO2 is approximately equivalent to 1880 µg/m3 under standard conditions.
This conversion is widely used to harmonize data from different sources (ground stations and satellite products), ensuring comparability between observations expressed in volumetric units (ppm) and mass units (µg/m3). Furthermore, the relationship has been validated in several atmospheric modeling and monitoring studies [1,15,16,17,18,19].
This enabled direct comparison of satellite and ground-based NO2 values on the same scale and in the same unit.
To illustrate this process, Figure 1 outlines the steps of the NO2 unit conversion process and demonstrates how it is integrated into the broader methodological framework for NO2 estimation.
Atmosphere 17 00037 g001
Figure 1. Conceptual diagram of unit conversion and its integration within the data processing workflow. Source: Author’s own elaboration.
This study was conducted strictly for academic purposes. The data analyzed were not reported to any governmental entity, and their processing focused on evaluating pollutant behavior from a scientific and exploratory perspective.
2.3. Metrics
Model performance was evaluated using four complementary statistical metrics that quantify goodness-of-fit, predictive accuracy, and systematic error between observed and modeled NO2 concentrations. The coefficient of determination (R2), root mean squared error (RMSE), mean absolute error (MAE), and mean bias error (Bias) were selected because they are widely used in air quality modeling and satellite–ground validation studies. Together, these metrics provide a comprehensive assessment of model performance across different concentration ranges and spatial contexts. The formal definitions, mathematical expressions, and interpretation guidelines for each metric are summarized in Table 1.
Table 1. Definitions, formulas, and interpretation guidance for performance metrics (R2, RMSE, MAE, and Bias) used in this study.

2.4. Data Preprocessing
(A)
Temporal Alignment
The time zone was unified to America/Mexico_City.
Satellite observations (13:20 local time) were matched to the nearest hourly block (13:00 h).
A continuous time series was generated for each station by combining ERA5 and Sentinel-5P data.
Records without temporal matches across sources (NA) were removed.
(B)
Data Cleaning
Data cleaning was performed in R, removing null values, outliers, and unvalidated records, preserving only synchronized and complete observations.
(C)
Spatial Bilinear Interpolation
To synchronize differences in resolution between point-based stations and satellite pixels, bilinear interpolation was applied. This method calculates intermediate values by weighting the distances between the four nearest points.
As shown in Figure 2, bilinear interpolation smoothed spatial variability in NO2 across monitoring stations.
Atmosphere 17 00037 g002
Figure 2. Scheme of bilinear interpolation between satellite pixels and RAMA station locations. Source: Author’s own elaboration based on data processed with Python.
The bilinear interpolation demonstrated solid performance: Coefficient of Determination (R2): 0.9196; Root Mean Square Error (RMSE): 6.80 µg/m3; Mean Absolute Error (MAE): 4.55 µg/m3; and Bias: 0.20 µg/m3 (see Table 2). These results confirm the method’s ability to represent the spatial variability of NO2 with high precision, consistent with previous studies conducted in similar urban contexts [11,20,21,22].
Table 2. Evaluation of the Machine Learning Model.

Statistical Comparison Between Satellite Data and Ground-Based Observations
Comparing nitrogen dioxide (NO2) concentrations from satellite (Sentinel-5P/TROPOMI) and surface measurements (RAMA) allowed assessment of both data sources. Both time series (Figure 3 and Figure 4) showed similar patterns. Peaks coincided with periods of high vehicular activity and stable atmospheric conditions. This revealed a strong temporal correspondence between spatial and ground-based observations.
Atmosphere 17 00037 g003
Figure 3. Time series of nitrogen dioxide (NO2) concentrations in µg/m3 obtained from Sentinel-5P/TROPOMI satellite observations (NO2_µg/m3_sat). Source: Author’s own elaboration based on Sentinel-5P/TROPOMI and RAMA (2024) data, processed in Python 3.11.
Atmosphere 17 00037 g004
Figure 4. Time series of nitrogen dioxide (NO2) concentrations in µg/m3 obtained from surface measurements from the Automatic Atmospheric Monitoring Network (RAMA) (NO2_µg/m3_est) during the year 2024. Source: Author’s own elaboration based on Sentinel-5P/TROPOMI and RAMA (2024) data, processed in Python 3.11.
Statistical analysis showed a strong Pearson correlation (r > 0.90) between the two measurements. Annual mean NO2 concentration was 42.8 µg/m3 from RAMA. It was 41.9 µg/m3 from satellite data after conversion and alignment. Ground-based data had a slightly higher standard deviation (±27.5 µg/m3) than satellite data (±24.8 µg/m3), reflecting more local surface-level variability.
These differences arise from the nature of each observation. Satellite sensors measure integrated tropospheric columns, which are affected by dispersion factors, cloud cover, and optical depth. Monitoring stations, in contrast, capture point-specific surface values that may be amplified by traffic intensity and unique topographic conditions [2,5,23,24].
The analysis of the mean bias (Bias) revealed a slight overestimation of satellite data relative to stations (+0.06 µg/m3), indicating an excellent fit and the potential to apply bias-correction techniques, such as quantile mapping, to enhance the local representation of modeled values. Therefore, we recommend implementing bias corrections, specifically quantile mapping, to enhance the accuracy of local satellite data. This level of agreement is comparable to that found in studies conducted in other megacities, where the differences between satellite and surface observations generally remain within ±10% [4,14,18,25].
The graphs illustrate the temporal correspondence between the two data sources and the consistency of concentration peaks associated with urban pollution episodes.
2.5. Downscaling and Modeling with Random Forest
A statistical downscaling was implemented using a Random Forest Regressor model, trained with cross-validation stratified by station (GroupKFold).
The predictor variables included:
Tropospheric NO2 columns (TROPOMI)
Temperature (ERA5)
Atmospheric pressure (ERA5)
Planetary Boundary Layer Height (PBLH, ERA5)
Geographic coordinates (latitude, longitude)
Figure 5 illustrates the methodological workflow employed for data integration, unit conversion, bilinear interpolation, and Random Forest (RF) modeling, applied to NO2 concentrations in Mexico City.
Atmosphere 17 00037 g005
Figure 5. Methodological diagram of the workflow for integration, conversion, interpolation, and RF modeling. Source: Author’s own elaboration based on data processed with Python.
The model was adjusted to capture the spatial and temporal variability of NO2 at the urban scale.
2.6. Baseline Model
In this study, the Random Forest (RF) algorithm serves as the only baseline model for predicting surface-level NO2 concentrations. RF was selected due to its demonstrated robustness in handling heterogeneous environmental datasets, its capacity to model non-linear interactions between satellite-derived NO2, meteorological variables, and spatial features, and its successful application in prior downscaling studies in urban air quality assessment. Unlike linear baseline approaches commonly used in statistical downscaling, such as Multiple Linear Regression (MLR), RF does not assume linearity between predictors and pollutant concentrations, enabling it to capture complex atmospheric processes governing pollutant dispersion and accumulation.
RF thus serves both as the primary model and the baseline reference, against which the performance of more advanced architectures, including state-of-the-art multimodal deep learning models such as AQNet, is evaluated. This choice aligns with the growing use of ensemble-based baselines in satellite-driven air quality modeling [11,16,21,26], where RF has consistently outperformed linear models while remaining computationally efficient.
2.7. Comparison with the State-of-the-Art AQNet Model
To contextualize the performance of the RF-based downscaling framework, we conducted a comparative analysis against AQNet, a recently proposed multimodal deep learning architecture specifically designed for Sentinel-based NO2 prediction. AQNet integrates:
(1)
Sentinel-2 multispectral imagery (12 bands);
(2)
Sentinel-5P tropospheric NO2;
(3)
Tabular descriptors including altitude, population density, urban/rural classification, and station metadata.
AQNet employs a MobileNetV3 backbone for Sentinel-2, a compact CNN for Sentinel-5P, and a fully connected network for structured data, followed by multimodal fusion layers. Trained across more than 1300 stations in Europe (2018–2020), AQNet achieved:
R2 = 0.685 (baseline architecture)
R2 = 0.728–0.755 (fine-tuned version)
MAE = 3.21–3.62 µg/m3
MSE = 18.4–33.5 µg/m3
Our RF model, trained exclusively on TROPOMI, ERA5 variables, and RAMA observations, outperformed both AQNet configurations, achieving R2 = 0.972, RMSE = 3.81 µg/m3, and MAE = 2.91 µg/m3. Despite its simplicity relative to AQNet’s multimodal design, RF benefited from high-quality, locally aligned data, demonstrating that traditional ensemble techniques can surpass deep neural architectures when supported by dense in situ observations and region-specific preprocessing workflows.
This finding is consistent with prior evaluations showing that deep learning models outperform classical machine learning only when large, multiregional datasets are available [12,14,27].
To contextualize the performance of the Random Forest (RF) downscaling framework developed in this study, a comparative evaluation was conducted against AQNet, a recently proposed state-of-the-art multimodal deep learning architecture for Sentinel-based NO2 prediction. The quantitative performance comparison between the RF model and both the baseline and fine-tuned versions of AQNet is summarized in Table 3.
Table 3. Performance comparison between RF and AQNet.

As shown in Table 3, the RF model achieved substantially higher predictive skill than AQNet across all reported metrics, including the coefficient of determination (R2), root mean squared error (RMSE), and mean absolute error (MAE). Despite relying on fewer input modalities, limited to TROPOMI tropospheric NO2, ERA5 meteorological variables, and geographic coordinates, the RF model outperformed AQNet’s multimodal configurations, which integrate Sentinel-2 imagery, Sentinel-5P data, and tabular descriptors. This result highlights the effectiveness of locally aligned preprocessing and dense in situ observations, demonstrating that ensemble-based machine learning approaches can surpass complex deep learning architectures when applied to region-specific air quality downscaling.
2.8. Ablation Studies
Inspired by the ablation design presented in AQNet, where Sentinel-2, Sentinel-5P, and tabular branches were individually removed to quantify their marginal contribution, we performed ablation experiments on the RF model.
The evaluated ablation configurations and their corresponding performance impacts are summarized in Table 4. The ablation variants considered were as follows:
Table 4. Ablation performance for the Random Forest model.

Ablation 1. No TROPOMI NO2 (satellite column removed)
Ablation 2. No meteorology (ERA5 variables removed)
Ablation 3. No PBLH
Ablation 4. No spatial features (lat/lon)
Ablation 5. No temperature
Full model (all predictors)
Consistent with AQNet’s ablations, which showed that removing Sentinel-2 produced the single largest degradation in R2, our results confirm TROPOMI tropospheric NO2 as the dominant predictor, with meteorology (especially PBLH) as the second-most important driver.
2.9. Sensitivity Analysis and Uncertainty Assessment
A comprehensive sensitivity analysis was performed to evaluate the robustness of the methodological framework and quantify uncertainty arising from (i) assumptions in tropospheric column height, (ii) meteorological predictors derived from ERA5, and (iii) the conversion between volumetric (ppm) and mass-based (µg/m3) NO2 concentrations. This procedure follows established approaches in satellite validation, AMF characterization, urban atmospheric modeling, and machine-learning-based NO2 estimation [4,5,6,10,11,12,14,15,16,18,19,26,28,29].
All reported concentrations include an explicit uncertainty term (±error), consistent with error-propagation practices recommended. The conversion of tropospheric NO2 column densities (mol/m2) into volume-based concentrations (mol/m3) requires an assumed tropospheric column height. Although a nominal value of 7 km was adopted in accordance with Sentinel-5P specifications and mid-latitude climatological profiles [4,5,6,13,18], Mexico City’s atmospheric structure is highly variable due to its altitude, topography, and frequent thermal inversions [1,2,7]. To evaluate structural dependence, four alternative heights were tested: 5 km, 7 km (baseline), 10 km, and 12 km. These sensitivity bounds are consistent with the role of vertical-profile assumptions and AMF-related uncertainty in satellite NO2 retrieval and validation workflows [5,6,18,29].
2.9.1. Sensitivity to Tropospheric Column Height
The conversion of tropospheric NO2 column densities (mol/m2) into volume-based concentrations (mol/m3) requires an assumed tropospheric column height. Although a nominal value of 7 km was adopted in accordance with Sentinel-5P specifications and mid-latitude climatological profiles [4,5,6,13,18], Mexico City’s atmospheric structure is highly variable due to its altitude, topography, and frequent thermal inversions [1,2,7]. To evaluate structural dependence, four alternative heights were tested: 5 km, 7 km (baseline), 10 km, and 12 km.
The results demonstrate substantial sensitivity (Table 5), consistent with reported uncertainties in vertical profile assumptions and AMF retrievals for TROPOMI and ground-based DOAS measurements [5,6,18,29]. The corresponding concentration curves are illustrated in Figure 6.
Atmosphere 17 00037 g006
Figure 6. Sensitivity of surface-level NO2 estimates to changes in tropospheric column height. Source: Author’s own elaboration based on data processed with Python.
Table 5. Sensitivity of the mol/m2 → µg/m3 conversion to variations in tropospheric column height.

Variations in column height introduce significant structural uncertainty and represent the most sensitive element of the conversion process. Reduced-height scenarios (≤5 km) lead to systematic overestimations, whereas expanded-height scenarios (≥10 km) tend to attenuate pollutant magnitude.
These variations are consistent with structural uncertainties observed in tropospheric retrievals and AMF calculations [5,6,18,29].
2.9.2. Sensitivity to Meteorological Predictors
Meteorological parameters influence NO2 dispersion, optical depth, and vertical mixing, particularly in high-altitude megacities such as Mexico City [1,2,7,23]. To assess model robustness, two perturbation strategies were applied:
(A)
Replacement of ERA5 predictors with ERA5-Land, reflecting structural differences between reanalysis products [28].
(B)
Stochastic ±1σ perturbations to temperature, pressure, wind speed, and PBLH, following methodologies used in machine learning atmospheric modeling [11,15,31,32].
Table 6 and Figure 6 summarize the model’s sensitivity to perturbations applied to the ERA5 meteorological predictors. Overall, the results show that the Random Forest model is relatively stable, but its performance does respond differently to variations in specific atmospheric variables.
Table 6. Model sensitivity to variations in ERA5 meteorological estimators.

Table 6 evaluates how sensitive the model is to different meteorological perturbations by measuring how much the error (ΔRMSE) increases when each variable is altered.
ERA5 → ERA5-Land (ΔRMSE = 3.1374):
Replacing the standard ERA5 predictors with ERA5-Land leads to a substantial increase in model error. This indicates that structural differences between the two reanalysis datasets have a meaningful impact on NO2 estimation.
Temperature (t2m) (ΔRMSE = 2.5589):
Perturbing temperature produces a moderate increase in error, suggesting that thermal conditions influence the model’s representation of NO2 dynamics, but not as strongly as wind or dataset substitution.
Pressure (sp) (ΔRMSE = 1.5734):
Surface pressure also results in moderate sensitivity. Changes in pressure slightly affect air density and vertical stability, resulting in noticeable but not dominant changes in the model output.
Wind (ΔRMSE = 4.5497):
Wind shows the largest increase in error among all predictors. This indicates that horizontal advection and turbulence play a major role in determining NO2 transport and dispersion, making wind the most influential meteorological factor in the model.
PBLH (ΔRMSE = 1.5571):
Although the numerical value is moderate, PBLH is classified as the dominant driver because variations in the planetary boundary layer directly determine the depth available for pollutant mixing. Even small perturbations can significantly affect near-surface NO2.
The sensitivity of the Random Forest model to perturbations in meteorological predictors is illustrated in Figure 7, which shows the relative changes in model error associated with variations in temperature, pressure, wind speed, and planetary boundary layer height.
Atmosphere 17 00037 g007
Figure 7. Sensitivity to Meteorological Predictors. Source: Author’s own elaboration based on data processed with Python.
These impacts agree with those reported for megacity-scale NO2 retrieval modeling in China, Europe, and North America [15,25,30,31].
2.9.3. Sensitivity to ppm–µg/m3 Conversion Factors
The conversion from volumetric concentration (ppm) to mass concentration (µg/m3) depends on temperature, pressure, and gas density. Its sensitivity has been noted in atmospheric chemistry and exposure assessment literature [1,17,19]. Due to Mexico City’s high elevation (~2240 m), non-standard atmospheric conditions significantly modify NO2 density and thus the ppm–µg/m3 conversion factor [2,7,23]. To quantify the impact of thermodynamic variability, three representative atmospheric cases were evaluated. The corresponding conversion factors, relative deviations from standard conditions, and associated uncertainty levels are summarized in Table 7.
Table 7. Sensitivity of the ppm → µg/m3 Conversion Under Alternative Atmospheric Conditions.

Three thermodynamic cases were evaluated:
These ranges match previously documented variability in NO2 density under changing thermodynamic conditions [13,17,19].
The variability of the ppm–µg/m3 conversion factor for NO2 under standard, mean, and extreme thermodynamic conditions is illustrated in Figure 8, highlighting the sensitivity of mass-based concentration estimates to changes in temperature and pressure.
Atmosphere 17 00037 g008
Figure 8. Conversion factors from parts per million (ppm) to micrograms per cubic meter (µg/m3) for nitrogen dioxide (NO2) under different thermodynamic conditions. The blue column represents standard atmospheric conditions (298 K, 1 atm), the green column corresponds to mean atmospheric conditions representative of Mexico City (~2240 m above sea level), accounting for reduced pressure and temperature effects, and the red column denotes extreme thermodynamic conditions. The figure illustrates the sensitivity of the ppm–µg/m3 conversion factor to temperature and pressure variability, highlighting the potential uncertainty introduced when applying standard-condition assumptions in high-altitude urban environments. Source: Author’s own elaboration based on data processed with Python.
2.9.4. Representation of Measurement Uncertainty (±Error)
To ensure methodological transparency and reproducibility, all NO2 values reported in this study are expressed together with their corresponding measurement uncertainty. This applies to values derived from surface observations, satellite retrievals, or Random Forest predictions. We use the notation value ± error. This convention follows recommended practices for atmospheric data processing, error propagation, and satellite–ground validation frameworks applied in tropospheric NO2 research [5,6,18,29]. Building on this convention, we now describe the approach used to quantify uncertainty across the various data sources employed.
For surface NO2 observations obtained from the RAMA, uncertainty was quantified as: [describe method below]. The next section outlines the procedure used for this quantification.
NO2,obs=NO2±σobs
(11)
where σobs represents the standard deviation of hourly values aggregated into daily means. This variability reflects short-term atmospheric processes such as turbulent diffusion, boundary layer fluctuations, and photochemical dynamics, which collectively contribute to intra-day concentration dispersion [7,13,19]. The resulting value, therefore, characterizes both the magnitude and natural temporal heterogeneity of surface-level NO2.
For model-derived estimations, uncertainty was represented as:
NO2,model=𝑦̂±σmodel
(12)
where denotes the Random Forest prediction and σmodel corresponds to the spread of the residuals. This statistical dispersion was estimated using the model’s cross-validated root mean square error (RMSE) and mean absolute error (MAE). These metrics are widely used in machine-learning-based NO2 downscaling and atmospheric modeling studies [11,15,30,31]. They encapsulate intrinsic uncertainty related to algorithmic learning, predictor variability, and structural differences between satellite-derived and surface-measured pollutant concentrations.
Uncertainty derived from meteorological predictors was incorporated through perturbation experiments in which key atmospheric variables were modified using ERA5 and ERA5-Land datasets. Similarly, variability in the ppm–µg/m3 conversion factor was expressed as a function of temperature- and pressure-dependent thermodynamic conditions, which can produce deviations ranging from mild to substantial depending on atmospheric state [1,17,19].
Finally, the total propagated uncertainty for each estimate was computed using quadratic error summation:
σtotal=σ2column+σ2meteo−−−−−−−−−−−−√+σ2conversion+σ2model
(13)
This approach is consistent with retrieval and AMF uncertainty propagation commonly used in the validation of TROPOMI tropospheric NO2 products [5,6,18,29]. The final reported concentrations, therefore, incorporate the combined effects of column-height assumptions, meteorological variability, conversion-factor sensitivity, and model residuals, providing a comprehensive representation of measurement uncertainty across all stages of the methodological workflow.
Table 8 summarizes the uncertainty associated with the observational dataset and the Random Forest model. The observed NO2 concentrations have a mean of 38.45 µg/m3 and substantial day-to-day variability (±23.97 µg/m3), reflecting the characteristic temporal fluctuations of urban pollution, influenced by traffic intensity, meteorology, and boundary layer dynamics. Predicted values show an almost identical mean (38.35 ± 24.55 µg/m3), indicating that the model accurately reproduces not only the central tendency but also the pollutant’s natural variability.
Table 8. Summary of measurement and model uncertainty expressed as ± error.

The model performance metrics express uncertainty as the statistical dispersion of errors. The RMSE (5.52 ± 3.35 µg/m3) and MAE (4.38 ± 3.35 µg/m3) fall within expected ranges for machine learning NO2 downscaling applications, demonstrating stable performance even under meteorological variability. The bias remains nearly zero (−0.10 ± 5.52 µg/m3), confirming the absence of systematic over- or underestimation. Together, these results indicate that uncertainty is well quantified and does not degrade the integrity of the model predictions, supporting their use for urban air quality assessment.
Figure 9 illustrates the relationship between observed and predicted surface-level NO2 concentrations, incorporating measurement uncertainty through horizontal and vertical error bars. Each white point represents an individual daily observation–prediction pair across all RAMA stations, while the gray envelope displays the propagated uncertainty (±error) associated with both observational variability and model residual spread. The 1:1 reference line (black dashed) indicates perfect agreement between observations and predictions. The close clustering of points around this line, with no systematic divergence at either low or high concentrations, demonstrates that the Random Forest model reproduces the magnitude and distribution of surface NO2 with high fidelity. The symmetry and narrow width of the error envelopes further confirm that uncertainty is balanced and does not introduce directional bias. This representation highlights the robustness of the modeling framework under diverse atmospheric conditions and supports the reliability of the downscaled NO2 estimates.
Atmosphere 17 00037 g009
Figure 9. Observed vs. predicted NO2 concentrations (µg/m3) obtained from the Random Forest model, including 1:1 line. Values represent surface-level NO2 across all RAMA stations during 2024. Source: Author’s own elaboration based on data processed with Python.
3. Results
3.1. Data Description
From a total of 4026 original records, 3246 data points were retained after data cleaning. Higher NO2 concentrations were observed at central urban stations (CCA, MER, PED), while lower values were found in peripheral or elevated stations (TAH, UIZ), reflecting known emission and dispersion patterns within Mexico City.
Figure 10 shows the geographic distribution of the RAMA stations used in this study.
Atmosphere 17 00037 g010
Figure 10. Map showing the location of RAMA stations. Source: Author’s own elaboration based on data processed and visualized in QGIS (v.3.34 Prizren) [27].
3.2. Performance of the Random Forest Downscaling Model
The Random Forest (RF) model demonstrated strong predictive performance for reconstructing surface-level NO2 concentrations across the Mexico City Metropolitan Area. The model achieved R2 = 0.972, RMSE = 3.81 µg/m3, and MAE = 2.91 µg/m3, indicating excellent agreement between predicted and observed concentrations. The scatterplot in Figure 11 shows a dense clustering of points around the 1:1 line, confirming the robustness of the downscaling framework.
Atmosphere 17 00037 g011
Figure 11. Observed vs. Predicted plot for the Random Forest model applied to the estimation of surface NO2 concentrations in Mexico City during 2024. The graph shows the ideal 1:1 line (red dashed) and the points corresponding to validated observations, indicating robust model performance with R2 = 0.972, RMSE = 3.81 µg/m3, MAE = 2.91 µg/m3, and Bias = 0.060 µg/m3. Source: Author’s own elaboration based on data processed with Python.
The model successfully reproduced expected spatial gradients, capturing higher concentrations along major traffic corridors and industrial zones, and lower levels in peripheral regions. Temporal behavior was also consistent with diurnal and seasonal patterns recorded by the RAMA.
GroupKFold cross-validation further validated the model’s generalization across stations, ensuring that performance did not depend on overlap between the training and validation sets (Table 9).
Table 9. Cross-Validation (GroupKFold) Results for the Random Forest Model.

These results confirm the suitability of the Random Forest model as a statistical downscaling tool, capable of generating high-resolution maps (≤1 km) from lower-scale satellite products (10–100 km). Furthermore, its strong performance suggests that this approach can be applied to other metropolitan regions with complex topographic and emission structures, strengthening validation strategies and complementing traditional atmospheric monitoring networks [25,26].
We used GroupKFold cross-validation to assess the Random Forest model’s performance in various settings. This method groups data by monitoring station, ensuring that information from each station appears only in either the training or validation set, but not in both. This helps us assess how well the model can predict at new locations where no data were collected.
These results confirm that the RF model is a reliable downscaling tool capable of generating high-resolution (≤1 km) NO2 fields from lower-resolution satellite inputs.
3.3. Statistical Comparison Between Satellite and Ground-Based Observations
The comparison between satellite-derived and surface-based NO2 concentrations shows strong temporal coherence between the two measurement sources. As illustrated in Figure 3 and Figure 4, the time series of NO2 from Sentinel-5P/TROPOMI and the RAMA exhibit highly similar daily patterns, with coincident concentration peaks during periods of intensified vehicular activity and meteorological stagnation. This alignment reflects the shared sensitivity of both systems to short-term atmospheric dynamics that modulate pollutant accumulation and dilution in the Mexico City basin [13,18].
Statistical analysis confirms a close correspondence between the two datasets. The annual mean NO2 concentration measured at RAMA stations was 42.8 µg/m3 (±27.5 µg/m3), whereas the downscaled Sentinel-5P estimate produced a mean of 41.9 µg/m3 (±24.8 µg/m3). These differences fall within the typical variability associated with surface–column comparisons reported for urban monitoring networks worldwide [13,19]. The Pearson correlation (r > 0.90) indicates a robust linear relationship, consistent with previous evaluations of TROPOMI retrieval quality in densely populated regions [18,33,34,35].
The mean bias was minimal (+0.06 µg/m3), demonstrating extremely close agreement between satellite and ground-based observations. This small positive shift confirms a slight satellite overestimation that remains negligible compared to the natural variability of NO2. Bias magnitudes of this order are fully consistent with those reported for other megacities, where satellite–surface differences generally remain within ±10% due to inherent algorithmic and meteorological uncertainties [13,17].
Taken together, these results confirm that the processed Sentinel-5P dataset can be reliably applied for high-resolution urban NO2 assessment in Mexico City after implementing bilinear interpolation and unit conversion procedures.
3.4. Comparison Between Satellite Validation and Machine Learning Model
Comparing results from the direct validation of Sentinel-5P/TROPOMI satellite data (a satellite instrument that measures atmospheric trace gases) with outputs from the Random Forest Regressor model (a type of machine learning algorithm) reveals improvements made by statistical downscaling (the process of increasing resolution using statistical techniques) and the integration of multisource data (data collected from various sources).
First, direct satellite validation showed a strong correlation between tropospheric NO2 columns and RAMA surface measurements, with an R2 of 0.920, RMSE of 6.80 µg/m3, and MAE of 4.55 µg/m3 (Figure 2). This demonstrates strong temporal and spatial correspondence between the two sources. However, limitations remain due to the satellite sensor’s vertical resolution, cloud interference, and local variability, which are not captured at the observation scale (~7 × 3.5 km).
Building on these findings, after applying the Random Forest model, the results improved significantly. The model achieved an R2 of 0.972, an RMSE of 3.81 µg/m3, an MAE of 2.91 µg/m3, and a near-zero bias of 0.06 µg/m3 (Table 2). This substantial improvement confirms the model’s ability to learn non-linear relationships between predictors (satellite, meteorological, and surface variables) and observed NO2. It overcomes the limitations of linear interpolation and reduces residual dispersion.
Furthermore, from a physical standpoint, the machine learning model successfully captures local fluctuations associated with mobile sources (vehicular traffic), atmospheric stability, and urban morphology. These are factors that cannot be resolved at the satellite scale. This behavior is consistent with previous findings. Machine learning algorithms have been shown to reduce pollutant estimation errors by 30% to 60% compared to traditional interpolation or linear adjustment methods [24,25].
This improved performance is illustrated in Figure 11, which visually shows the increased accuracy of the Random Forest model compared with direct satellite validation. The higher density of points along the 1:1 line indicates an almost perfect correspondence between predicted and observed values, evidencing the model’s effectiveness in reconstructing surface-level concentrations.
In summary, the progression from satellite validation to Random Forest modeling demonstrates how the approach provides a reliable baseline for regional monitoring, while also extending coverage to urban and local scales. This enables the continuous spatial characterization of NO2 without the need for ground-based instruments and provides a strategic tool for air quality management in cities with complex topography and limited monitoring, such as Mexico City.
Building upon this foundation, Figure 12 displays the annual average NO2 concentration for 2024, derived from validated and processed data in QGIS.
Atmosphere 17 00037 g012
Figure 12. Average annual concentration of NO2 (2024). Source: Author’s own elaboration based on data processed and visualized in QGIS (v.3.34 Prizren).
3.5. Integration of Baselines, Ablation, and Comparison with AQNet
To contextualize model performance, the RF model was benchmarked against AQNet, a multimodal deep learning architecture integrating Sentinel-2, Sentinel-5P, and tabular inputs. AQNet reports R2 = 0.685 for its baseline configuration and 0.728–0.755 when fine-tuned. In contrast, the RF model achieved R2 = 0.972, outperforming both AQNet versions in R2, RMSE, and MAE.
Ablation experiments quantified each predictor group’s contribution:
No TROPOMI: R2 = 0.816 → largest accuracy decline, confirming that satellite-derived NO2 provides essential spatial structure.
No Meteorology: R2 = 0.887 → underscores the role of ERA5 fields in capturing atmospheric variability.
No PBLH: R2 = 0.912 → reflects the importance of boundary layer dynamics.
This is demonstrated by the result when coordinates are omitted (R2 = 0.958), indicating that spatial structure is already embedded in satellite and meteorological predictors.
Feature-importance scores further highlighted that TROPOMI NO2, PBLH, temperature, and surface pressure are the strongest predictors, while latitude and longitude contribute marginally.
Together, these results demonstrate that classical ensemble learning—when combined with high-quality local monitoring and meteorological data—can outperform deep learning architectures designed for broader, heterogeneous domains.
3.6. Model Evaluation Incorporating Uncertainty
The Random Forest regression model demonstrated strong predictive performance for estimating surface-level NO2. The model achieved R2 = 0.9196, RMSE = 6.80 µg/m3, MAE = 4.55 µg/m3, and Bias = 0.20 µg/m3, reflecting excellent agreement between predicted and observed concentrations across diverse meteorological and emission conditions.
Building on these metrics, Table 5 incorporates the corresponding measurement and model uncertainties (represented as ± SD). Observed NO2 exhibited a mean of 38.45 ± 23.97 µg/m3, indicating substantial temporal variability inherent to urban pollution influenced by traffic density, atmospheric stability, and boundary layer dynamics. Predicted NO2 values closely matched this distribution (38.35 ± 24.55 µg/m3), demonstrating that the model successfully reproduced not only the magnitude but also the variability of the pollutant.
Model error diagnostics expressed with uncertainty (RMSE = 5.52 ± 3.35 µg/m3, MAE = 4.38 ± 3.35 µg/m3) align with values reported for similar downscaling frameworks in international studies [10,11,14,25]. The nearly zero bias (−0.10 ± 5.52 µg/m3) confirms the absence of systematic distortion.
Figure 9 visualizes the relationship between observed and predicted NO2, displaying both horizontal (observational) and vertical (model) error bars. The tight clustering around the 1:1 line demonstrates high predictive fidelity, while the symmetrical error envelopes indicate balanced uncertainty without directional bias. Together, these elements confirm that the modeling approach remains robust even in the face of the inherent uncertainties in meteorological conditions, vertical profile assumptions, and unit conversions.
3.7. Spatial Distribution of NO2 Incorporating Model-Derived Uncertainty
Building on the validated predictive performance, Figure 11 shows the spatial distribution of annual mean NO2 concentrations across Mexico City for 2024. The downscaled map reveals expected spatial heterogeneity. Higher concentrations occur along major road corridors, in industrial zones, and in densely populated central areas. Lower values appear in the periphery and elevated zones. Here, atmospheric mixing and reduced local emissions contribute to dispersal.
TROPOMI retrievals have intrinsic uncertainties related to air mass factor (AMF) assumptions, vertical mixing, and thermodynamic conditions [5,6,29]. As described in Section 2.5, propagating these uncertainties ensures the mapped concentrations reflect realistic confidence ranges. Applying propagated uncertainty (σ_total) to each prediction allows the spatial representation to include atmospheric, conversion, and model-related variability. This strengthens the reliability of the resulting surface-NO2 fields [5,6,19,29].
The spatial patterns produced clearly reflect the established emission dynamics and topographic limitations of the Mexico City basin. High NO2 levels in central and northeastern sectors are a direct result of dominant traffic flows, industrial activity, and restricted ventilation corridors. These results demonstrate the effectiveness of integrating satellite products and machine learning downscaling to produce spatially continuous, uncertainty-aware pollution maps that directly support environmental management and health-impact decisions.
4. Discussion
4.1. Interpretation of Random Forest Performance and Downscaling Accuracy
The Random Forest (RF) model exhibited strong predictive skill (R2 = 0.972; RMSE = 3.81 µg/m3; MAE = 2.91 µg/m3), confirming that statistical downscaling based on integrated satellite, meteorological, and surface observations can accurately reconstruct surface-level NO2 concentrations in complex urban regions. This behavior aligns with previous research highlighting the effectiveness of machine-learning- and ensemble-based approaches for pollutant estimation in megacities with strong spatiotemporal variability [8,10,11,25].
The model successfully captured the sharp spatial gradients characteristic of Mexico City, driven by traffic density, topographical constraints, and meteorological interactions, as described in detail in foundational studies of the region’s air quality dynamics [2,7]. The strong performance also reflects the robustness of ensemble methods such as Random Forest, whose capacity to aggregate multiple decision trees enhances generalization and mitigates overfitting [26].
4.2. Comparison with AQNet and Implications for Model Complexity
Benchmarking AQNet highlights the tradeoff between model complexity and data features. Although AQNet uses a multimodal deep learning framework, its reported R2 (0.685–0.755) is lower than the RF accuracy in Mexico City.
This result supports earlier evidence that deep learning models do not systematically outperform classical methods when applied to localized, high-resolution datasets, especially in cities with dense monitoring networks and well-defined meteorological regimes [8,11,14,25]. Ensemble methods such as RF can more efficiently leverage structured datasets with low noise and consistent spatial–temporal relationships.
Thus, the results underscore that model complexity must be aligned with data density, representativeness, and spatial domain, as previously emphasized in machine learning studies for China, Brazil, and Europe [16,25,36].
4.3. Interpretation of Ablation Study Results
Ablation experiments revealed the dominant role of TROPOMI NO2 in defining the spatial structure of surface NO2 fields. Removing this predictor produced the largest drop in performance (R2 = 0.816), consistent with validation studies demonstrating a strong relationship between tropospheric NO2 columns and surface concentrations when retrievals are corrected for air mass factor (AMF) uncertainties and vertical mixing effects [5,6,13,18,29].
Meteorological variables also proved essential: eliminating ERA5 fields reduced model accuracy to R2 = 0.887, confirming the crucial role of boundary layer dynamics, atmospheric stability, and circulation patterns in shaping pollutant accumulation in the Mexico City basin [2,13,36]. Removing PBLH produced a moderate decline (R2 = 0.912), reflecting its known influence on pollutant dilution and vertical confinement [1,28].
The minimal effect of removing spatial coordinates (R2 = 0.958) suggests that spatial structure is already embedded within satellite and meteorological predictors—a pattern consistent with other machine learning downscaling frameworks reported in the literature [10,11,25,30].
4.4. Interpretation of Variable Importance and Atmospheric Processes
The variable-importance analysis reinforces the atmospheric mechanisms governing nitrogen dioxide (NO2) behavior. The TROPOspheric Monitoring Instrument (TROPOMI) NO2 emerged as the most influential predictor, confirming its capacity to capture spatially coherent emission patterns and regional-scale transport effects, as documented in prior satellite-based NO2 assessment studies [4,5,13].
Meteorological predictors, including planetary boundary layer height (PBLH), temperature, and surface pressure, followed in importance, reflecting their impact on chemical reactivity, atmospheric dispersion, and boundary layer height variability [1,2,28]. These findings mirror results from ensemble and hybrid machine learning models applied to China and North America, where meteorology consistently ranks among the highest drivers of surface-level nitrogen dioxide (NO2) [14,18,25,30].
Together, these variable interactions demonstrate that the random forest (RF) model learned physically meaningful relationships, effectively integrating vertical information from satellite retrievals and dynamic processes from the European Centre for Medium-Range Weather Forecasts Reanalysis (ERA5) to reconstruct surface concentrations.
4.5. Implications for Urban Air Quality Monitoring and Management
The findings presented here have significant implications for air quality assessment in metropolitan regions. The RF-based downscaling approach yields high-resolution NO2 fields that preserve intraurban gradients and incorporate uncertainty propagation, supporting exposure assessment and emission hotspot detection. These strengths are particularly valuable for cities such as Mexico City, where complex topography and uneven station distribution limit the representativeness of surface networks [2,7].
Building on these implications, the successful integration of Sentinel-5P with machine learning demonstrates the potential of satellite-based monitoring for regions with sparse ground instrumentation—consistent with emerging recommendations to leverage satellite data to improve urban air quality equity and coverage [34].
4.6. Strengths, Limitations, and Future Research
A major strength of this study lies in demonstrating that classical ensemble learning can, in certain contexts, outperform advanced multimodal deep learning architectures—particularly in data-rich, locally calibrated urban environments. By integrating meteorological dynamics (ERA5), validated satellite retrievals (Sentinel-5P), and high-frequency surface observations (RAMA), the model’s robustness is enhanced. This approach aligns with prior research that combines satellite and machine learning predictors for NO2 estimation [10,11,16,25].
Despite these strengths, limitations persist. The daily temporal resolution of TROPOMI restricts analyses to a single overpass, and retrieval accuracy is sensitive to AMF assumptions, cloud cover, and vertical profile uncertainties, as extensively documented in validation studies [5,6,13,29]. Additionally, ERA5 reanalysis may not fully capture microscale circulation patterns in urban canyons [28].
To address these limitations and extend this research, future work should explore (i) temporal deep learning architectures, (ii) multi-pollutant modeling (PM2.5, O3), (iii) cross-city generalization tests, and (iv) integration with high-resolution urban meteorological models, as recommended in recent air quality modeling literature [8,16,27,37].
5. Conclusions
The results of this study demonstrate that the Random Forest (RF) downscaling framework is a robust and effective tool for estimating surface-level NO2 concentrations in complex urban environments such as the Mexico City Metropolitan Area. The model successfully reproduced both spatial gradients and temporal variability, achieving high agreement with RAMA observations and outperforming more complex deep learning architectures such as AQNet in this data-rich, locally calibrated context. These findings confirm that ensemble-based approaches, when supported by high-quality surface, meteorological, and satellite datasets, can provide reliable and computationally efficient alternatives for urban air quality assessment.
The methodology proved resilient to perturbations in structural assumptions—including tropospheric column height, meteorological drivers, and thermodynamic conversion factors—as evidenced by the sensitivity analysis. This robustness reinforces the value of integrating satellite retrievals (Sentinel-5P/TROPOMI), reanalysis meteorological fields (ERA5), and surface monitoring data within a transparent framework that explicitly accounts for uncertainty propagation. Such consistency is essential in high-altitude basins like Mexico City, where atmospheric dynamics strongly modulate pollutant dispersion.
A key contribution of this study is demonstrating the value of downscaling satellite-derived tropospheric NO2 columns into surface-level concentrations with high spatial resolution and uncertainty-aware outputs. This capability allows local and regional authorities to extend coverage beyond existing monitoring networks, identify emission hotspots, support exposure assessments, and guide regulatory planning where station density is insufficient. The approach complements the RAMA by providing spatial continuity and improving surveillance in areas lacking ground measurements.
The proposed methodology is replicable and scalable. Other Latin American metropolitan areas—many of which face similar challenges related to limited monitoring infrastructure, complex topography, and heterogeneous emissions—can adopt this architecture by integrating available satellite products, meteorological reanalyzes, and machine learning estimators. The transparency of the uncertainty framework facilitates transferability across regions with distinct climatic and emission regimes.
Finally, combining validated satellite imagery with machine learning predictions significantly expands the operational scope of environmental management systems. It enables more proactive, evidence-based urban air quality governance, supports public health protection, and contributes to broader climate and sustainability objectives across the region. The methodology can be extended in future work to other pollutants (e.g., PM2.5, O3, SO2) and to multi-pollutant forecasting models, reinforcing its relevance for long-term environmental planning and policy development.
Author Contributions
Conceptualization, Y.R.M.H.; Methodology, Y.R.M.H.; Investigation, Y.R.M.H.; Resources, Y.R.M.H.; Data curation, Y.R.M.H.; Writing—original draft, Y.R.M.H.; Writing—review & editing, Y.R.M.H., M.P.G., R.T.A.S., L.B.S., O.M.-C. and R.J.M.-B.; Supervision, M.P.G., R.T.A.S. and L.B.S. All authors have read and agreed to the published version of the manuscript.