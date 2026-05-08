John Douros1
, Henk Eskes1
, Jos van Geffen1
, K. Folkert Boersma1,2
, Steven Compernolle3
, Gaia Pinardi3
,
Anne-Marlene Blechschmidt4
, Vincent-Henri Peuch5
, Augustin Colette6
, and Pepijn Veefkind1
1Royal Netherlands Meteorological Institute, 3730 AE De Bilt, the Netherlands
2Meteorology and Air Quality group, Wageningen University, 6708 PB Wageningen, the Netherlands
3Royal Belgian Institute for Space Aeronomy (BIRA-IASB), Ringlaan 3, 1180 Uccle, Belgium
4
Institute of Environmental Physics, University of Bremen, IUP-UB, Otto-Hahn-Allee 1, 28359 Bremen, Germany
5European Centre for Medium-Range Weather Forecast (ECMWF), Sinfield Park, Reading, UK
6National Institute for Industrial Environment and Risks (INERIS), Verneuil-en-Halatte, France
Correspondence: John Douros (<john.douros@knmi.nl>)
Received: 20 May 2022 – Discussion started: 29 June 2022
Revised: 29 October 2022 – Accepted: 3 December 2022 – Published: 25 January 2023
Abstract. The Sentinel-5P TROPOspheric Monitoring Instrument (TROPOMI) instrument, launched in October 2017,
provides unique observations of atmospheric trace gases at a
high resolution of about 5 km, with near-daily global coverage, resolving individual sources like thermal powerplants,
industrial complexes, fires, medium-scale towns, roads, and
shipping routes. Even though Sentinel-5P (S5P) is a global
mission, these datasets are especially well suited to test highresolution regional-scale air quality (AQ) models and provide
valuable input for emission inversion systems.
In Europe, the Copernicus Atmosphere Monitoring Service (CAMS) has implemented an operational regional AQ
forecasting capability based on an ensemble of several European models, available at a resolution of 0.1◦ × 0.1◦
. In this
paper, we present comparisons between TROPOMI observations of nitrogen dioxide (NO2) and the CAMS AQ forecasts and analyses of NO2. We discuss the different ways
of making these comparisons and present quantitative results
in the form of maps for individual days, summer and winter
months, and a time series for European subregions and cities
between May 2018 and March 2021.
The CAMS regional products generally capture the finescale daily and averaged features observed by TROPOMI in
much detail. In summer, the comparison shows a close agreement between TROPOMI and the CAMS ensemble NO2 tropospheric columns with a relative difference of up to 15 %
for most European cities. In winter, however, we find a significant discrepancy in the column amounts over much of
Europe, with relative differences up to 50 %. The possible
causes for these differences are discussed, focusing on the
possible impact of retrieval and modeling errors. Apart from
comparisons with the CAMS ensemble, we also present results for comparisons with the individual CAMS models for
selected months.
Furthermore, we demonstrate the importance of the free
tropospheric contribution to the estimation of the tropospheric column and thus include profile information from
the CAMS configuration of the ECMWF’s (European Centre for Medium-Range Weather Forecasts) global integrated
model above 3 km altitude in the comparisons. We also show
that replacing the global 1◦ × 1
◦
a priori information in
the retrieval by the regional 0.1◦ × 0.1◦
resolution profiles
of CAMS leads to significant changes in the TROPOMIretrieved tropospheric column, with typical increases at the
emission hotspots up to 30 % and smaller increases or decreases elsewhere. As a spinoff, we present a new TROPOMI
NO2 level 2 (L2) data product for Europe, based on the replacement of the original TM5-MP generated global a priori profile by the regional CAMS ensemble profile. This
European NO2 product is compared with ground-based remote sensing measurements of six Pandora instruments of
the Pandonia Global Network and nine Multi-AXis Differential Optical Absorption Spectroscopy (MAX-DOAS) instruments. As compared to the standard S5P tropospheric NO2
Published by Copernicus Publications on behalf of the European Geosciences Union.
510 J. Douros et al.: S5P
column data, the overall bias of the new product for all except
two stations is 5 % to 12 % smaller, owing to a reduction in
the multiplicative bias. Compared to the CAMS tropospheric
NO2 columns, dispersion and correlation parameters with respect to the standard data are, however, superior.
1 Introduction
Nitrogen dioxide (NO2) is a key component of air pollution.
In combination with hydrocarbons and sunlight, NO2 produces ozone and also contributes to the formation of secondary aerosol, which has significant health effects. It is also
associated with acidification and the eutrophication of the environment. Monitoring of NO2 is therefore of major importance, and space-based observations complement dedicated
air quality (AQ) networks of surface air quality monitoring
stations in areas with poor coverage, also providing valuable
measurements above the surface which are otherwise very
scarce.
Monitoring of atmospheric NO2 from space has a long
history, starting with the launch of the Global Ozone Monitoring Experiment (GOME) instrument. More recently, a
new generation of space spectrometers was developed to provide observations at kilometer scale. The Sentinel-5P TROPOspheric Monitoring Instrument (TROPOMI) instrument
(Veefkind et al., 2012), launched in October 2017, is providing unprecedented detail and, thanks to its high spatial resolution, is able to identify emissions from individual sources.
A geostationary constellation of three satellites which
combines high resolution with diurnal sampling of NO2 is
also being set up, with the Geostationary Environment Monitoring Spectrometer (GEMS; Choi et al., 2018) instrument on
the Korean Aerospace Research Institute GEO-KOMPSAT2B satellite being the first one (launched in February 2020).
The other two are TEMPO over the U.S. (Zoogman et al.,
2017) and Sentinel-4 (Ingmann et al., 2012) over Europe.
The main mission objective for this new generation of satellites is the detailed monitoring of the spatial and temporal distribution of emissions. Apart from NO2, these instruments, including TROPOMI, measure a number of key air
pollutants, including CO (Borsdorff et al., 2018), HCHO
(De Smedt et al., 2018), and SO2 (Theys et al., 2017). In
the past few decades, satellite NO2 observations have been
compared with global (e.g., Noije et al., 2006) and regional
models (e.g., Huijnen et al., 2010a). Because of their high
resolution, this new generation of satellite instruments, like
TROPOMI, provides enough detail to contribute to air pollution and emission monitoring at the regional and local scales.
The European Copernicus Atmosphere Monitoring Service (CAMS; <https://atmosphere.copernicus.eu>, last access:
20 May 2022), provides operational daily analyses, forecasts,
and reanalyses of the atmospheric composition at the global
and regional scale. CAMS makes direct use of satellite atmospheric composition observations (including reactive gases
like ozone (Inness et al., 2019b), CO, and NO2, aerosol properties, and greenhouse gases), with a special focus on the
Copernicus Sentinel satellites. Combining models and satellite data using advanced data assimilation techniques leads
to daily analyses and reanalyses of concentrations and emissions, consistent with the observations in the literature (Inness et al., 2015, 2019a; Miyazaki et al., 2020a).
In 2020, the satellite observations of TROPOMI attracted
massive attention, both in science and in the media. As a positive side effect of the lockdown measures worldwide, several sectors have experienced strong reductions in activity
and emission levels (road traffic, air transport, and industry),
which induced considerable decreases in the levels of certain
pollutants over several regions of the globe (Gkatzelis et al.,
2021). In some cases, these decreases were clearly observed
from space (Bauwens et al., 2020; Ding et al., 2020; Sun et
al., 2021; Stavrakou et al., 2021). Also, within CAMS, dedicated studies have been performed to investigate the emission
(Guevara et al., 2021) and concentration (Barré et al., 2021)
changes in Europe, accounting for the variability introduced
by weather changes.
Satellite instruments like Ozone Monitoring Instrument
(OMI) and TROPOMI have clearly demonstrated the capability to measure detailed NO2 distributions on a near-daily
basis, but improving the quantitative aspects of the vertical
column uncertainties remains a major challenge. The absolute vertical column amount is influenced by the assumed
a priori profile shape, surface radiative properties, cloud aspects, free tropospheric NO2, and stratospheric NO2. All of
these aspects need to be accounted for. In particular, the
spatial resolution of the a priori is recognized as an important factor to improve the tropospheric column, and several
groups have developed regional satellite data products for
China, Europe, and the USA based on high-resolution regional air quality modeling systems (Lin et al., 2014; Liu et
al., 2021; M. Liu et al., 2020; Zhou et al., 2009; McLinden et
al., 2014; Griffin et al., 2019; Laughner et al., 2019).
The aim of this paper is to explore the different ways of
making comparisons between TROPOMI observations and
model results. We approach this from two different angles.
First, we present a comparison between the CAMS regional
ensemble and the TROPOMI NO2 observations for an extended measurement period (2018–2021), with a closer look
at specific days and months. Second, we present a novel
European TROPOMI level 2 (L2) NO2 product based on
NO2 a priori profiles of the CAMS regional AQ analyses,
which have a 10 times (or 100 times in terms of model
cell area) better spatial resolution than the global TM5-MP
model (Williams et al., 2017) which is used as a priori in
the operational retrieval. This new European TROPOMI NO2
product is then validated against European surface remote
sensing Multi-AXis Differential Optical Absorption Spectroscopy (MAX-DOAS) and Pandora instruments.
Geosci. Model Dev., 16, 509–534, 2023 <https://doi.org/10.5194/gmd-16-509-2023>
J. Douros et al.: S5P 511
2 The TROPOMI NO2 measurements
The TROPOspheric Monitoring Instrument (TROPOMI) is
the single instrument payload on the Sentinel-5P satellite,
which is one of the Sentinel instruments of the European
Copernicus Program dedicated to monitoring atmospheric
composition. TROPOMI is a spectrometer measuring in the
UV, visible, near-infrared, and shortwave infrared, which allows the retrieval of a large number of trace gases and aerosol
properties (Veefkind et al., 2012). The TROPOMI instrument is unique in several ways because it combines neardaily global coverage with a wide spectral range, footprints
of 3.5×5.5 km2
at nadir (since 6 August 2019 and 3.5×7 km2
before that) and a very large signal-to-noise ratio. Because
of the small footprints, TROPOMI is able to distinguish
medium-sized pollution sources such as cities, powerplants,
industrial complexes, major highways, individual fires, and
even individual large ships (Goldberg et al., 2019; Miyazaki
et al., 2020b; F. Liu et al., 2020; Georgoulias et al., 2020).
The operational TROPOMI NO2 product is described in
van Geffen et al. (2020), which focuses on the DOAS slant
column retrieval, van Geffen et al. (2022), which describes
the tropospheric vertical column retrieval and air mass factor aspects up to processor version 1.4.0, van Geffen et al.
(2022), which discusses the upgrade to version 2.2.0 on
July 2021, and Riess et al. (2022), which discusses the improvement in the cloud pressure product and how that improves NO2 air mass factors and retrievals. Users of the data
are advised to first consult the product README file (PRF;
Eskes and Eichmann, 2021) which provides a short introduction to the processor versions, data quality remarks, algorithm changes, and links to the relevant documentation and
routine validation. The product user manual (PUM; Eskes
et al., 2022) describes the content and use of the L2 data
files. The Algorithm Theoretical Basis Document (ATBD;
van Geffen et al., 2021) provides a detailed description of
the implementation of the NO2 retrieval.
As explained in the ATBD and in van Geffen et al. (2022),
the NO2 retrieval consists of three steps, namely spectral fitting, estimation of the stratospheric column, and computation
of the tropospheric air mass factor. Integrated in the retrieval
are daily forecast and analysis runs with the global TM5-
MP (Huijnen et al., 2010b; Williams et al., 2017) chemistry
transport model. The second step involves an assimilation
of the total columns of TROPOMI in TM5-MP to force the
modeled characteristics of the stratosphere to be consistent
with TROPOMI. The assimilation is set up in such a way
that the forcing happens predominantly in regions with low
boundary-layer pollution levels (ocean and remote land regions). In the third step, use is made of space–time co-located
TM5-MP NO2 tropospheric profiles to compute the tropospheric column. It is relevant to note that the assimilation step
does not distinguish between spread-out free-tropospheric
background NO2 and stratospheric NO2, and a possible freetropospheric bias in TM5-MP will translate to a background
bias in the retrieval of the tropospheric column (Dirksen et
al., 2011). Unfortunately, there is very little in situ observational (aircraft) data to validate the free troposphere, which is
one relevant aspect for which the retrieval may be improved.
For this work, we have processed the full TROPOMI
data record up to March 2021, based on the following versions of the processor (i.e., retrieval algorithm; see also the
PRF): the reprocessing dataset v1.2.2 from 30 April 2018 to
17 October 2018, the offline v1.2.0 from 17 October 2018
to 28 November 2018, the offline v1.2.2 from 28 November 2018 to 20 March 2019, v1.3.x from 20 March 2019 to
29 November 2020, and v1.4.0 from 29 November 2020 until
March 2021, inclusive. The changes introduced from processor v1.2.0 to v1.3.2 are relatively minor and do not have a
large impact on NO2.
Therefore, we consider the time series from April 2018
to October 2020 as being rather stable. The upgrade to version 1.4.0 on 29 November 2020 (for the offline product)
brought only one change, namely an update of the FRESCO
cloud retrieval, which led to an overall decrease in the effective cloud pressure of about 5 %. Because of the large sensitivity of the NO2 retrieval to this quantity, this resulted in
a considerable change and general increase in NO2 in the
more polluted regions (van Geffen et al., 2022; Riess et al.,
2022). The datasets were filtered with the “qa_value” quality
parameter provided in the data product, and only observations with a qa_value > 0.75 were kept to produce the results described below. This filtering choice can be seen as a
cloud mask, since it removes the cloud-covered scenes (with
a cloud radiance fraction > 0.5) and some more uncertain
retrievals.
The TROPOMI mission includes a routine validation effort (<http://mpc-vdaf.tropomi.eu>, last access: 20 May 2022)
with 3-monthly updates of the validation report for the operational products (Lambert et al., 2021). The main results
of the validation against MAX-DOAS, Pandora, and Système D’Analyse par Observations Zénithales (SAOZ) instruments is summarised in Verhoelst et al. (2021), although
the averaging kernel is not used in that work. For versions
1.2.x and 1.3.x, Lambert et al. (2021) find a negative bias
against surface-based remote sensing observations of the tropospheric column of −34 % on average against MAX-DOAS
and −24 % against Pandora total column observations in polluted regions. Note that especially the MAX-DOAS comparisons are sensitive to the NO2 vertical profile, and improvements in the comparison by up to 20 % are reported
when Sentinel-5P averaging kernels are used (Lambert et al.,
2021). Comparing TROPOMI versions 1.2.x and 1.3.x with
the OMI QA4ECV retrieval product (Boersma et al., 2018)
showed also that TROPOMI retrievals were lower than OMI,
especially over polluted regions (with large aerosol concentrations) and especially in winter (Lambert et al., 2021). In
Europe, TROPOMI NO2 from versions 1.2.x and 1.3.x are
about 3 %–20 % lower than OMI-QA4ECV in winter, but
the products are highly correlated (Lambert et al., 2021).
<https://doi.org/10.5194/gmd-16-509-2023> Geosci. Model Dev., 16, 509–534, 2023
512 J. Douros et al.: S5P
Table 1. The models involved in CAMS.
Model Institute Reference
IFS (compo) ECMWF Flemming et al. (2015)
ENSEMBLE Météo-France Marécal et al. (2015)
CHIMERE INERIS Menut et al. (2013)
DEHM Aarhus University Brandt et al. (2012)
EMEP Met.no Simpson et al. (2012)
EURAD-IM University of Cologne Memmesheimer et al. (2004)
GEM-AQ WUT Kaminski et al. (2008)
MATCH SMHI Robertson et al. (1999)
MOCAGE Météo-France Guth et al. (2016)
LOTOS-EUROS KNMI/TNO Manders et al. (2017)
SILAM FMI Sofiev et al. (2015)
These differences between OMI and TROPOMI are largely
attributed to differences in the cloud pressure retrievals and
thus, with version 1.4.0, the two products were much more
consistent, with the regional monthly mean observations
agreeing to within 10 %, and with version 2.2.0 agreeing to
within 5 % for the European region (Lambert et al., 2021).
To summarize, a negative bias in tropospheric NO2 of the
order of −30 % has been found in ground-based column observations in polluted regions, which is largely attributed to
systematic errors in the profile shapes, the retrieved cloud
pressure, and surface albedo used. Cloud-related biases in
versions 1.2.x and 1.3.x seem to show a strong seasonality,
from around −20 % in Europe in winter, to only small impacts in summer. With version 1.4.0, we observe an increase
in tropospheric NO2 columns of around 20 % in winter over
Europe and with version 2.2 between 10 % and 40 % (van
Geffen et al., 2022).
3 The CAMS European air quality forecasts and model
ensemble
The Copernicus Atmosphere Monitoring Service (CAMS)
is one of the six thematic services of the flagship European space program of Copernicus. CAMS was built to
provide the capacity to continuously monitor the composition of Earth’s atmosphere at global and regional scales
(Hollingsworth et al., 2008; <http://atmosphere.copernicus.eu>,
last access: 20 May 2022).
CAMS is comprised of two distinct atmospheric composition components for the global and regional scales. A global
forecast system is used to produce operational daily forecasts
of reactive gases, aerosols, and greenhouse gases across
the globe at a resolution of about 40 km. This is based on
the European Centre for Medium-Range Weather Forecasts
(ECMWF) Integrated Forecasting System (IFS), forming
the compo (which stands for composition) configuration of
the system, which integrates online a representation of the
relevant physicochemical processes. Analyses, based on the
assimilation of satellite observations of atmospheric composition and the subsequent forecasts, are produced twice a day
(Flemming et al., 2015; Eskes et al., 2015; Huijnen et al.,
2019). ECMWF’s 4-D data assimilation system for aerosol
and reactive gases is described in Inness et al. (2015, 2019a).
For NO2, the CAMS global system assimilates a number
of satellite retrievals, including GOME-2 and OMI (see
<https://confluence.ecmwf.int/display/CKB/CAMS%3A+>
Global+atmospheric+composition+forecast+data+ documentation#CAMS:Globalatmosphericcompositionfore
castdatadocumentation-Satelliteobservations, last access:
20 May 2022). The TROPOMI NO2 data assimilation
became operational in October 2021.
The CAMS regional production system for the European domain is operated by Météo-France (Marécal et
al., 2015) and provides daily 4 d forecasts and analyses,
for the day before, of the main air pollutants and pollen
species from seven (9 from October 2019 to May 2022
and 11 since May 2022) state-of-the-art European regional
atmospheric chemistry models (see <https://atmosphere>.
copernicus.eu/regional-air-quality-production-systems, last
access: 20 May 2022). An ensemble product (henceforth,
ENSEMBLE, which is used extensively in this paper) is calculated from the regional model outputs and is currently the
median of all individual models, but new ensemble processing methodologies have been tested and will replace the current one and become operationally available in 2022.
Both the 4 d forecasts and daily analyses for the previous
day are made available in an hourly temporal resolution and
a spatial resolution of 0.1◦ up to 5 km above the surface (at
0, 50, 250, 500, 1000, 2000, 3000, and 5000 m above the
surface). The ENSEMBLE up until October 2019 was calculated using the following seven regional models: CHIMERE,
EMEP, EURAD-IM, LOTOS-EUROS, MATCH, MOCAGE,
and SILAM. Since then, DEHM and GEM-AQ have also
been used (Table 1). All regional model data, plus the ENSEMBLE, are provided on a European domain of 25◦ W–
45◦ E, 30–70◦ N, up until 12 June 2019, when the northern
boundary was extended to 72◦ N, with a horizontal resolution
of 0.1◦ × 0.1◦
. Anthropogenic emissions used are the TNO
MACC-III (Kuenen et al., 2014) and CAMS-REG_AP/GHG
(Granier et al., 2019) emission inventories over Europe. Successive improved versions of the latter have been used over
the years.
All models are driven by the operational IFS meteorological forecasts (HIGHRES), which have a horizontal resolution
of about 9 km and use the gas and aerosol concentrations
from CAMS global as lateral boundary conditions, which
are intended to make the regional model output consistent
with the global model output (Douros et al., 2020). Any differences between individual models may thus be attributed
to different representations of the physical and dynamical
atmospheric processes, chemistry and aerosol dynamics, or
the natural emissions inside the domain. Moreover, regional
models are updated generally once per year, all at the same
time. This allows for models to keep up to date, very much
like it is done for Numerical Weather Prediction. A drawback
Geosci. Model Dev., 16, 509–534, 2023 <https://doi.org/10.5194/gmd-16-509-2023>
J. Douros et al.: S5P 513
Figure 1. The three ways of comparing the CAMS NO2 forecasts
with TROPOMI. In the top row, the TROPOMI tropospheric retrieval (a) is compared with the CAMS profiles multiplied by the
kernels (b). In the bottom row, the CAMS profile is used a priori in
the TROPOMI retrieval (c), and this is compared with the CAMS
vertical column (d). The third option is a direct comparison of the
TROPOMI and CAMS tropospheric columns (a, c), but this is suboptimal, since it depends on the TROPOMI a priori. The meaning
of all acronyms in blue is described in Sect. 4.1.
of this practice is that it introduces slight discontinuities that
are not connected with changes in weather or emissions.
The evaluation of the regional services is based on the
routine European AQ surface observations, operated by the
individual countries and collected by the European Environmental Agency (EEA; e.g., <https://regional.atmosphere>.
copernicus.eu/evaluation.php?interactive=cdf, last access:
20 May 2022). Apart from this, CAMS also has a dedicated validation activity for concentrations above the surface
(Douros et al., 2020). This activity includes also a comparison with satellite NO2 and MAX-DOAS remote sensing observations (Blechschmidt et al., 2018). An early comparison
of the CAMS ENSEMBLE with OMI tropospheric columns
is discussed in Huijnen et al. (2010a).
4 Intercomparison approach
4.1 Three approaches to compare model and satellite
observations
NO2 total column retrievals are implicitly dependent on an
a priori tracer profile. The retrieval algorithm accounts for
the fact that the sensitivity of the instrument is different at
different altitudes i.e., the sensitivity is higher in the free troposphere and lower in the boundary layer. This information
is encoded in the averaging kernel which is proportional to
the measurement sensitivity and depends on the viewing geometry, cloud properties, aerosols, and surface albedo (Eskes
and Boersma, 2003).
Based on these considerations, several possible approaches of comparing model output and satellite observations exist, which are presented in Fig. 1. Figure 1a indicates the standard TROPOMI retrieval, as provided in the
TROPOMI L2 data files, henceforth denoted as S5P. As explained in the TROPOMI PUM (Eskes et al., 2022), the a priori profiles x
tm5 in the retrieval may be replaced by any other
model NO2 profile information x
model, which is, in our case,
CAMS or x
cams, resulting in a new retrieved tropospheric
NO2 column V
trop,cams (Fig. 1c). The method makes use of
the tropospheric averaging kernel A
trop and the air mass factors M provided by the TROPOMI L2 data files, as follows
(Eskes et al., 2022):
V
trop,cams =
M
M0
V
trop
M0
(x
cams) = M(x
tm5)
X
l
A
trop
l
x
cams
l
/
X
l
x
cams
l
. (1)
Here, M(x
tm5) is the tropospheric air mass factor provided in
the TROPOMI product, depending on the TM5-MP a priori
profile x
tm5, and M0
(x
cams) is a new air mass factor computed
with the alternative model profile x
cams. The summation over
l is over the tropospheric model levels.
The tropospheric averaging kernel vector A
trop of the
TROPOMI product is obtained by scaling the total averaging kernel by M/Mtrop, where M is the total air mass factor,
and Mtrop is the tropospheric air mass factor (Eskes et al.,
2022). All elements of the kernel are set to zero above the
tropopause layer l
tm5
tp , or,
A
trop =
M
Mtrop A ,l <= l
tm5
tp
A
trop = 0 ,l > ltm5
tp .
(2)
All the above quantities are provided in the TROPOMI product.
We therefore also discuss three distinct ways of recomputing the TROPOMI tropospheric column using CAMS NO2
profiles by using the profile solely from the regional ensemble of CAMS, solely from the global CAMS NO2 model,
or the combined global–regional profile using IFS (compo)
above 3 km altitude and CAMS–regional below. These alternative TROPOMI products are indicated by the acronyms
S5P-R (R as in regional), S5P-G (G as in global) and S5PRG (RG as in regional–global), respectively (Fig. 1c). Please
note that all references to CAMS–regional in this section or
the following sections can refer to either the ENSEMBLE or
individual regional models and should be clearly indicated in
each case. The same goes for derived columns containing the
“-R” suffix, which indicates the use of either the ENSEMBLE or individual models.
The CAMS model simulation of the measured NO2 column, denoted as C
A in Eq. (3), is obtained by multiplying
the CAMS model partial column profile x
cams with the tropospheric averaging kernel A
trop, or
C
A =
X
l
A
trop
l
x
cams
l
. (3)
This equation requires a vertical interpolation between the
levels for which the model data are available and the
<https://doi.org/10.5194/gmd-16-509-2023> Geosci. Model Dev., 16, 509–534, 2023
514 J. Douros et al.: S5P
TROPOMI data product levels (in which the averaging kernel is defined), which should ideally conserve the total column amount. As above, we distinguish three different CAMS
profiles; so CAMS-A can be CAMS-R-A, CAMS-G-A, or
CAMS-RG-A ( Fig. 1b).
A direct comparison of the NO2 tropospheric column
as provided in the TROPOMI product (S5P) and a modelgenerated column would introduce extra uncertainties and
biases, as the TROPOMI tropospheric columns depend on
the retrieval a priori and therefore on the quality of the TM5-
MP profiles used. This comparison approach is depicted in
Fig. 1 with an orange arrow. The most common approach for
comparing models and satellite retrievals is the comparison
of the two upper boxes of Fig. 1 (upper green arrow). As
explained in Eskes and Boersma (2003), the relative comparison becomes independent of the a priori profile shape of the
TM5-MP model used in the S5P retrieval.
An equally valid comparison approach is the replacement
of the a priori profile used in the retrieval by the air quality model a priori and subsequent direct comparison with the
modeled tropospheric column (lower green arrow in Fig. 1).
In this way, any relative comparison also becomes independent of the a priori profile shape from the TM5-MP model,
since this is removed from the retrieval product. The vertical
model column can be seen as a multiplication with the identity matrix I. Hence, the notation CAMS-R-I, CAMS-G-I, or
CAMS-RG-I is used for this modeled vertical tropospheric
column (Fig. 1d).
4.2 Implementation of the comparisons
Proper temporal and spatial sampling of the satellite observations and model output fields is essential in order to minimize representativity errors during the comparison. To this
end, all available data were regridded to the CAMS regional
grid (see Sect. 3). In this process, source grids were either
the TROPOMI footprint (i.e., the native grid of TROPOMI,
which is different for each orbit), the IFS (compo) grid, or
the TM5-MP grid. See Table 2 for the characteristics of each
of those grids.
Horizontal regridding is performed by means of an areaweighted average of source cells that correspond to target
(i.e., CAMS–regional) cells. For example, a target grid cell
o containing retrieval columns yˆ
o
i will acquire the value
yˆo =
P
iwiyˆ
o
i
/
P
iwi
, where weights wi are given by the retrieval column pixel area. In the case of regridded TROPOMI
observations, these may be called superobservations, as typically about three TROPOMI observations are averaged to
construct one observation for a CAMS grid cell.
Moreover, to minimize spatial representativeness errors,
we imposed an additional constraint regarding the satellite
data, i.e., a value for a target grid cell was calculated and assigned only if the coverage of valid source data for this cell
were above 50 %. This is on top of the filtering based on the
quality assurance parameter qa_value > 0.75, following the
Table 2. Input data characteristics.
Input Horizontal Levels Temporal
resolution resolution
IFS (compo) 0.4◦ × 0.4◦ 137a 3 h
CAMS–regional 0.1◦ × 0.1◦ 8
b 1 h
TM5-MP 1◦ × 1
◦ 34 0.5 h
TROPOMI 3.5 × 5.5 km2 c 34d –
a There were 60 levels before 10 July 2019. b Number of sampling altitudes.
Individual models and the ENSEMBLE data have the exact same
characteristics. c Horizontal resolution at nadir and 3.5 × 7 km2 before
6 August 2019. d Levels of the averaging kernels.
suggestion of the TROPOMI PUM (Eskes et al., 2022). This
area-weighted regridding of a single TROPOMI orbit to the
target grid can be seen in Fig. 2. Intensive variables (temperatures, pressures, averaging kernels, tropopause layer index, etc.) are interpolated horizontally using bilinear regridding. Modeled fields were sampled in time at the satellite
overpass time over central Europe using the closest available
time, based on the temporal resolution of each data source
(see Table 2).
In the vertical, the approach followed was to transform all
available data in the TM5-MP vertical levels, i.e., the levels of the TROPOMI product averaging kernel. So, CAMS
regional model data were linearly interpolated to the TM5-
MP levels from the eight sampling altitudes (Table 2), while,
for the global model where data were available in the native model levels, data were interpolated in mass conservative fashion.
All integrations to columns were performed on the TM5-
MP vertical levels, and we consider the three possible options
mentioned in Sect. 4.1. The first one is taking into account
only the CAMS–regional ENSEMBLE (or, for that matter,
any individual regional model) for reconstructing the column. In this case, the last TM5-MP level considered was the
one which lies just below 5000 m above the surface, which
means that a large part of the free troposphere is not accounted for (concentration is assumed to be zero). The second option involves using only IFS (compo) data, where the
last TM5-MP level considered is the one assigned to the
tropopause, as provided in the form of the tropopause layer
index in the TROPOMI product. Finally, we also consider a
merger between CAMS–regional and IFS (compo) in the vertical, where we use the regional profile up to about 3000 m
above the surface and complement it with IFS (compo) data
up to the tropopause. All concentrations are converted to densities (molec. m−3
) based on temperature profiles provided
by TM5-MP (in the case of CAMS–regional data) and pressure profiles from either IFS (compo) or TM5-MP. Comparisons between CAMS and TROPOMI are presented for
several regions, indicated in Fig. 3, and for major European
cities using boxes of 7 × 5 (CAMS–regional) grid cells.
Geosci. Model Dev., 16, 509–534, 2023 <https://doi.org/10.5194/gmd-16-509-2023>
J. Douros et al.: S5P 515
Figure 2. TROPOMI retrieval field of orbit 3704 (one of the orbits on 1 July 2018), plotted on the native grid (a) for the Netherlands area,
compared to the regridded field in the CAMS regional grid (0.1◦ × 0.1◦
resolution) for the same retrieval (b).
Figure 3. Definition of the regions of interest for the calculation of
column comparison statistics.
5 Comparisons between TROPOMI and CAMS
By averaging the regridded maps of all TROPOMI orbits
and model data within a given period, we are able to perform comparisons of tropospheric columns for that period.
Note that the maps presented in the figures in this section do
not correspond to the whole CAMS regional domain of the
target grid, but are magnified to a more central part of the
European domain, and all figures include cells that contain
valid TROPOMI observations, based on the criteria defined
in Sect. 4.2. Moreover, regional modeled NO2 fields in this
section originate from the first forecast day and the near-realtime (NRT) analyses for the day before.
5.1 Comparisons for individual days and monthly
means
Maps of daily TROPOMI columns and CAMS model mean
tropospheric NO2 columns using CAMS-RG are given in
Figs. 4 and 5, for 26 July 2018 and 15 February 2019, respectively. Figure 4 follows the scheme of Fig. 1; thus, columns
with S5P, CAMS-RG-A, S5P-RG, and CAMS-RG-I are presented, while in Fig. 5 only S5P-RG and CAMS-RG-I are
shown. CAMS–regional data used in this section are the first
day forecasts. Based on an inspection of those maps which
are based on two largely cloud-free days over central Europe,
we can already draw some important conclusions regarding
how the two products compare. Most emission hotspots are
clearly identifiable in both S5P- and CAMS-RG-based maps.
This includes the large- and medium-sized cities and whole
areas with increased pollution burden, as in the Po Valley or
southwestern Germany. Advection characteristics also agree
qualitatively, such as the strong transport of NO2 from England, the Netherlands, Belgium, and Germany to the North
Sea on 15 February 2019 (Fig. 5). Differences, however, are
seen in the quantitative details, with the model-based maps
leading to longer and more pronounced plumes. This is quite
evident in the case of the Liverpool (UK) and English Channel areas (26 July) and in the North Sea (15 February). Some
hotspots seem to be absent altogether in the TROPOMI retrieval, for example, the powerplants in the Lusatia region
in eastern Germany, possibly related to inaccurate assumptions in the emissions used in the CAMS models (e.g., differences in activity during the examined days or in the emission injection characteristics). Ship tracks can be seen in both
TROPOMI and CAMS fields but are generally more prominent in the CAMS fields (e.g., in the Bay of Biscay or the
North Sea). TROPOMI also seems to indicate higher background values in summer.
Monthly averages of regridded column fields offer wider
spatial coverage and a qualitatively different view of the observed and modeled features. The maps in Fig. 6 present
the comparison of the mean TROPOMI tropospheric NO2
columns S5P with CAMS-RG-A for the months of July 2018
and January 2019. Similar to the daily fields, CAMS–
regional data in this section are also based on the first day
of the 4 d forecasts. CAMS columns appear to be capturing the observed locations of high NO2 columns well over
densely populated regions like the Benelux area, Po Valley,
and other large European cities. For July, absolute values at
the hotspots seem to be comparable, but background values
are higher in the case of S5P. The situation is considerably
different in January, where CAMS-RG-A columns are significantly higher over the hotspots. Naturally, these much higher
values also seem to affect through advection rural land areas
or even areas over the sea.
<https://doi.org/10.5194/gmd-16-509-2023> Geosci. Model Dev., 16, 509–534, 2023
516 J. Douros et al.: S5P
Figure 4. Comparison of S5P (a), CAMS-RG-A (b), S5P-RG (c), and CAMS-RG-I (d) columns, based on the scheme of Fig. 1, for
26 July 2018.
Figure 5. Comparison of S5P and CAMS-RG-A columns (Fig. 1c, d) for 15 February 2019. Please note the difference in the color bar scale
compared to Fig. 4.
5.2 Time series
Figure 7 depicts the time series of monthly mean S5P and
CAMS-RG-A vertical column densities for nine major European cities, while Fig. 8 shows the corresponding time series
for the domains of Fig. 3 from May 2018 to March 2021. For
this long time series, the CAMS–regional data utilized were
the NRT analyses, as this is the regional product used in the
European L2 TROPOMI product, as detailed in Sect. 6.
The spatial averaging required for the time series of
the cities (Fig. 7) was performed for 7 × 5 cell domains
(0.7◦ × 0.5◦
) for all the cities, which corresponds to areas of
roughly 70 × 50 km2
centered at the respective city centers.
This comparison reveals remarkably similar values between
the S5P and CAMS-RG-A columns for some of the cities
in southern Europe (Madrid, Rome, and Istanbul), while discrepancies are larger in most of the rest, especially in the
wintertime when CAMS-derived column densities almost always acquire higher values. The domain-averaged monthly
mean time series of Fig. 8 present a similar picture, where
comparison is much more favorable during the summertime,
but the two column densities differ substantially during the
wintertime in practically all of the examined domains.
5.3 Discussion of the CAMS-TROPOMI differences
The wintertime discrepancies identified in the previous sections may be due to uncertainties in both the satellite retrieval
(Lorente et al., 2017) (see also Sect. 2) and chemical transport modeling. Note, however, that the January fields presented above (Sect. 5.1) are unavoidably based on a much
fewer observations compared to the July ones due to increased cloud coverage, snow cover, and low solar zenith angles.
As mentioned before, TROPOMI validation indicates a
negative bias in tropospheric NO2 in polluted regions. Part
of this may be attributed to the (horizontal resolution of the)
global TM5-MP a priori, but in our comparisons, the averaging kernels are accounted for, which removes this source
of error. Furthermore, biases in versions 1.2.x and 1.3.x of
the retrieval algorithm seem to show a seasonality compared
Geosci. Model Dev., 16, 509–534, 2023 <https://doi.org/10.5194/gmd-16-509-2023>
J. Douros et al.: S5P 517
Figure 6. Monthly averaged S5P and CAMS-RG-A columns for July 2018 (a, b) and January 2019 (c, d).
Figure 7. Time series of monthly mean original TROPOMI columns (S5P; red) and the CAMS combined columns (CAMS-RG-A; blue),
with averaging kernels applied for nine major European cities. The retrieval algorithm versions used are as described in Sect. 2. The panels
are ordered according to the geographical location. Vertical axes are different for each city. Green vertical bars in July and November 2018
represent the model spread for those 2 months.
<https://doi.org/10.5194/gmd-16-509-2023> Geosci. Model Dev., 16, 509–534, 2023
518 J. Douros et al.: S5P
Figure 8. Time series of the TROPOMI original columns (S5P; red) and the CAMS combined columns (CAMS-RG-A; blue), with averaging
kernels applied for the domains as defined in Fig. 3. The retrieval algorithm versions used are as described in Sect. 2. Vertical axes are different
for each domain. Green vertical bars in July and November 2018 represent the model spread for those 2 months.
to OMI, from around −20 % in Europe in winter to only
small impacts in summer. With version 1.4.0, this difference
largely disappears (van Geffen et al., 2022), especially due to
increases in TROPOMI columns in wintertime. The large solar zenith angle in winter leads to small sensitivities near the
surface, which will enhance potential biases. The presence of
snow, on the other hand, will strongly enhance the sensitivity and may reduce retrieval errors. These considerations are
broadly in line with the observed TROPOMI-CAMS differences, and it seems likely that part of the systematic seasonal
effects is caused by retrieval uncertainties.
Modeling deficiencies can, on the other hand, be related
to uncertainties in the input data (primarily, emissions) and
also to the modeling of processes such as the injection of
emissions into the atmosphere, especially from point sources,
chemistry, vertical mixing, or advection. Past studies have indicated that total anthropogenic emissions in the TNO emissions inventory may be overestimated or not properly distributed in time. For example, Petetin et al. (2015) showed
that anthropogenic NOx emissions in the TNO inventory,
which is the basis for the MACC-III emissions inventory
(used by the CAMS regional models before September 2018)
and the CAMS-REG-AP v1.1 emissions inventory (September 2018 to June 2019), were overestimated for the Paris area.
Moreover, MACC-III emissions were based on 2011 as a reference year, while CAMS-REG-AP v1.1 was based on 2015,
which means that the downward trend in NOx emissions that
prevailed during the preceding decade (e.g., Lorente et al.,
2019; Zara et al., 2021) may not have been properly accounted for in the model simulations, leading to overestimations in NO2 concentrations. Biogenic soil NOx emissions
are also known to be underestimated (Vinken et al., 2014;
Visser et al., 2019), which can be one of the reasons behind
the lower modeled background columns levels.
In the comparison between regional air quality models and
OMI retrievals performed by Huijnen et al. (2010a), the seaGeosci. Model Dev., 16, 509–534, 2023 <https://doi.org/10.5194/gmd-16-509-2023>
J. Douros et al.: S5P 519
sonal cycle was found to be overestimated by the model simulations, which is in agreement with results by Blechschmidt
et al. (2018) for MAX-DOAS locations in Bremen and Observatoire de Haute-Provence (OHP). However, in Huijnen
et al. (2010a), there was a stronger discrepancy between
columns from the regional model simulations and satellite retrievals during the summer, while the comparison was more
favorable during winter, unlike in Blechschmidt et al. (2018)
and the current work.
From a process-based modeling point of view, the discrepancy in question may indicate deficiencies in the treatment of
wintertime chemistry. The NOx lifetime is much longer during winter because of the lower concentrations of OH and
RO2 radicals which act as sinks for NO2. Thus, a possible
underprediction of OH production, via the photolysis of O3
when less light is available, could lead to higher NO2 (Shah
et al., 2020; Stavrakou et al., 2008). Difficulties in the description of wintertime chemistry may also be related to heterogeneous chemistry, as the conversion of N2O5 to aerosol
is more sensitive and inherently more uncertain compared to
summer conditions. In addition to these, even mild overpredictions of NOx emissions can, due to the longer NO2 lifetime, be amplified to produce a larger impact on tropospheric
concentrations.
The treatment of vertical mixing can also affect the modeled NO2 vertical profile shape. Enhanced mixing will tend
to lead to lower NO2 concentrations near the surface and a
less steep vertical gradient in the boundary layer. The accurate prediction of the boundary layer development under the
often stable wintertime conditions, let alone temperature inversions, is an outstanding challenge for atmospheric models. Under such conditions, turbulent diffusion will often be
overestimated, subsequently leading to an overestimation of
the boundary layer height (Sandu et al., 2013). This overestimation of vertical mixing has, in turn, been shown to lead to
increases in the calculated vertical columns (Huijnen et al.,
2010a). NOx lifetime also generally increases with height.
Enhanced transport to higher altitudes will therefore lead to
an increase in the column amounts for the same number of
emissions. Similarly, the overestimation of injection heights
from point sources may lead to higher concentrations aloft,
leading to an overestimation of column amounts.
5.4 Results for the individual regional models
Figure 9 shows the S5P and CAMS-RG-A columns for the
ENSEMBLE and for each of CAMS regional production
models, based on the available first day forecasts for the
month of July 2018. At that time, there were seven operational models providing daily forecasts. As already identified in Sect. 5.1, background values appear higher for S5P
columns, but hotspots seem to be comparable. Since the same
emissions are, in principle, used by all models, differences
between the modeled columns should be attributed to differences in the treatment of transport (both in the horizontal and
the vertical), chemistry, or NO2 removal processes.
Differences between the individual models are further
examined in Fig. 10, which depicts maps for the average
monthly CAMS-RG-A and S5P-RG column spread, for July
and November 2018. These spreads are calculated on the basis of the difference between the minimum and maximum
values for these quantities, as calculated by using any of
the seven regional models, and can be considered to be a
measure of the uncertainty in the CAMS ENSEMBLE-based
columns. As expected, the spread is significantly higher (by a
factor of almost 5) for the actual modeled columns (CAMSRG-A) than for the TROPOMI columns when using the
CAMS model a priori from the individual models (S5P-RG).
Moreover, the spread is considerably larger for November,
by a factor of almost 2, compared to the summer month of
July. In July, the CAMS-RG-A spread is the largest at urban
areas all over Europe but more so in Benelux, the Ruhr area,
and England, while for winter CAMS-RG-A is more homogeneous across the domain but prominently high in the Po
Valley. A similar behavior arises for S5P-RG, with the largest
values of the spread over high activity areas during summer
and higher, more homogeneous values during winter.
Some basic statistics for individual cities for July and
November 2018 are provided in Table 3, which shows the
monthly mean values of S5P and CAMS-RG-A columns, the
lowest and highest model values for CAMS-RG-A, ratios between the S5P-RG and S5P columns, the relative difference,
and the spatial (Pearson’s R) correlation coefficient between
S5P and CAMS-RG-A, which is also based on the monthly
mean values. We base the calculation of the relative difference on the arithmetic mean of S5P and CAMS-RG-A, using
the |S5P−CAMS-RG-A|/[(S5P+CAMS-RG-A)/2]·100%
formula. The table shows that TROPOMI lies within the
model spread for July, but this is not the case for most cities
in November. Relative differences are up to 15 % for most
cities in July but up to 50 % for most cities in November.
Correlations are typically high, except for London in July
and Helsinki in November.
For the months of July and November 2018, Figs. 7 and 8
also depict the model spread of the CAMS-RG-A columns in
the form of solid green vertical bars. Note that the amount of
data involved in the actual regional model output, download
time, storage space, and the computational cost required for
processing 7 to 11 models has prevented us from calculating the spread for the full length of the time series in these
plots. Furthermore, for cities, the spread is also clearly lower
in July than in November in the selected domains, but the
S5P column values still mostly lie within the range since the
comparison is in any case more favorable during the summer.
The larger November spread does include the S5P column
values for some of the cities/domains, but the wintertime
discrepancy discussed above appears to be generally larger
than what could be explained by model variability and is thus
<https://doi.org/10.5194/gmd-16-509-2023> Geosci. Model Dev., 16, 509–534, 2023
520 J. Douros et al.: S5P
Figure 9. Comparison of S5P and CAMS-RG-A columns for seven CAMS regional production models based on the first day forecasts for
July 2018.
more systematic in nature. To conclude, both model results
and retrievals seem to be more uncertain in winter.
5.5 Results for the regional models – analysis vs.
forecast
The assimilation of (primarily surface) observations by the
CAMS regional models has been demonstrated to lead to
improved assessments of the 3-D concentration fields for
NO2 (Douros et al., 2020). The hypothesis would thus be
that, when using analyzed CAMS regional profiles to replace
the default TM5-MP a priori, this would lead to improved
TROPOMI (S5P-RG) columns. In this section, we aim to investigate the differences introduced by the use of the analyses
as compared to the first day forecasts.
Geosci. Model Dev., 16, 509–534, 2023 <https://doi.org/10.5194/gmd-16-509-2023>
J. Douros et al.: S5P 521
Figure 10. Model spread (for a definition, see Sect. 5.4) for tropospheric NO2 columns. The first row depicts CAMS-RG-A (a, c) and
S5P-RG (b, d) for July 2018, while the second row is the same for November 2018. Note the different scales.
Table 3. S5P and CAMS-RG-A column statistics at various European cities for July and November 2018, including the S5P-RG / S5P ratio.
Monthly mean values (1015 molec. cm−2
)
S5P CAMS-RG-A CAMS-RG-Amin CAMS-RG-Amax S5P-RG-A / S5P Rel. diff. (%)∗ Cor. coeff.∗
July 2018
London 6.40 7.19 5.66 12.27 1.15 11.66 0.23
Helsinki 1.92 2.08 1.63 2.76 0.99 8.28 0.84
Moscow 5.93 7.80 4.36 12.01 1.14 27.28 0.86
Paris 4.97 4.73 3.90 8.06 1.36 4.87 0.71
Berlin 2.36 2.61 2.07 3.81 1.30 9.90 0.93
Warsaw 2.01 2.13 1.69 4.54 1.39 6.02 0.89
Madrid 2.96 3.39 1.70 7.42 1.35 13.47 0.90
Rome 2.34 2.21 1.75 3.29 1.27 5.97 0.92
Istanbul 4.30 2.66 1.95 5.25 1.68 47.21 0.97
November 2018
London 5.81 9.31 7.44 13.00 1.09 46.26 0.81
Helsinki 2.00 4.39 2.67 6.81 0.93 74.79 0.59
Moscow 8.79 13.80 7.55 22.44 1.02 44.33 0.96
Paris 6.08 8.86 6.46 12.74 1.20 37.18 0.97
Berlin 5.50 8.76 5.63 14.21 1.10 45.78 0.73
Warsaw 4.33 7.16 4.95 9.77 1.11 49.30 0.79
Madrid 4.86 6.70 3.89 10.74 1.17 31.86 0.87
Rome 3.93 5.41 3.82 7.31 1.31 31.76 0.91
Istanbul 4.35 4.14 2.12 5.28 1.35 4.99 0.79
∗ Relative difference and correlation coefficient between S5P and CAMS-RG-A.
<https://doi.org/10.5194/gmd-16-509-2023> Geosci. Model Dev., 16, 509–534, 2023
522 J. Douros et al.: S5P
Figure 11. Percentile relative change between TROPOMI tropospheric NO2 columns derived using a merged CAMS a priori (S5P-RG)
based on the regional NRT analysis and regional forecast and averaged over the months of July 2018 (a) and January 2019 (b).
Figure 11 depicts the percentage of relative change
for July 2018 and January 2019 using the (S5P-RGAN −
S5P-RGFC)/|S5P-RGFC|·100% formula. Positive values indicate higher values for the analyses, while negative values
indicate higher values for the forecasts. For July, most areas in mainland Europe show higher values when using analyzed profiles, with the exception of some areas in the North
Sea and the English channel, where the columns based on
the forecasts seem higher. The situation for January is much
more ambiguous, as differences are generally smaller, and
there are no distinct patterns on the relative change map. The
noisy features in the northern part of the map are probably
due to the noise in the TROPOMI retrievals, as the values in
this part of the domain are very low.
6 A European TROPOMI NO2 level 2 product
The importance of using high-resolution realistic profiles as
a priori has been recognized by several groups, resulting in
dedicated regional retrieval products (M. Liu et al., 2020;
Griffin et al., 2019; Laughner et al., 2019) for the USA and
East Asia. Based on the combination of the CAMS–regional
NO2 profiles up to 3000 m altitude and IFS (compo) above,
we have generated a new S5P-RG level 2 TROPOMI NO2
product, using the approach described in Sect. 4.2. For this
product, we chose to use the regional ENSEMBLE for the
NRT analysis rather than the forecasts in order to benefit
from its better performance (Douros et al., 2020). For this
new product, horizontal regridding is performed with the
TROPOMI grid for the orbit as the target.
This new product is an extension of the L2 product files
with three new fields added to the existing data product. The
most relevant extra field is the one containing the S5P-RG
data but the original (S5P) is also still available. Data files
have been cropped to remove parts of the orbits with no overlap with the CAMS European domain, reducing the size of
the dataset by about a factor 15 compared to the original L2
dataset.
In general, we find that the 0.1◦ high-resolution CAMS–
regional a priori profile increases the dynamical range in NO2
vertical column density (VCD) values. More specifically, in
the emission hotspots, NO2 values are typically increased by
between 5 % and 30 %, but the increase strongly depends on
the location and time.
6.1 Impact of the free tropospheric column on the
retrievals and comparisons
A way to evaluate the impact of the free tropospheric column on the retrievals is by comparing TROPOMI retrievals
using either CAMS-RG or CAMS-R a priori profiles (S5PRG and S5P-R, respectively) with the respective CAMS-RG
and CAMS-R modeled columns (CAMS-RG-I and CAMSR-I). Monthly mean maps for July 2018 based on this scheme
are shown in Fig. 12.
Modeled columns (CAMS-RG-I and CAMS-R-I;
Fig. 12b, d) appear to be quite similar in these maps, while
TROPOMI columns (S5P-RG and S5P-R) are considerably
different, with background values being fairly higher for
S5P-R compared to S5P-RG. Though the free tropospheric
column is relatively small, even in summer, the TROPOMICAMS comparison nevertheless appears to be very sensitive
to it. When the free troposphere is removed, the model
columns will be somewhat smaller. The air mass factor in
the TROPOMI retrieval, however, will also be significantly
lower due to the shape of the averaging kernel, leading to a
noticeable increase in the TROPOMI retrieval. These effects
are opposite, thus leading to a cumulative increase in the
difference between TROPOMI and model-derived columns
when the free tropospheric column is too low or missing.
An alternative way of investigating the impact of the free
troposphere is by calculating the ratios between S5P-CAMS
for all available combinations of a priori profiles (S5P-RG,
S5P-R, S5P-G) and the native TROPOMI tropospheric column. Figure 13 shows maps of those three ratios averaged
over the summer months (June–August, JJA) of 2019. In
order to take full advantage of the high resolution of the
TROPOMI data, these maps were produced by regridding
column fields to a regular lat–long grid of 0.02◦ × 0.02◦
.
What is quite evident from Fig. 13 is that the S5P-R / S5P
ratio is larger than unity almost everywhere in the domain.
For S5P-G / S5P, the values are much closer to unity, while
for S5P-RG / S5P, the values are larger at most emission
Geosci. Model Dev., 16, 509–534, 2023 <https://doi.org/10.5194/gmd-16-509-2023>
J. Douros et al.: S5P 523
Figure 12. Monthly averaged S5P-RG (a), CAMS-RG-I (b), S5P-R (c), and CAMS-R-I (d) columns for July 2018.
Figure 13. The ratio of the retrievals performed with CAMS a priori profiles and the original TROPOMI retrievals. (a) S5P-RG/S5P, (b) S5PG/S5P, and (c) S5P-R/S5P. Data regridded from the L2 product to a 0.02◦ × 0.02◦ grid and averaged over the summer months (JJA) of 2019.
Note the different scales.
hotspots, e.g., at urban areas and across ship tracks in the
North Sea but closer to unity for most other areas. A ratio
larger than 1 reflects the fact that tropospheric columns are
larger when replacing the default TM5-MP a priori with a
CAMS modeled profile. But, in order to better understand
why this is the case, averaged profiles for both a summer
month (July 2018) and a winter one (January 2019) were
calculated at two locations, namely the distinctly urban environment of Paris and a fairly remote rural location in the
Cantal region of France, away from large emission sources.
Those profiles are shown in Fig. 14, together with the respective averaging kernels, and are calculated only for the times
of valid TROPOMI observations.
The averaging kernel, which describes the vertical structure of the impact of the a priori information assumed in the
retrieval, clearly acquires lower values near the surface for
the rural case due to lower albedo values at this location. For
July, the averaging kernel is close to unity at about 2 km over
the surface, while for January this altitude is much lower, at
about 1 km, indicating a shallower boundary layer.
<https://doi.org/10.5194/gmd-16-509-2023> Geosci. Model Dev., 16, 509–534, 2023
524 J. Douros et al.: S5P
Figure 14. Mean averaging kernel profiles (a, d) and NO2 profiles for Paris (b, e) and a rural location in France (c, f) during July (a–c) and
January (d–f) 2018. Mean NO2 profiles are plotted based on data from CAMS regional (ENSEMBLE), IFS (compo), and TM5-MP.
Comparisons between the modeled NO2 profiles reveal
higher mixing ratios as expected near the surface for the
regional ENSEMBLE in the urban location, but the ratios
are somewhat lower for the rural location. This difference
is more prominent during July and is possibly related to a
more efficient photochemical conversion of NOx to NO2, the
shorter lifetime, and higher resolution of the regional models.
IFS (compo) mixing ratios near the surface are, in any case,
not expected to be representative of most hotspot regions in
Europe due to the relatively coarse horizontal resolution of
the model. The ENSEMBLE tends to produce very low concentrations at 5 km altitude compared to IFS (compo) and
TM5-MP but more similar concentrations around 3 km. IFS
(compo) and TM5-MP agree reasonably well in summer, but
larger differences are seen in winter.
What is clear from the mean NO2 profiles for July is that,
for urban areas, the CAMS regional ENSEMBLE has a much
larger fraction of its column in the boundary layer compared
to either TM5-MP or IFS (compo). Moreover, as the averaging kernel provides the contribution of different altitudes
to the signal observed by TROPOMI, a large part of this
signal is normally interpreted as being representative of the
free troposphere, which, in the case of the ENSEMBLE, is
largely missing. This skews the S5P-R (and thus the ratio)
to higher values. TM5-MP and IFS (compo) have fairly similar profiles, leading to a more balanced ratio when examining the ratio for CAMS-G. The most interesting behavior
appears to be when using the CAMS-RG a priori. In urban areas, CAMS-R values are higher close to the surface, mainly
due to the higher horizontal resolution of the regional models
and the underlying emissions, which is something that leads
to higher S5P-RG columns and thus ratios. In rural areas,
the averaging kernel has somewhat lower values, and at the
same time, the free troposphere now also contributes to the
full tropospheric column, leading to lower S5P-RG columns
and ratios. The overall impact is therefore a notable increase
in the dynamic range of S5P-RG VCDs.
6.2 Validation of the TROPOMI-CAMS regional L2
product against ground-based data
The routine validation of the operational TROPOMI satellite NO2 tropospheric and total column retrievals largely reGeosci. Model Dev., 16, 509–534, 2023 <https://doi.org/10.5194/gmd-16-509-2023>
J. Douros et al.: S5P 525
lies on the global network of MAX-DOAS remote-sensing
instruments and the Pandora instruments from the Pandonia
Global Network (PGN; Verhoelst et al., 2021; Lambert et al.,
2021). Both instrument types are commonly used for the validation of satellite NO2 data (Celarier et al., 2008; Herman et
al., 2009, 2019; Chan et al., 2020; Compernolle et al., 2020;
Pinardi et al., 2020) Here we focus on the European S5P-RG
product discussed in Sect. 6. We note that earlier validation
of S5P NO2 with regional CAMS profiles was done by Ialongo et al. (2020), using the Pandora instrument at Helsinki.
In this study, we have used nine MAX-DOAS and six Pandora stations (see Table 4) that are within the spatial scope of
the S5P-RG product. In addition, we compare the operational
TROPOMI product and the CAMS-RG-I product with the
same reference dataset. This allows for a double-delta validation, i.e., S5P-RG vs. S5P and S5P-RG vs. CAMS-RG-I.
Practically, the CAMS-RG-I tropospheric columns can be reconstructed from the fields in the new product by multiplying
the smoothed CAMS column (CAMS-RG-A) with the ratio
of the operational S5P tropospheric air mass factor (AMF)
over the S5P-RG tropospheric AMF, with all the relevant information made available in the new product. This follows
that, by rearranging the second line of Eq. (1), we obtain
C
I ≡
X
l
x
cams
l =
M(x
tm5)
M(x
cams)
X
l
A
trop
l
x
cams
l
=

M(x
tm5)
M(x
cams)
C
A
. (4)
In order to focus on the tropospheric VCD, tropospheric
columns are estimated from the Pandora total columns by
subtracting the S5P stratospheric estimation, as done in
Pinardi et al. (2020). This is indicated by PGNtropo. The filter and colocation processing follows Verhoelst et al. (2021).
Only satellite pixels with qa_value > 0.75 and covering the
ground-based instrument location are kept. Regarding PGN
data, only the highest-quality label (0 and 10) is used. MAXDOAS data are retained if the data within ±1 h of overpass
time are available; the interpolated value at overpass time is
then used. PGN data are retained if the data within ±0.5 h of
overpass time are available; the average value is then used.
Figure 15 presents the results of the validation as density
scatterplots of the three datasets (the operational S5P, the
S5P-RG, and the CAMS-RG-I shown as columns in the figure) versus the MAX-DOAS data (upper row) and the PGN
data (lower row), where the co-located data are merged over
all stations. Quality indicators for the bias (mean and median difference and median relative difference) and difference dispersion (standard deviation, SD, and one-half of the
68 inter-percentile, 1/2 IP68) are provided, in addition to the
Pearson’s (R) correlation coefficient, the reduced major axis
(RMA) regression slope and intercept, and the residual dispersion (SD and 1/2 IP68) from the RMA regression line.
For both the comparisons with MAX-DOAS and with PGN,
one can conclude the following:
– The overall bias (both absolute scale and relative) of
S5P is more negative than that of S5P-RG, which in turn
is more negative than that of CAMS-RG-I.
– The bias of S5P clearly has a multiplicative component,
as indicated by the low RMA regression slope. This
component is reduced for S5P-RG.
– Data are more scattered, with higher difference dispersion parameters, in the case of CAMS-RG-I, while the
dispersion parameters are comparable for S5P and S5PRG. The correlation is slightly better for S5P than for
S5P-RG, while it is decidedly lower for CAMS-RG-I.
– The dispersion from the regression line is lower for S5P
than for S5P-RG, which in turn is lower than for CAMSRG-I.
Figure 16 is based on the same data, separated per station, that shows both the relative bias (median relative difference) for each dataset and the bias change with respect to S5P
or CAMS-RG-I. Blue bars indicate a reduction in the bias,
while red bars indicate an increase in the bias. At all stations,
except the PGN sites of INOE, S5P-RG presents a reduction
in the bias from 5 % to 18 % compared to S5P, showing the
impact of the a priori profile shapes used in the satellite retrievals. Bias changes in S5P-RG compared to CAMS-RG-I
can be positive or negative, are highly station dependent, and
can be much larger in absolute value. The largest discrepancies (over 40 %) are found at the MAX-DOAS sites of De
Bilt, Cabauw, Bremen, and Uccle. Difference dispersions per
station (not shown) are mostly comparable between S5P and
S5P-RG, while they are higher for CAMS-RG-I.
One should be aware that, even when a better a priori profile is used, it will still be different from the true profile. In
combination with the different vertical sensitivity between
the satellite and the reference data, a discrepancy will remain.
Therefore, when profiles retrieved by MAX-DOAS are available, an alternative approach is the application of the satellite averaging kernels to the NO2 lower tropospheric profiles
derived from the MAX-DOAS observations. This latter approach removes the TROPOMI a priori dependence from the
relative comparison, and it has been shown in the recent quarterly validation report for the TROPOMI products (Lambert
et al., 2021) that the (negative) bias estimate is reduced by
up to 20 % when the MAX-DOAS profile data are smoothed
vertically using S5P averaging kernels, indicating a significant impact of the profile shape due to the different vertical sensitivity profiles of MAX-DOAS versus the satellite
retrievals. It was also shown in Liu et al. (2021) that using
the S5P averaging kernel reduced the bias of about 16 % in
Munich for their regional TROPOMI product. It is therefore
likely that application of the satellite averaging kernel would
remove part of the residual bias of S5P-RG. However, as
<https://doi.org/10.5194/gmd-16-509-2023> Geosci. Model Dev., 16, 509–534, 2023
526 J. Douros et al.: S5P
Figure 15. Correlation density plots of S5P, S5P-RG, and CAMS-RG-I (columns 1 to 3) vs. MAX-DOAS (a–c) and vs. PGNtropo (d–f).
Quality indicators for bias (mean and median difference and median relative difference), difference dispersion (standard deviation and 1/2
IP68) are provided, in addition to the Pearson’s (R) correlation coefficient, the reduced major axis (RMA) regression slope and intercept, and
the residual dispersion (standard deviation, SD, and 1/2 IP68) from the RMA regression line.
Table 4. Overview of the stations contributing to the TROPOMI-CAMS tropospheric NO2 validation in this study.
Station Location Institute
MAX-DOAS sites
Athens 38.05◦ N, 23.86◦ E IUP-B
Bremen 53.10◦ N, 8.85◦ E IUP-B
Cabauw 51.97◦ N, 4.93◦ E KNMI
De Bilt 52.10◦ N, 5.18◦ E KNMI
Mainz 49.99◦ N, 8.23◦ E MPI-C
Munich 48.15◦ N, 11.57◦ E LMU
Thessaloniki_ciri 40.56◦ N, 22.99◦ E AUTH
Thessaloniki_lap 40.63◦ N, 22.96◦ E AUTH
Uccle 50.80◦ N, 4.36◦ E BIRA-IASB
Pandora sites∗
National Observatory of Athens (NOA) 37.99◦ N, 23.77◦ E PMOD/WRC; Luftblick OG, Austria
Helsinki 60.20◦ N, 24.96◦ E FMI; Luftblick OG, Austria
Innsbruck 47.26◦ N, 11.39◦ E Luftblick OG, Austria
INOE (Magurele, Romania) 44.35 ˘
◦ N, 26.03◦ E INOE; Luftblick OG, Austria
National Research Council (CNR; Rome) 41.84◦ N, 12.65◦ E ESA; Luftblick OG, Austria
Rome Sapienza 41.90◦ N, 12.52◦ E ESA; Luftblick OG, Austria
IUP-B is the Institute of Environmental Physics, University of Bremen. KNMI is the Royal Netherlands Meteorological Institute. MPI-C is
the Max-Planck-Institut für Chemie. LMU is the Ludwig-Maximilians-Universität München. AUTH is the Aristotle University of
Thessaloniki. BIRA-IASB is the Royal Belgian Institute for Space Aeronomy. PMOD/WRC is the Physical Meteorological Observatory
of Davos. FMI is the Finnish Meteorological Institute. INOE is the National Institute for Research and Development in Optoelectronics,
Romania. ESA is the European Space Agency. ∗ Note that, although the Pandora site of Ny-Ålesund (Svalbard) is within the range of
truncated orbits of the S5P-RG product, the product has fill values for the CAMS-specific fields, so this location was not considered.
Geosci. Model Dev., 16, 509–534, 2023 <https://doi.org/10.5194/gmd-16-509-2023>
J. Douros et al.: S5P 527
Figure 16. Median biases and relative bias changes for the different comparisons at all the MAX-DOAS (a, b) and Pandora (c, d) stations. The
left column (a, c) presents the comparison between SP5 (gray) and SP5-RG (black), while the right column (b, d) presents the comparison
between CAMS-RG-I (gray) and S5P-RG (black).
there are profile measurements available for only one MAXDOAS of the stations in Table 4, this topic is not pursued in
this study.
In summary, one can conclude that the bias of the tropospheric NO2 of S5P-RG is improved compared to that of the
operational S5P product for almost all stations by 5 %–18 %,
while the overall dispersion of both products is similar, but
the dispersion from the RMA regression line is better for
the standard S5P. The difference dispersion and correlation
parameters are superior for S5P and S5P-RG compared to
CAMS-RG-I.
In Fig. 17, we present the ratio of the CAMS a-priori-based
retrieval by the original retrieval at the MAX-DOAS locations. Most locations show values of around 1.1, indicating
that the coarse resolution of the TROPOMI a priori may lead
to a 10 % underestimation of the tropospheric column in urban regions. For Athens, this is about 30 %, showing that the
exact ratio will depend strongly on the location of the MAXDOAS instrument. The remote locations show values smaller
than unity, as discussed above. Interestingly, the ratio is relatively constant over the whole time period, with no obvious
seasonality.
Figure 17. Time series from May 2018 to March 2021 of the ratio of
TROPOMI NO2 retrievals at sites with a MAX-DOAS instrument.
The ratio is defined as the retrieval using the CAMS a priori profiles
divided by the operational retrieval. The seven sites are Athens in
Greece, Bremen in Germany, De Bilt in the Netherlands, Uccle in
Belgium (urban), Cabauw in the Netherlands (close to urban areas),
Observatoire de Haute-Provence (OHP) in France, and Jungfraujoch in Switzerland (remote).
<https://doi.org/10.5194/gmd-16-509-2023> Geosci. Model Dev., 16, 509–534, 2023
528 J. Douros et al.: S5P
7 Conclusions
In this work, we present a comparison of tropospheric NO2
from TROPOMI observations over Europe with the median
(ENSEMBLE) and seven individual models included in the
CAMS regional air quality ensemble for various selected
periods from May 2018 to March 2021. A methodological
scheme was introduced to elucidate approaches for model–
satellite comparisons, which builds on the fact that relative
differences can be made independent of the a priori profile
shape used in the satellite retrieval. We suggest that optimal model–satellite comparisons can be done in two ways,
namely either by applying the satellite averaging kernels to
the modeled profiles or by replacing the a priori in the retrieval with the modeled profiles, thus making use of the averaging kernel and air mass factor information in the original
TROPOMI NO2 L2 files.
During summer, the tropospheric NO2 columns, based
on the CAMS ENSEMBLE having applied the satellite averaging kernels, agree quantitatively to the corresponding
columns from TROPOMI, especially over major European
cities. Background values in summer, however, are found
to be significantly higher in the TROPOMI dataset, either
indicating issues with the modeling of soil emissions in
the CAMS models or with the separation of troposphere
from the stratosphere in the retrieval. In winter, the average
ENSEMBLE-based column amount is found to be significantly and systematically higher, and the difference seems
to increase with latitude. Possible reasons for this, including both larger retrieval uncertainties and modeling deficiencies of NO2 simulations in winter, were discussed. Validation
against surface NO2 concentrations performed within CAMS
does not confirm, however, this different behavior depending on latitude, a fact which points to the complementary
value of satellite-derived tropospheric columns as a means
for validating atmospheric composition models. Moreover, a
well-documented negative bias in TROPOMI has been partly
addressed in processor version 1.4.0 of the NO2 retrieval
that became operational in December 2020, and this has led
to an increase in the column amounts compared to previous versions, especially in winter. This development has the
potential to reduce the aforementioned difference between
TROPOMI and CAMS.
Qualitatively, the majority of all modeled NO2 local enhancements over cities, industries, powerplants, highways,
and shipping routes, derived from the underlying emission
maps, are also observed by TROPOMI. Transient features
such as city plumes are also comparable, although the differences there appear more pronounced, as the characteristics
of the modeled plumes are very sensitive to the modeling
of advection. An examination of the spatial aspects of the
columns derived on the basis of the individual CAMS regional models during a summer month mostly reveals similarities with those of the ENSEMBLE, but values, especially at hotspots, acquire quite different values, signifying
a considerable model spread. TROPOMI columns in summertime are thus found to lie within that model spread in
all examined areas. The spread is much more sizable during
autumn–winter, but this increased model variability in wintertime conditions is apparently not enough to explain the
large discrepancies between the satellite- and model-based
columns. The spatial correlation in European cities, on the
other hand, does not exhibit clear signs of seasonality, and in
most cases, we obtain values larger than 0.8.
Comparisons of TROPOMI retrievals using the CAMS a
priori based on the forecasts of analyses indicate that, in most
areas of mainland Europe, retrievals based on analyzed profiles have up to ∼ 20 % higher values compared to those
based on the forecasts, especially during the summertime.
This indicates that the assimilation of NO2 observations by
the models, mainly in the form of surface observations, can
considerably modify the shape and values of the CAMS vertical profile. The difference in winter is significantly reduced.
By making use of the averaging kernel and air mass factor information in the original TROPOMI NO2 L2 files, we
were also able to estimate the impact of the free troposphere
on the model–satellite comparison, and despite the relatively
small contribution of the free troposphere to the total tropospheric column, the effect on the comparison was found to
be substantial, suggesting that the free troposphere should
be invariably considered. This is of special interest as free
tropospheric NO2 concentrations were generally found to
be very low in the regional models at altitudes above 3 km,
partly because processes like lightning, deep convection, and
aircraft emissions are not consistently described in the regional models the way they are in the CAMS global system.
TROPOMI tropospheric columns derived using alternative
configurations of the CAMS profiles to replace the a priori
of the retrieval were also compared, and while the use of the
CAMS regional ENSEMBLE for the boundary layer systematically leads to higher urban area values due to the higher
resolution of the underlying emissions and models, the use
of the IFS (compo) model for the free troposphere was found
to lead to more balanced or even decreased columns at rural
areas.
We also introduce a new European TROPOMI L2 product utilizing a priori profiles from the CAMS models, building on the methodology and tools developed for the model–
satellite comparisons. This new product makes use of a vertically merged CAMS regional ENSEMBLE and global model
profile to replace the a priori used in the retrieval and thus
takes advantage of the substantially higher horizontal resolution of the CAMS regional models, leading to an increase
in the dynamical range of the NO2 columns compared to the
operational retrieval product, with typically increased tropospheric columns of up to 30 % over emission hotspots and
slight decreases over background areas.
This characteristic is further supported by calculating the
ratio of the TROPOMI column with the replaced a priori over
the native TROPOMI column at the locations of the global
Geosci. Model Dev., 16, 509–534, 2023 <https://doi.org/10.5194/gmd-16-509-2023>
J. Douros et al.: S5P 529
MAX-DOAS network of remote sensing instruments. Most
urban locations indicate a column enhancement of at least
10 % when replacing the TM5-MP a priori of the retrieval
with the merged CAMS profile.
Remote locations, however, point to values of the ratio being lower than unity, which means that the replacement of
the a priori corrects to lower column values. These corrections seem to be robust in time, with no obvious seasonality.
Comparisons with MAX-DOAS and PANDORA data indicate that the overall bias of tropospheric NO2 when replacing the a priori is improved when compared to that of the
standard, operational S5P product. This is not the case for
the correlation coefficient, suggesting that the CAMS profiles may not match the true profile variation well.
The findings of this paper reveal a generally favorable
comparison between TROPOMI and the CAMS regional
models, although certain aspects of the comparison expose
some of the intrinsic uncertainties in both the TROPOMI
product and the CAMS models. Noteworthy improvements
are expected from the TROPOMI side, with the introduction
of version 2.2.0 of the retrieval algorithm in July 2021, but
these will unlikely be enough to bridge the gap with the wintertime modeled columns, as identified in our comparison.
Identifying the reasons behind these discrepancies in NO2
columns might probably also require model sensitivity studies, with alternative chemistry and vertical mixing schemes,
and further improvements in the input data, such as emissions
and their injection heights.
Code and data availability. The bulk of the code used in this paper
is available on Zenodo (<https://doi.org/10.5281/zenodo.7016483>;
Douros, 2022). Horizontal interpolation was done using the regridding capabilities of the Earth System Modeling Framework (ESMF;
<https://earthsystemmodeling.org/regrid>, last access: 20 May 2022).
TROPOMI L2 datasets used in this paper are made available
operationally through the ESA Sentinel-5P data hub (https://
s5phub.copernicus.eu, last access: 20 May 2022), while the new
L2 product described in Sect. 6 is made available through the
TEMIS portal (<https://www.temis.nl/airpollution/no2col/no2_euro>_
tropomi_cams.php, last access: 20 May 2022). Since the conception
and writing of this paper, the data in TEMIS have been updated
using the S5P-PAL NO2 dataset (<https://data-portal.s5p-pal.com/>
products/no2.html, last access: 20 October 2022), which is based
on version 2.3.1 of the processor. Data for the new L2 product used
in this paper have, however, been retained and can be made available, upon request to the corresponding author, to interested users.
CAMS model data, both for the regional models and IFS (compo)
were retrieved from the CAMS Atmosphere Data Store (https:
//ads.atmosphere.copernicus.eu, last access: 20 May 2022) and its
predecessor hosted by Météo-France.
Supplement. The supplement related to this article is available online at: <https://doi.org/10.5194/gmd-16-509-2023-supplement>.
Author contributions. JD developed the code for the comparisons
between TROPOMI and CAMS and for the production of the new
L2 product. JD and HE were responsible for the development of
the proposed methodology and are the main authors of the paper.
SC and GP were responsible for the comparison with the MAXDOAS and the Pandora observations. VHP and AC contributed to
the CAMS modeling part. All authors reviewed and improved on
the paper.
Competing interests. The contact author has declared that none of
the authors has any competing interests.
Disclaimer. Publisher’s note: Copernicus Publications remains
neutral with regard to jurisdictional claims in published maps and
institutional affiliations.
Acknowledgements. Sentinel-5 Precursor is a European Space
Agency (ESA) mission on behalf of the European Commission
(EC). The TROPOMI payload is a joint development by ESA
and the Netherlands Space Office (NSO). The Sentinel-5 Precursor
ground segment development has been funded by ESA and with national contributions from the Netherlands, Germany, and Belgium.
This work contains modified Copernicus Sentinel-5P TROPOMI
data (2018–2021), processed in the operational framework or locally at KNMI, with post-processing for validation purposes performed by BIRA-IASB.
Part of the reported work was carried out in the framework of
the Copernicus Sentinel-5 Precursor Mission Performance Centre
(S5P MPC), contracted by the European Space Agency (ESA/ESRIN; contract no. 4000117151/16/I-LG) and supported by the Belgian Federal Science Policy Office (BELSPO), the Royal Belgian
Institute for Space Aeronomy (BIRA-IASB), the Netherlands Space
Office (NSO), and the German Aerospace Center (DLR). Part of
this work was also carried out in the framework of the nationally
funded S5P Validation Team (S5PVT) AO projects NIDFORVAL
(ID no. 28607; principal investigator Gaia Pinardi, BIRA-IASB)
and CESAR (ID no. 28596, principal investigator Arnoud Apituley, KNMI), which are acknowledged in particular for the collection
of ground-based data tailored to the S5P validation. Steven Compernolle and Gaia Pinardi have been supported partly by BELSPO and ESA through the ProDEx project TROVA-E2 (grant
no. PEA 4000116692).
The authors are indebted to the instrument principal investigators, staff at the stations, and supporting agencies for the acquisition and fast delivery of the MAX-DOAS and Pandora measurements contributing to this paper. The authors are especially grateful to ESA/ESRIN, for running the FRM4DOAS and Pandonia
FRM projects of the Fiducial Reference Measurements (FRM) program, and for supporting the ESA Atmospheric Validation Data
Centre (EVDC) established at NILU. The MAX-DOAS data used
in this publication were obtained from Alkiviadis Bais (AUTH),
for Thessaloniki, Ankie Piters (KNMI), for Cabauw and De Bilt,
John P. Burrows and Andreas Richter (IUP-B), for Bremen and
Athens (Athens instrument hosted by NOA), Ka Lok Chan (DLR),
for Munich, Michel Van Roozendael (BIRA-IASB), for Uccle, and
Thomas Wagner (MPIC), for Mainz. Part of the MAX-DOAS data
<https://doi.org/10.5194/gmd-16-509-2023> Geosci. Model Dev., 16, 509–534, 2023
530 J. Douros et al.: S5P
contributes to the Network for the Detection of Atmospheric Composition Change (NDACC) and is publicly available. The PGN
data were collected from Stelios Kazadzis (PMOD/WRC), for
Athens, Jari Hovila (FMI), for Helsinki, Anca Nemuc (INOE), for
Magurele, Martin Tiefengraber (Luftblick), for Innsbruck, and Ste- ˘
fano Casadio (ESA), for Rome CNR and Rome Sapienza, while
central data processing is done by Martin Tiefengraber (Luftblick).
PGN is a bilateral project supported with funding from ESA and
NASA, and the data are available publicly.
The authors express special thanks to Ann Mari Fjæraa (NILU),
Sander Niemeijer (s[&]t), José Granville, and Olivier Rasson
(BIRA-IASB), for post-processing of the network and satellite data
and for their dedication to the S5P TROPOMI operational validation. The authors are also thankful to Tijl Verhoelst (BIRA-IASB),
for in-depth discussions on NO2 validation methods and uncertainties. Copernicus Atmosphere Monitoring Service (CAMS) is implemented by the European Centre for Medium-Range Weather Forecasts and its contractors on behalf of the European Commission
Directorate-General for Defence Industry and Space sector (DG
DEFIS) as a component of the European Union’s flagship Space
program Copernicus.
Financial support. This research has been supported by the European Space Agency (ESA/ESRIN; contract no. 4000117151/16/ILG) and BELSPO and ESA through the ProDEx project TROVAE2 (grant no. PEA 4000116692).
