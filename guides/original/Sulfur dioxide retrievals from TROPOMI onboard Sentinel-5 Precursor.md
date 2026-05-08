Atmos. Meas. Tech., 10, 119–153, 2017
<www.atmos-meas-tech.net/10/119/2017/>
doi:10.5194/amt-10-119-2017
© Author(s) 2017. CC Attribution 3.0 License.
Sulfur dioxide retrievals from TROPOMI onboard Sentinel-5
Precursor: algorithm theoretical basis
Nicolas Theys1
, Isabelle De Smedt1
, Huan Yu1
, Thomas Danckaert1
, Jeroen van Gent1
, Christoph Hörmann2
,
Thomas Wagner2
, Pascal Hedelt3
, Heiko Bauer3
, Fabian Romahn3
, Mattia Pedergnana3
, Diego Loyola3
, and
Michel Van Roozendael1
1Royal Belgian Institute for Space Aeronomy (BIRA-IASB), Brussels, Belgium
2Max Planck Institute for Chemistry (MPIC), Hahn-Meitner-Weg 1, 55128 Mainz, Germany
3
Institut für Methodik der Fernerkundung (IMF), Deutsches Zentrum für Luft und Raumfahrt (DLR),
Oberpfaffenhofen, Germany
Correspondence to: N. Theys (<theys@aeronomie.be>)
Received: 21 September 2016 – Published in Atmos. Meas. Tech. Discuss.: 22 September 2016
Revised: 19 November 2016 – Accepted: 12 December 2016 – Published: 9 January 2017
Abstract. The TROPOspheric Monitoring Instrument
(TROPOMI) onboard the Copernicus Sentinel-5 Precursor
(S-5P) platform will measure ultraviolet earthshine radiances
at high spectral and improved spatial resolution (pixel size
of 7 km × 3.5 km at nadir) compared to its predecessors
OMI and GOME-2. This paper presents the sulfur dioxide
(SO2) vertical column retrieval algorithm implemented in
the S-5P operational processor UPAS (Universal Processor
for UV/VIS Atmospheric Spectrometers) and comprehensively describes its various retrieval steps. The spectral
fitting is performed using the differential optical absorption
spectroscopy (DOAS) method including multiple fitting
windows to cope with the large range of atmospheric SO2
columns encountered. It is followed by a slant column
background correction scheme to reduce possible biases
or across-track-dependent artifacts in the data. The SO2
vertical columns are obtained by applying air mass factors
(AMFs) calculated for a set of representative a priori profiles
and accounting for various parameters influencing the
retrieval sensitivity to SO2. Finally, the algorithm includes
an error analysis module which is fully described here. We
also discuss verification results (as part of the algorithm
development) and future validation needs of the TROPOMI
SO2 algorithm.
1 Introduction
Sulfur dioxide enters the Earth’s atmosphere via both natural
and anthropogenic processes. Through the formation of sulfate aerosols and sulfuric acid, it plays an important role on
the chemistry at local and global scales and its impact ranges
from short-term pollution to climate forcing. While about
one-third of the global sulfur emissions originate from natural sources (volcanoes and biogenic dimethyl sulfide), the
main contributor to the total budget is from anthropogenic
emissions mainly from the combustion of fossil fuels (coal
and oil) and from smelting. Over the last decades, a host of
satellite-based UV–visible instruments have been used for
the monitoring of anthropogenic and volcanic SO2 emissions. Total vertical column density (VCD) of SO2 has been
retrieved with the sensors TOMS (Krueger, 1983), GOME
(Eisinger and Burrows, 1998; Thomas et al., 2005; Khokar et
al., 2005), SCIAMACHY (Afe et al., 2004), OMI (Krotkov
et al., 2006; Yang et al., 2007, 2010; Li et al., 2013; Theys
et al., 2015), GOME-2 (Richter et al., 2009; Bobrowski et
al., 2010; Nowlan et al., 2011; Rix et al., 2012; Hörmann
et al., 2013) and OMPS (Yang et al., 2013). In particular,
the Ozone Monitoring Instrument (OMI) has largely demonstrated the value of satellite UV–visible remote sensing (1) in
monitoring volcanic plumes in near-real time (Brenot et al.,
2014) and changes in volcanic degassing at the global scale
(Carn et al., 2016, and references therein) and (2) in detecting
and quantifying large anthropogenic SO2 emissions, weak or
Published by Copernicus Publications on behalf of the European Geosciences Union.
120 N. Theys et al.: S-5P SO2 algorithm theoretical basis
Figure 1. Map of averaged SO2 columns from OMI clear-sky pixels
for the 2005–2009 period.
unreported emission sources worldwide (Theys et al., 2015;
Fioletov et al., 2016; McLinden et al., 2016) as well as investigating their long-term changes (Krotkov et al., 2016;
van der A et al., 2016; He et al., 2016). An example map
of OMI SO2 columns (Theys et al., 2015) averaged over the
2005–2009 period is shown in Fig. 1, illustrating typical anthropogenic emission hotspots (China, eastern Europe, India
and the Middle East) and signals from volcanic activity (e.g.,
from the volcanoes in DR Congo).
The 7-year-lifetime Sentinel-5p sensor TROPOMI
(Veefkind et al., 2012) will fly on a polar low-Earth orbit
with a wide swath of 2600 km. The TROPOMI instrument
is a push-broom imaging spectrometer similar in concept
to OMI. It has eight spectral bands covering UV to SWIR
wavelengths. The SO2 retrieval algorithm exploits measurements from band 3 (310–405 nm), with typical spectral
resolution of 0.54 nm, signal-to-noise ratio of about 1000
and pixel size as good as 7 km × 3.5 km.
TROPOMI will continue and improve the measurement
time series of OMI SO2 and other UV sensors. Owing to similar performance to OMI in terms of signal-to-noise ratio and
unprecedented spatial resolution, TROPOMI will arguably
discern very fine details in the SO2 distribution and will be
able to detect point sources with annual SO2 emissions of
about 10 kT yr−1 or lower (using oversampling techniques).
This paper gives a thorough description of the operational
TROPOMI SO2 algorithm and reflects the S-5P SO2 L2 Algorithm Theoretical Basis Document v1.0. In Sect. 2, we first
present the product requirements and briefly discuss the expected product performance in terms of precision and accuracy. It is then followed by the SO2 column retrieval algorithm description. An error analysis of the retrieval method
is presented in Sect. 3. Results from algorithm verification
exercise using an independent retrieval scheme is given in
Sect. 4. The possibilities for future validation of the retrieved
SO2 data product can be found in Sect. 5. Conclusions are
given in Sect. 6. Additional information on data product and
auxiliary data, as well as a list of acronyms, is provided in
the Appendix.
2 TROPOMI SO2 algorithm
2.1 Product requirements
While UV measurements are highly sensitive to SO2 at high
altitudes (upper troposphere–lower stratosphere), the sensitivity to SO2 concentration in the boundary layer is intrinsically limited from space due to the combined effect of scattering (Rayleigh and Mie) and ozone absorption that hamper the penetration of solar radiation into the lowest atmospheric layers. Furthermore, the SO2 absorption signature
suffers from the interference with the ozone absorption spectrum.
The retrieval precision (or random uncertainty) is driven
by the signal-to-noise ratio of the recorded spectra and by the
retrieval wavelength interval used, the accuracy (or systematic uncertainty) is limited by the knowledge on the auxiliary
parameters needed in the different retrieval steps. Among
these are the treatment of other chemical interfering species,
clouds and aerosol, the representation of vertical profiles
(gas, temperature, pressure), and uncertainties on data from
external sources (e.g., surface reflectance).
Requirements on the accuracy and precision for the data
products derived from the TROPOMI measurements are
specified in the GMES Sentinels 4 and 5 and 5p Mission
Requirements Document MRD (Langen et al., 2011), the
Report of The Review Of User Requirements for Sentinels4/5 (Bovensmann et al., 2011) and the Science Requirements
Document for TROPOMI (van Weele et al., 2008). These requirements derive from the Composition of the Atmosphere:
Progress to Applications in the user CommunITY (CAPACITY) study (Kelder et al., 2005) and have been fine-tuned
by the Composition of the Atmospheric Mission concEpts
and SentineL Observation Techniques (CAMELOT; Levelt
et al., 2009) and Original and New TRopospheric composition and Air Quality measurements (ONTRAQ; Zweers et al.,
2010) studies. The CAPACITY study has defined three main
themes: the ozone layer (A), air quality (B), and climate (C),
with further division into sub-themes. Requirements for SO2
have been specified for a number of these sub-themes. In the
following paragraphs, we discuss these requirements and the
expected performances of the SO2 retrieval algorithm (summary is given in Table 1).
2.1.1 Theme A3 – ozone layer assessment
This theme addresses the importance of measurements in
the case of enhanced SO2 concentrations in the stratosphere
due to severe volcanic events. The long-term presence (up
to several months) of SO2 in the stratosphere contributes to
the stratospheric aerosol loading and hence affects the cliAtmos. Meas. Tech., 10, 119–153, 2017 <www.atmos-meas-tech.net/10/119/2017/>
N. Theys et al.: S-5P SO2 algorithm theoretical basis 121
Table 1. Requirements on SO2 vertical column products as derived from the MRD. Left- and right-hand numbers in ranges denote accuracy
and precision, respectively.
Horizontal Required Achievable Theme
resolution uncertainty uncertainty (table in
(km) MRTD)
Enhanced stratospheric 50–200 30 % for Met for VCD > 0.5 DU A3
column VCD > 0.5 DU VCD > 0.5 DU
Tropospheric 5–20 30–60 % or 50 %/ B1, B2, B3
column 1.3 × 1015 molecules cm−2 3–6 × 1016 molecules cm−2
(least stringent)
Total column 5–20 30–60 % or 50 %/ B1, B2, B3
1.3 × 1015 molecules cm−2 3–6 × 1016 molecules cm−2
(least stringent)
mate and the stratospheric ozone budget. For such scenarios, the requirements state that the stratospheric vertical column should be monitored with a total uncertainty of 30 %.
Although powerful volcanic events generally produce large
amounts of SO2, monitoring such a plume over extended periods of time also requires the detection of the plume after it
has diluted during the weeks after the eruption.
From an error analysis of the proposed SO2 algorithm
(Sect. 3), we have assessed the major sources of uncertainty
in the retrieved SO2 column. One of the main contributors
to the total uncertainty is instrumental noise. This source of
error alone limits the precision to vertical columns above
about 0.25 DU (1 DU = 2.69 × 1016 molec cm−2
). For SO2
in the stratosphere, the summing-up of the various uncertainties (Sect. 3) is believed to be around the required uncertainty
of 30 % for diluted SO2 plumes, provided that the vertical
column is larger than 0.5 DU. Explosive volcanic eruptions
capable of injecting SO2 into the stratosphere regularly show
stratospheric SO2 columns of a few DU to several hundreds
of DU or more, as was the case, for example, for the eruptions of Mt. Kasatochi (Yang et al., 2010) and Sarychev Peak
(Carn et al., 2011). For very large SO2 concentrations, the
dynamical use of different fitting windows (see Sect. 2.2) enables the 30 % uncertainty level to be reached (see Sect. 4).
2.1.2 Theme B – air quality
This theme includes three sub-themes:
B1 Protocol monitoring: this involves the monitoring of
abundances and concentrations of atmospheric constituents, driven by several agreements, such as the
Gothenburg protocol, National Emission Ceilings, and
EU Air Quality regulations.
B2 Near-real-time (NRT) data requirements: this comprises
the relatively fast (∼ 30 min) prediction and determination of surface concentrations in relation to health and
safety warnings.
B3 Assessment: this sub-theme aims at answering several
air-quality-related scientific questions, such as the effect
on air quality of spatial and temporal variations in oxidizing capacity and long-range transport of atmospheric
constituents.
A more detailed description of the air quality sub-themes can
be found in Langen et al. (2011).
The user requirements on SO2 products are equal for
all three sub-themes. For the total vertical column and
the tropospheric vertical column of SO2, the user requirements state an absolute maximum uncertainty of
1.3 × 1015 molecules cm−2 or 0.05 DU. This number derives
from the ESA CAPACITY study, where the number was expressed as 0.4 ppbv for a 1.5 km thick boundary layer reaching up to 850 hPa. From the uncertainty due to instrument
noise only, it is clear that the 0.05 DU requirement cannot
be met on a single-measurement basis. This limitation was
already found in the ESA CAMELOT study (Levelt et al.,
2009).
For anthropogenic SO2 typically confined in the planetary boundary layer (PBL), calculations performed within
the CAMELOT study showed that the smallest vertical column that can be detected in the PBL is of about 1–3 DU
(for a signal-to-noise ratio (S/N) of 1000). Although pollution hotspots can be better identified by spatial or temporal averaging, several uncertainties (e.g., due to varying surface albedo or SO2 vertical profile shape) are not averaging
out and directly limit the product accuracy to about 50 %
or more. Though the difference between the MRD requirements and the expected TROPOMI performance is rather
large, one could argue that the required threshold should
not be a strict criterion in all circumstances. The user requirement of 0.05 DU represents the maximum uncertainty
to distinguish (anthropogenic) pollution sources from background concentrations. Bovensmann et al. (2011) reviewed
the MRD user requirements and motivated a relaxation of
certain user requirements for specific conditions. For measurements in the PBL, the document proposes a relative
<www.atmos-meas-tech.net/10/119/2017/> Atmos. Meas. Tech., 10, 119–153, 2017
122 N. Theys et al.: S-5P SO2 algorithm theoretical basis
Figure 2. Flow Diagram of the TROPOMI DOAS retrieval algorithm for SO2.
requirement of 30–60 % in order to discriminate between
enhanced (> 1.5 ppbv), moderate (0.5–1.5 ppbv), and background concentrations (< 0.5 ppbv). It is expected that it will
be possible to discriminate these three levels by averaging
(spatiotemporally) TROPOMI data.
For volcanic SO2 plumes in the free troposphere, a better
measurement sensitivity is expected for TROPOMI. The expected precision is about 0.5 DU on the vertical column. The
accuracy on the SO2 vertical column will be strongly limited by the SO2 plume height and the cloud conditions. As
these parameters are highly variable in practice, it is difficult
to ascertain the product accuracy for these conditions.
2.2 Algorithm description
The first algorithm to retrieve SO2 columns from space-borne
UV measurements was developed based on a few wavelength
pairs (for TOMS) and has been subsequently applied and refined for OMI measurements (e.g., Krotkov et al., 2006; Yang
et al., 2007, and references therein). Current algorithms exploit back-scattered radiance measurements in a wide spectral range using a direct fitting approach (Yang et al., 2010;
Nowlan et al., 2011), a principal component analysis (PCA)
method (Li et al., 2013) or (some form of) differential optical
absorption spectroscopy (DOAS; Platt and Stutz, 2008); see,
e.g., Richter et al. (2009), Hörmann et al. (2013), or Theys et
al. (2015).
Direct fitting schemes in which on-the-fly radiative transfer simulations are made for all concerned wavelengths and
resulting simulated spectra are adjusted to the spectral observations, are in principle the most accurate. They are able to
cope with very large SO2 columns (such as those occurring
during explosive volcanic eruptions), i.e., conditions typically leading to a strongly nonlinear relation between the
SO2 signal and the VCD. However, the main disadvantage
of direct fitting algorithms with respect to DOAS (or PCA)
is that they are computationally expensive and are out of
reach for TROPOMI operational near-real-time processing,
for which the level 1b data flow is expected to be massive
and deliver around 1.5 million spectral measurements per orbit (∼ 15 orbits daily) for band 3 (with a corresponding data
size of 6 GB). To reach the product accuracy and processing performance requirements, the approach adopted here
applies DOAS in three different fitting windows (within the
310–390 nm spectral range) that are still sensitive enough to
SO2 but less affected by nonlinear effects (Bobrowski et al.,
2010; Hörmann et al., 2013).
Figure 2 shows the full flow diagram of the SO2 retrieval
algorithm including the dependencies on auxiliary data and
other L2 products. The algorithm and its application to OMI
data are also described in Theys et al. (2015), although there
are differences in some settings. The baseline operation flow
of the scheme is based on a DOAS retrieval algorithm and
is identical to that implemented in the retrieval algorithm for
HCHO (also developed by BIRA-IASB; see De Smedt et al.,
2016). The main output parameters of the algorithm are SO2
vertical column density, slant column density, air mass factor,
averaging kernels (AKs) and error estimates. Here, we will
first briefly discuss the principle of the DOAS VCD retrieval
before discussing the individual steps of the process in more
detail.
First, the radiance and irradiance data are read from an S5P L1b file, along with geolocation data such as pixel coorAtmos. Meas. Tech., 10, 119–153, 2017 <www.atmos-meas-tech.net/10/119/2017/>
N. Theys et al.: S-5P SO2 algorithm theoretical basis 123
dinates and observation geometry (sun and viewing angles).
At this stage cloud cover information (see Table A3 in Appendix A) is also obtained from the S-5P cloud L2 data, as
required for the calculation of the AMF, later in the scheme.
Then relevant absorption cross section data, as well as characteristics of the instrument (e.g., slit functions), are used as
input for the determination of SO2 slant column density. As
a baseline, the slant column fit is done in a sensitive window
from 312 to 326 nm. For pixels with a strong SO2 signal,
results from alternative windows where the SO2 absorption
is weaker can be used instead. An empirical offset correction (dependent on the fitting window used) is then applied to
the SCD. The latter correction accounts for systematic biases
in the SCDs. Following the SCD determination, the AMF is
estimated based on a pre-calculated weighting functions (or
box AMFs) look-up table (LUT). This look-up table is generated using the LInearized Discrete Ordinate Radiative Transfer (LIDORT) code (Spurr, 2008) and has several entries:
cloud cover data, topographic information, observation geometry, surface albedo, effective wavelength (representative
of the fitting window used), total ozone column and the shape
of the vertical SO2 profile. The algorithm also includes an error calculation and retrieval characterization module (Sect. 3)
that computes the averaging kernels (Eskes and Boersma,
2003), which characterize the vertical sensitivity of the measurement and which are required for comparison with other
types of data (Veefkind et al., 2012).
The final SO2 vertical column is obtained by
Nv =
Ns − Nback
s
M
, (1)
where the main quantities are the vertical column (Nv), the
slant column density (Ns) and the values used for the background correction (Nback
s
). M is the air mass factor.
2.2.1 Slant column retrieval
The backscattered radiance spectrum recorded by the space
instrument differs from the solar spectrum because of the interactions of the photons with the Earth’s atmosphere and
surface reflection. Hence, the reflectance spectra contains
spectral features that can be related to the various absorbing species and their amounts in the atmosphere. The DOAS
method aims at the separation of the highly structured trace
gas absorption spectra and broadband spectral structures. The
technique relies on a number of assumptions that can be summarized as follows:
a. The spectral analysis and atmospheric radiative transfer
computations are treated separately by considering one
averaged atmospheric light path of the photons traveling
from the sun to the instrument.
b. The absorption cross sections are not strongly dependent on pressure and temperature. Additionally, the averaged light path should be weakly dependent on the
wavelength – for the fitting window used – which enables defining an effective absorption (slant) column
density. It should be noted that this is not strictly valid
for the SO2 DOAS retrieval because of strong absorption by ozone and in some cases SO2 itself (for large
SO2 amounts).
c. Spectrally smoothed structures due broadband absorption, scattering and reflection processes can be well reproduced by a low-order polynomial as a function of
wavelength.
Photons collected by the satellite instrument may have followed very different light paths through the atmosphere depending on their scattering history. However, a single effective light path is assumed, which represents an average of
the complex paths of all reflected and scattered solar photons
reaching the instrument within the spectral interval used for
the retrieval. This simplification is valid if the effective light
path is reasonably constant over the considered wavelength
range. The spectral analysis can be described by the following equation:
ln
πI (λ)
µ0E0 (λ)
= −X
j
σj (λ)Nsj +
X
p
cpλ
p
, (2)
where I (λ) is the observed backscattered earthshine radiance (W m−2 nm−1
sr−1
), E0 is the solar irradiance
(W m−2 nm−1
) and µ0 = cos θ0. The first term on the righthand side indicates all relevant absorbing species with absorption cross sections σj (cm2 molec−1
). Integration of the
number densities of these species along the effective light
path gives the slant column density Nsj (molec cm−2
). Equation (2) can be solved by least-squares fitting techniques
(Platt and Stutz, 2008) for the slant column values. The final
term in Eq. (2) is the polynomial representing broadband absorption and (Rayleigh and Mie) scattering structures in the
observed spectrum and also accounts for possible errors such
as uncorrected instrument degradation effects, uncertainties
in the radiometric calibration or possible residual (smooth)
polarization response effects not accounted for in the level
0–1 processing.
Apart from the cross sections for the trace gases of interest, additional fit parameters need to be introduced to account
for the effect of several physical phenomena on the fit result.
For SO2 fitting, these are the filling-in of Fraunhofer lines
(Ring effect) and the need for an intensity offset correction.
In the above, we have assumed that for the ensemble of observed photons a single effective light path can be assumed
over the adopted wavelength fitting interval. For the observation of (generally small) SO2 concentrations at large solar
zenith angles (SZAs) this is not necessarily the case. For such
long light paths, the large contribution of O3 absorption may
lead to negative SO2 retrievals. This may be mitigated by
taking the wavelength dependence of the O3 SCD over the
<www.atmos-meas-tech.net/10/119/2017/> Atmos. Meas. Tech., 10, 119–153, 2017
124 N. Theys et al.: S-5P SO2 algorithm theoretical basis
Table 2. DOAS settings used to retrieved SO2 slant columns.
Fitting intervals 1 and 2 312–326 nm (w1), 325–335 nm (w2)
Cross sections SO2 : 203K (Bogumil et al., 2003)
O3 : 228 and 243 K with Io correction (Brion et al., 1998)
Pseudo-O3 cross sections (λσO3, σ
2
O3
; Puk¯ıte et al., 2010)
Ring effect: two eigenvectors (Vountas et al., 1998) generated for 20 and
87◦
solar zenith angles using LIDORT-RRS (Spurr et al., 2008)
Polynomial Fifth order
Fitting interval 3 360–390 nm (w3)
Cross sections SO2: Hermans et al. (2009) extrapolated at 203K
NO2 : 220 K (Vandaele et al., 1998)
O2-O2: Greenblatt et al.,1990
Ring effect: single spectrum (Chance and Spurr, 1997)
Polynomial Fourth order
Intensity offset correction Linear offset
Spectrum shift and stretch Fitted
Spectral spikes removal procedure Richter et al. (2011)
Reference spectrum Baseline: daily solar irradiance
Foreseen update: daily averaged earthshine spectrum in Pacific region
(10◦ S–10◦ N, 160◦ E–120◦ W); separate spectrum for each detector row.
NRT: averaged spectra of the last available day; offline: averaged spectra of
the current day
Figure 3. Absorption cross sections of SO2 and O3. The blue, yellow and green boxes delimit the three SO2 fitting windows 312–
326, 325–335 and 360–390 nm, respectively.
fitting window into account, as will be described in the next
section.
The different parts of the DOAS retrieval are detailed in
the next subsections and Table 2 gives a summary of settings
used to invert SO2 slant columns. Note that, in Eq. (2), the
daily solar irradiance is used as a baseline for the reference
spectrum. As a better option, it is generally preferred to use
daily averaged radiances, selected for each across-track position, in the equatorial Pacific. In the NRT algorithm, the
last valid day can be used to derive the reference spectra,
while in the offline version of the algorithm, the current day
should be used. Based on OMI experience, it would allow,
for example, for better handling of instrumental artifacts and
degradation of the recorded spectra for each detector. At the
time of writing, it is planned to test this option during the
S-5P commissioning phase.
Wavelength fitting windows
DOAS measurements are in principle applicable to all gases
having suitable narrow absorption bands in the UV, visible,
or near-IR regions. However, the generally low concentrations of these compounds in the atmosphere, and the limited
signal-to-noise ratio of the spectrometers, restrict the number of trace gases that can be detected. Many spectral regions
contain several interfering absorbers and correlations between absorber cross sections can sometimes lead to systematic biases in the retrieved slant columns. In general, the correlation between cross sections decreases if the wavelength
interval is extended, but then the assumption of a single effective light path defined for the entire wavelength interval
may not be fully satisfied, leading to systematic misfit effects
that may also introduce biases in the retrieved slant columns
(e.g., Puk¯ı¸te et al., 2010) . To optimize DOAS retrieval settings, a trade-off has to be found between these effects. In
the UV–visible spectral region, the cross-section spectrum of
SO2 has its strongest bands in the 280–320 nm range (Fig. 3).
For the short wavelengths in this range, the SO2 signal, however, suffers from a strong increase in Rayleigh scattering
and ozone absorption. In practice, this leads to a very small
SO2 signal in the satellite spectra compared to ozone absorpAtmos. Meas. Tech., 10, 119–153, 2017 <www.atmos-meas-tech.net/10/119/2017/>
N. Theys et al.: S-5P SO2 algorithm theoretical basis 125
tion, especially for tropospheric SO2. Consequently, SO2 is
traditionally retrieved (for GOME, SCIAMACHY, GOME2, OMI) using sensitive windows in the 310–326 nm range.
Note that even in this range the SO2 absorption can be 3 orders of magnitude lower than that of ozone.
The TROPOMI SO2 algorithm is using a multiple-window
approach:
– 312–326 nm: classical fitting window, ideal for small
columns. This window is used as baseline. If nonlinear
effects due to high SO2 amounts are encountered, one
of the two following windows will be used instead.
– 325–335 nm: in this window, differential SO2 spectral
features are 1 order of magnitude smaller than in the
classical window. It allows the retrieval of moderate
SO2 columns, an approach similar to the one described
by Hörmann et al. (2013).
– 360–390 nm: SO2 absorption bands are 2–3 orders of
magnitude weaker than in the classical window and
are best suited for the retrieval of extremely high SO2
columns (Bobrowski et al., 2010)
Note that in the 325–335 and 360–390 nm windows the
Rayleigh scattering and ozone absorption are less important
than in the baseline 312–326 nm window (see also Fig. 3).
Specifically, in the first two intervals, absorption cross sections of O3 at 228 and 243 K are included in the fit and,
to better cope with the strong (nonlinear) ozone absorption
at short wavelengths, the retrieval also includes two pseudocross sections following the approach of Puk¯ıte et al. (2010):
λσO3
and σ
2
O3
calculated from the O3 cross-section spectrum
at 228 K. The correction for the Ring effect is based on the
technique outlined by Vountas et al. (1998). This technique
involves a PCA of a set of Ring spectra, calculated for a range
of solar zenith angles. The first two of the resulting eigenvectors appear to accurately describe the Ring spectra, with
the first eigenvector representing the filling-in of Fraunhofer
lines and the second mostly representing the filling-in of gas
absorption features. In the retrieval algorithm, these vectors
are determined by orthogonalizing two Ring spectra, calculated by LIDORT-RRS (Spurr et al., 2008), a version of LIDORT accounting for rotational Raman scattering, for a low
SZA (20◦
) and a high SZA (87◦
), respectively.
Wavelength calibration and convolution to TROPOMI
resolution
The quality of a DOAS fit critically depends on the accuracy
of the alignment between the earthshine radiance spectrum,
the reference spectrum and the cross sections. Although the
level 1b will contain a spectral assignment, an additional
spectral calibration is part of the SO2 algorithm. Moreover,
the DOAS spectral analysis also includes the fit of shift and
stretch of radiance spectra because the TROPOMI spectral
registration will differ from one ground pixel to another, e.g.,
due to thermal variations over the orbit as well as due to inhomogeneous filling of the slit in flight direction.
The wavelength registration of the reference spectrum can
be fine-tuned by means of a calibration procedure making
use of the solar Fraunhofer lines. To this end, a reference
solar atlas, Es
, accurate in absolute vacuum wavelength to
better than 0.001 nm (Chance and Kurucz, 2010) is degraded
at the resolution of the instrument, through convolution by
the TROPOMI instrumental slit function.
Using a nonlinear least-squares approach, the shift (1i)
between the reference solar atlas and the TROPOMI irradiance is determined in a set of equally spaced sub-intervals
covering a spectral range large enough to encompass all relevant fitting intervals. The shift is derived according to the
following equation:
E0 (λ) = Es(λ − 1i), (3)
where Es
is the solar spectrum convolved at the resolution of
the instrument and 1i
is the shift in sub-interval i. A polynomial is then fitted through the individual points in order
to reconstruct an accurate wavelength calibration 1(λ) for
the complete analysis interval. Note that this approach allows
one to compensate for stretch and shift errors in the original
wavelength assignment.
In the case of TROPOMI, the procedure is complicated by
the fact that such calibrations must be performed (and stored)
for each separate spectral field on the CCD detector array.
Indeed, due to the imperfect characteristics of the imaging
optics, each row of the TROPOMI instrument must be considered a separate spectrometer for analysis purposes.
In a subsequent step of the processing, the absorption cross
sections of the different trace gases must be convolved with
the instrumental slit function. The baseline approach is to use
slit functions determined as part of the TROPOMI key data.
Slit functions are delivered for each binned spectrum and as a
function of wavelength. Note that an additional feature of the
prototype algorithm allows for an effective slit function of
known line shape to be dynamically fitted (e.g., asymmetric
Gaussian). This can be used for verification and monitoring
purpose during commissioning and later on during the mission.
More specifically, wavelength calibrations are made for
each TROPOMI orbit as follows:

1. The TROPOMI irradiances (one for each row of the
CCD) are calibrated in wavelength over the 310–390 nm
wavelength range, using 10 sub-windows.
2. The earthshine radiances and the absorption cross sections are interpolated (cubic spline interpolation) on the
calibrated wavelength grid, prior to the DOAS analysis.
3. During spectral fitting, shift and stretch parameters are
further derived to align radiance and irradiance spectra.
<www.atmos-meas-tech.net/10/119/2017/> Atmos. Meas. Tech., 10, 119–153, 2017
126 N. Theys et al.: S-5P SO2 algorithm theoretical basis
Table 3. Criteria for selecting alternative fitting windows.
Window number w1 w2 w3
Wavelength range 312–326 nm 325–335 nm 360–390 nm
Derived slant column S1 S2 S3
Application Baseline for S1 > 15 DU S2 > 250 DU
every pixel and S2 > S1 and S3 > S2
The reference wavelength grid used in the DOAS procedure is the (optimized) grid of the TROPOMI solar
irradiance.
Spike removal algorithm
A method to remove individual hot pixels or detector pixels
affected by the South Atlantic Anomaly has been presented
for NO2 retrievals in Richter et al. (2011). Often only a few
individual detector pixels are affected, and in these cases, it is
possible to identify and remove the noisy points from the fit.
However, as the amplitude of the distortion is usually only of
the order of a few percent or less, it cannot always be found in
the highly structured spectra themselves. Higher sensitivity
for spikes can be achieved by analyzing the residual of the
fit where the contribution of the Fraunhofer lines, scattering,
and absorption is already removed.
When the residual for a single detector pixel exceeds the
average residual of all detector pixels by a chosen threshold ratio (the tolerance factor), the pixel is excluded from the
analysis, in an iterative process. This procedure is repeated
until no further outliers are identified, or until the maximum
number of iterations is reached (here fixed to 3). This is especially important to handle the degradation of 2-D detector
arrays such as OMI or TROPOMI. However, this improvement of the algorithm has a non-negligible impact on the
time of processing. At the time of writing, the exact values
for the tolerance factor and maximum number of iterations of
the spike removal procedure are difficult to ascertain and will
only be known during operations. To assess the impact on the
processing time, test retrievals have been done on OMI spectra using a tolerance factor of 5 and a limit of three iterations
(this could be relaxed), leading to an increase in processing
time by a factor of 1.5.
Fitting window selection
The implementation of the multiple-fitting-window retrieval
requires selection criteria for the transition from one window to another. These criteria are based on the measured
SO2 slant columns. As a baseline, the SO2 SCD in the 312–
326 nm window will be retrieved for each satellite pixel.
When the resulting value exceeds a certain criterion, the slant
column retrieval is taken from an alternative window. As part
of the algorithm development and during the verification exercise (Sect. 4), closed-loop retrievals have been performed
Figure 4. OMI SO2 vertical columns (DU) averaged for the year
2007 (top) with and (bottom) without background correction. Only
clear-sky pixels (cloud fraction lower than 30 %) have been kept.
AMFs calculated from SO2 profiles from the IMAGES global
model are applied to the slant columns (Theys et al., 2015).
and application of the algorithm to real data from the GOME2 and OMI instruments lead to threshold values and criteria
as given in Table 3.
2.2.2 Offset correction
When applying the algorithm to OMI and GOME-2 data,
across-track/viewing-angle-dependent residuals of SO2 were
found over clean areas and negative SO2 SCDs are found at
high SZA which need to be corrected (note that this is a common problem of most algorithms to retrieve SO2 from space
UV sensors). A background correction scheme was found
mostly necessary for the SO2 slant columns retrieved in the
baseline fitting window. The adopted correction scheme depends on across-track position and measured O3 slant column as described below.
Atmos. Meas. Tech., 10, 119–153, 2017 <www.atmos-meas-tech.net/10/119/2017/>
N. Theys et al.: S-5P SO2 algorithm theoretical basis 127
The correction is based on a parameterization of the background values that are then subtracted from the measurements. The scheme first removes pixels with high SZA
(> 70◦
) or SCDs larger than 1.5 DU (measurements with presumably real SO2) and then calculates the offset correction
by averaging the SO2 data on an ozone slant column grid
(bins of 75 DU). This is done independently for each acrosstrack position and hemisphere, and the correction makes use
of measurements averaged over a time period of 2 weeks preceding the measurement of interest (to improve the statistics
and minimize the impact of a possible extended volcanic SO2
plume on the averaged values).
It should be noted that the O3 slant column is dependent
on the wavelength when applying the approach of Puk¯ıte et
al. (2010):
SCD(λ) = SCDT 1 + SCDT 2 + λSCDλ + σs(λ)SCDs
. (4)
SCDT 1 and SCDT 2 are the retrieved ozone slant columns
corresponding to the ozone cross sections at two temperatures (T 1, T 2) included in the fit. SCDλ and SCDs are the
retrieved parameters for the two pseudo-cross sections λ · σs
and σ
2
s
(σs being the O3 cross section at T 1). In order to apply the background correction, the O3 slant column expression (Eq. 4) is evaluated at 313 nm (read below).
An example of the effect of the background correction is
shown in Fig. 4 for OMI. One can see that after correction
(top panel) the retrievals show smooth/unstriped results and
values close to zero outside the polluted areas. In some regions (in particular at high latitudes), residual columns can
be found, but are generally lower than 0.2 DU.
For the two additional fitting windows, residual SO2 levels are relatively small in comparison to the column amounts
expected to be retrieved in these windows. However, simplified background corrections are also applied to the alternative windows: the offset corrections use parameterizations of
the background slant columns based on latitude (bins of 5◦
),
cross-track position and time (2-week moving averages as for
the baseline window). To avoid contamination by strong volcanic eruptions, only the pixels are kept with SCD less than
50 and 250 DU for the fitting windows 325–335 and 360–
390 nm, respectively.
It should be noted that the background corrections do not
imply saving 2 weeks of SO2 L2 data in intermediate products, but only the averaged values (6i=1, N SCDi/N) over
the predefined working grids (note: the numerators 6i=1, N
SCDi and denominators N are stored separately).
This background correction is well suited for the case of
a 2-D-detector array such as TROPOMI, for which acrosstrack striping can possibly arise due to imperfect crosscalibration and different dead/hot pixel masks for the CCD
detector regions. This instrumental effect can also be found
for scanning spectrometers, but since these instruments only
have one single detector, such errors do not appear as stripes.
These different retrieval artifacts can be compensated for (up
to a certain extent) using background corrections which depend on the across-track position. All of these corrections are
also meant to handle the time-dependent degradation of the
instrument. Note that experiences with OMI show that the
most efficient method to avoid across-track stripes in the retrievals is to use row-dependent mean radiances as control
spectrum in the DOAS fit.
2.2.3 Air mass factors
The DOAS method assumes that the retrieved slant column
(after appropriate background correction) can be converted
into a vertical column using a single air mass factor M (representative of the fitting interval):
M =
Ns
Nv
, (5)
which is determined by radiative transfer calculations with
LIDORT version 3.3 (Spurr, 2008). The AMF calculation is
based on the formulation of Palmer et al. (2001):
M =
Z
m
0
(p)·s(p)dp, (6)
with m0 = m(p)/Ctemp(p), where m(p) is the so-called
weighting function (WF) or pressure-dependent air mass factor, Ctemp is a temperature correction (see Sect. 2.2.3.7) and
s is the SO2 normalized a priori mixing ratio profile, as a
function of pressure (p).
The AMF calculation assumes Lambertian reflectors for
the ground and the clouds and makes use of pre-calculated
WF LUTs at 313, 326 and 375 nm (depending on the fitting
window used). Calculating the AMF at these three wavelengths was found to give the best results using closedloop retrievals (see Auxiliary material of Theys et al., 2015).
The WF depends on observation geometry (solar zenith angle: SZA; line-of-sight angle: LOS; relative azimuth angle:
RAA), total ozone column (TO3), scene albedo (alb), surface pressure (ps), cloud top pressure (pcloud) and effective
cloud fraction (feff).
Examples of SO2 weighting functions are displayed in
Fig. 5 (as a function of height for illustration purpose) and
show the typical variations in the measurement sensitivity as
a function of height, wavelength and surface albedo.
The generation of the WF LUT has been done for a large
range of physical parameters, listed in Table 4. In practice,
the WF for each pixel is computed by linear interpolation
of the WF LUT at the a priori profile pressure grid and using the auxiliary data sets described in the following subsections. Linear interpolations are performed along the cosine of
solar and viewing angles, relative azimuth angle and surface
albedo, while a nearest-neighbor interpolation is performed
in surface pressure. In particular, the grid of surface pressure
<www.atmos-meas-tech.net/10/119/2017/> Atmos. Meas. Tech., 10, 119–153, 2017
128 N. Theys et al.: S-5P SO2 algorithm theoretical basis
Table 4. Physical parameters that define the WF look-up table.
Parameter Number of
grid points
Grid values Symbol
Atmospheric pressure (hPa) 64 1056.77, 1044.17,1031.72, 1019.41, 1007.26, 995.25,
983.38, 971.66, 960.07, 948.62, 937.31, 926.14, 915.09,
904.18, 887.87, 866.35, 845.39, 824.87, 804.88, 785.15,
765.68, 746.70, 728.18, 710.12, 692.31, 674.73, 657.60,
640.90, 624.63, 608.58, 592.75, 577.34, 562.32, 547.70,
522.83, 488.67, 456.36, 425.80, 396.93, 369.66, 343.94,
319.68, 296.84, 275.34, 245.99, 210.49, 179.89, 153.74,
131.40, 104.80, 76.59, 55.98, 40.98, 30.08, 18.73, 8.86,
4.31, 2.18, 1.14, 0.51, 0.14, 0.03, 0.01, 0.001
pl
Altitude corresponding to
the atmospheric pressure,
using a US standard atmosphere (km)
64 −0.35, −0.25, −0.15, −0.05, 0.05, 0.15, 0.25, 0.35,
0.45, 0.55, 0.65, 0.75, 0.85, 0.95, 1.10, 1.30, 1.50, 1.70,
1.90, 2.10, 2.30, 2.50, 2.70, 2.90, 3.10, 3.30, 3.50, 3.70,
3.90, 4.10, 4.30, 4.50, 4.70, 4.90, 5.25, 5.75, 6.25, 6.75,
7.25, 7.75, 8.25, 8.75, 9.25, 9.75, 10.50, 11.50, 12.50,
13.50, 14.50, 16.00, 18.00, 20.00, 22.00, 24.00, 27.50,
32.50, 37.50, 42.50, 47.50, 55.00, 65.00, 75.00, 85.00,
95.00
zl
Solar zenith angle (◦
) 17 0, 10, 20, 30, 40, 45, 50, 55, 60, 65, 70, 72, 74, 76, 78,
80, 85
θ0
Line-of-sight angle (◦
) 10 0, 10, 20, 30, 40, 50, 60, 65, 70, 75 θ
Relative azimuth
angle (◦
)
5 0, 45, 90, 135, 180 ϕ
Total ozone column (DU) 4 205, 295, 385, 505 TO3
Surface albedo 14 0, 0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.3 0.4,
0.6, 0.8, 1.0
As
Surface/cloud top pressure
(hPa)
17 1063.10, 1037.90, 1013.30, 989.28, 965.83, 920.58,
876.98, 834.99, 795.01, 701.21, 616.60, 540.48, 411.05,
308.00, 226.99, 165.79, 121.11
ps
AMF wavelength 3 313, 326, 375
is very thin near the ground in order to minimize interpolation errors caused by the generally low albedo of ground surfaces. Furthermore, the LUT and model pressures are scaled
to the respective surface pressures in order to avoid extrapolations outside the LUT range.
Observation geometry
The LUT covers the full range of values for solar zenith angles, line-of-sight angles and relative azimuth angles that can
be encountered in the TROPOMI measurements. The observation geometry is readily present in the L1b data for each
satellite pixel.
Total ozone column
The measurement sensitivity at 313 nm is dependent on the
total ozone absorption. The LUT covers a range of ozone
column values from 200 to 500 DU for a set of typical ozone
profiles. The total ozone column is directly available from
the operational processing of the S-5P total ozone column
product.
Surface albedo
The albedo value is very important for PBL anthropogenic
SO2 but less critical for volcanic SO2 when it is higher in the
atmosphere. For the surface albedo dimension, we use the climatological monthly minimum Lambertian equivalent reflector (minLER) data from Kleipool et al. (2008) at 328 nm for
w1 and w2, and 376 m for w3. This database is based on OMI
measurements and has a spatial resolution of 0.5◦ × 0.5◦
.
Note that other surface reflectance databases with improved
spatial resolution (more appropriate for TROPOMI) will
likely become available and these data sets will be considered for next algorithmic versions.
Atmos. Meas. Tech., 10, 119–153, 2017 <www.atmos-meas-tech.net/10/119/2017/>
N. Theys et al.: S-5P SO2 algorithm theoretical basis 129
Figure 5. SO2 box AMFs at 313, 326 and 375nm for albedo of (a) 0.06 and (b) 0.8. SZA: 40◦
; LOS: 10◦
; RAA: 0◦
; surface height: 0 km.
Clouds
The AMF calculations for TROPOMI partly cloudy scenes
use the cloud parameters (cloud fraction fc, cloud albedo
Ac, cloud top pressure ctp) supplied by the nominal S-5P
cloud algorithm OCRA/ROCINN in its Clouds as Reflecting Boundaries (CRB) implementation (Loyola et al., 2016).
The cloud surface is considered to be a Lambertian reflecting
surface and the treatment of clouds is achieved through the
independent pixel approximation (IPA; Martin et al., 2002),
which considers an inhomogeneous satellite pixel as being
composed (as for the radiance intensity) of two independent
homogeneous scenes, one completely clear and the other
completely cloudy. The weighting function is expressed as
m(p) = 8mcloud (p) + (1 − 8)mclear(p), (7)
where 8 is the intensity-weighted cloud fraction or cloud radiance fraction:
8 =
feffIcloud
feffIcloud + (1 − feff)Iclear
. (8)
The suffixes “clear” and “cloudy” refer to the WF and intensity calculation corresponding to a fully clear or cloudy
pixel, respectively. The WF LUT is therefore accompanied
by an intensity LUT with the same input grids. Both LUTs
have been generated for a range of cloud cover fractions and
cloud top pressures.
Note that the variations in the cloud albedo are directly
related to the cloud optical thickness. Strictly speaking, in
a Lambertian (reflective) cloud model approach, only thick
clouds can be represented. An effective cloud fraction corresponding to an effective cloud albedo of 0.8 (feff ∼= fc
Ac
0.8
)
can be defined in order to transform optically thin clouds into
equivalent optically thick clouds of reduced extent. Note that
in some cases (thick clouds with Ac > 0.8) the effective cloud
fraction can be larger than one and the algorithm assumes
feff = 1. In such altitude-dependent air mass factor calculations, a single cloud top pressure is assumed within a given
viewing scene. For low effective cloud fractions (feff lower
than 10 %), the current cloud top pressure output is highly
unstable and it is therefore reasonable to consider the observation a clear-sky pixel (i.e., the cloud fraction is set to
0 in Eq. 8) in order to avoid unnecessary error propagation
through the retrievals, which can be as high as 100 %. Moreover, it has been shown recently by Wang et al. (2016) using multi-axis DOAS (MAX-DOAS) observations to validate
satellite data that, in the case of elevated aerosol loadings in
the PBL (typically leading to apparent feff up to 10 %), it
is recommended to apply clear-sky AMFs rather than total
AMFs (based on cloud parameters) that presumably correct
implicitly for the aerosol effect on the measurement sensitivity.
It should be noted that the formulation of the pressuredependent air mass factor for a partly cloudy pixel implicitly includes a correction for the SO2 column lying below
the cloud and therefore not seen by the satellite, the socalled ghost column. Indeed, the total AMF calculation as
expressed by Eqs. (6) and (7) assumes the same shape factor and implies an integration of the a priori profile from
the top of the atmosphere to the ground, for each fraction
of the scene. The ghost column information is thus coming
from the a priori profile shapes. For this reason, only observations with moderate cloud fractions (feff lower than 30 %)
are used, unless it can be assumed that the cloud cover is
mostly situated below the SO2 layer, i.e., a typical situation
for volcanic plumes injected into the upper troposphere or
lower stratosphere.
<www.atmos-meas-tech.net/10/119/2017/> Atmos. Meas. Tech., 10, 119–153, 2017
130 N. Theys et al.: S-5P SO2 algorithm theoretical basis
Surface height
The surface height (zs) is determined for each pixel by interpolating the values of a high-resolution digital elevation map,
GMTED2010 (Danielson and Gesch, 2011).
Profile shapes
It is generally not possible to know at the time of observation
what the SO2 vertical profile is and whether the observed
SO2 is of volcanic origin or from pollution (or both). Therefore, the algorithm computes four vertical columns for different hypothetical SO2 profiles.
Three box profiles of 1 km thickness, located in the boundary layer, upper troposphere and lower stratosphere, are used.
The first box profile stands for typical conditions of well
mixed SO2 (from volcanic or anthropogenic emissions) in
the boundary layer, while the upper-troposphere and lowerstratosphere box profiles are representative of volcanic SO2
plumes from effusive and explosive eruptions, respectively.
In order to have more realistic SO2 profiles for polluted scenes, daily forecasts calculated with the global TM5
chemical transport model (Huijnen et al., 2010) will also
be used. TM5 will be operated with a spatial resolution
of 1◦ × 1
◦
in latitude and longitude, and with 34 sigma
pressure levels up to 0.1 hPa in the vertical direction. TM5
will use 3 h meteorological fields from the European Centre
for Medium-Range Weather Forecast (ECMWF) operational
model (ERA-Interim reanalysis data for reprocessing, and
the operational archive for real time applications and forecasts). These fields include global distributions of wind, temperature, surface pressure, humidity, (liquid and ice) water
content, and precipitation. A more detailed description of the
TM5 model is given at <http://tm.knmi.nl/> and by van Geffen
et al. (2016).
For the calculation of the air mass factors, the profiles are
linearly interpolated in space and time, at the pixel center
and S-5P local overpass time, through a model time step of
30 min. For NRT processing, the daily forecast of the TM5
model (located at KNMI) will be ingested by the UPAS operational processor.
To reduce the errors associated to topography and the
lower spatial resolution of the model compared to the
TROPOMI 7 km × 3.5 km spatial resolution, the a priori profiles need to be rescaled to effective surface elevation of the
satellite pixel. The TM5 surface pressure is converted by
applying the hypsometric equation and the assumption that
temperature changes linearly with height (Zhou et al., 2009):
ps = pTM5(
TTM5
(TTM5 + 0(zTM5 − zs))
)
−
g
R0 (9)
where pTM5 and TTM5 are the TM5 surface pressure and temperature, 0 = 6.5 K km−1
the lapse rate, zTM5 the TM5 terrain height, and zs surface elevation for the satellite ground
pixel. The TM5 SO2 profile is shifted to start at ps and scaled
so that volume mixing ratios are preserved (see Zhou et al.,
2009).
Temperature correction
The SO2 absorption cross sections of Bogumil et al. (2003)
show a clear temperature dependence which has an impact
on the retrieved SO2 SCDs depending on the fitting window used. However, only one temperature (203 K) is used for
the DOAS fit, therefore a temperature correction needs to be
applied: SCD’ = Ctemp.SCD. While the SO2 algorithm provides vertical column results for a set of a priori profiles, applying this correction to the slant column is not simple and as
a workaround it is preferred to apply the correction directly
to the AMFs (or box AMFs to be precise) while keeping the
(retrieved) SCD unchanged: AMF’ = AMF/Ctemp. This formulation implicitly assumes that the AMF is not strongly affected by temperature, which is a reasonable approximation
(optically thin atmosphere). The correction to be applied requires a temperature profile for each pixel (which is obtained
from the TM5 model):
Ctemp = 1/[1 − α.(T [K] − 203)], (10)
where α equals 0.002, 0.0038 and 0 for the fitting windows
312–326, 325–335 and 360–390 nm, respectively. The parameter α has been determined empirically by fitting Eq. (10)
through a set of data points (Fig. 6), for each fitting window.
Each value in Fig. 6 is the slope of the fitting line between
the SO2 differential cross sections at 203 K vs. the cross
section at a given temperature. In the fitting window 360–
390 nm, no temperature correction is applied (α = 0) because
the cross sections are quite uncertain. Moreover, the 360–
390 nm wavelength range is meant for extreme cases (strong
volcanic eruptions) for SO2 plumes in the lower stratosphere,
where a temperature of 203 K is a good baseline.
Aerosols
The presence of aerosol in the observed scene (likely when
observing anthropogenic pollution or volcanic events) may
affect the quality of the SO2 retrieval (e.g., Yang et al.,
2010). No explicit treatment of aerosols (absorbing or not)
is foreseen in the algorithm as there is no general and easy
way to treat the aerosols effect on the retrieval. At processing time, the aerosol parameters (e.g., extinction profile or
single-scattering albedo) are unknown. However, the information on the S-5P UV absorbing aerosol index (AAI) by
Zweers (2016) will be included in the L2 SO2 files as it
gives information to the users on the presence of aerosols
for both anthropogenic and volcanic SO2. Nevertheless, the
AAI data should be used/interpreted with care. In an offline
future version of the SO2 product, absorbing aerosols might
be included in the forward model, if reliable information on
Atmos. Meas. Tech., 10, 119–153, 2017 <www.atmos-meas-tech.net/10/119/2017/>
N. Theys et al.: S-5P SO2 algorithm theoretical basis 131
Figure 6. Effect of temperature (relative to 203 K) on SO2 retrieved SCD for fitting windows 312–326 (left) and 325–335 nm (right). The
red lines show the adopted formulation of Ctemp (Eq. 10). Note that, for the 312–326 nm window, the result at 273K has been discarded from
the fit as it is seems rather inconsistent with the dependence at other temperatures.
absorbing aerosol can be obtained from the AAI and the S-5P
aerosol height product (Sanders and de Haan, 2016).
3 Error analysis
3.1 Introduction
The total uncertainty (accuracy and precision) on the SO2
columns produced by the algorithm presented in Sect. 2 is
composed of many sources of error (see also, e.g., Lee et al.,
2009). Several of them are related to the instrument, such
as uncertainties due to noise or knowledge of the slit function. These instrumental errors propagate into the uncertainty
on the slant column. Other types of error can be considered model errors and are related to the representation of the
physics in the algorithm. Examples of model errors are uncertainties on the trace gas absorption cross sections and the
treatment of clouds. Model errors can affect the slant column
results or the air mass factors.
The total retrieval uncertainty on the SO2 vertical columns
can be derived by error propagation, starting from Eq. (1)
and if one assumes uncorrelated retrieval steps (Boersma et
al., 2004; De Smedt et al., 2008):
σ
2
Nv
=
σNS
M
2

+

σN
back
S
M
2
+

NS − N
back
S

σM
M2
!2
, (11)
where σNs and σ
back
Ns are the errors on the slant column NS
and on the background correction N
back
S
, respectively.
The error analysis is complemented by the total column averaging kernel (AK) as described in Eskes and
Boersma (2003):
AK(p) =
m0
(p)
M
(12)
(m0
is the weighting function, Eq. 6), which is often used
to characterize the sensitivity of the retrieved column to a
change in the true profile.
3.2 Error components
The following sections describe and characterize 20 error
contributions to the total SO2 vertical column uncertainty.
These different error components and corresponding typical
values are summarized in Tables 5 and 6. Note that, at the
time of writing, the precise effect of several S-5P-specific
error sources are unknown and will be estimated during operations.
A difficulty in the error formulation presented above
comes from the fact that it assumes the different error
sources/steps of the algorithm to be independent and uncorrelated, which is not strictly valid. For example, the background correction is designed to overcome systematic features/deficiencies of the DOAS slant column fitting, and
these two steps cannot be considered independent. Hence,
summing up all the corresponding error estimates would lead
to overestimated error bars. Therefore, several error sources
will be discussed in the following subsections without giving actual values at this point. Their impact is included and
described in later subsections.
Another important point to note is that one should also (be
able to) discriminate systematic and random components of
<www.atmos-meas-tech.net/10/119/2017/> Atmos. Meas. Tech., 10, 119–153, 2017
132 N. Theys et al.: S-5P SO2 algorithm theoretical basis
Table 5. Systematic and random error components contributing to the total uncertainty on the SO2 slant column.

# Error source Type* Parameter uncertainty Typical uncertainty on SO2 SCD

1 SO2 absorption S 6 % (window 1) 6 %
cross section 6 % (window 2)
unknown (window 3)
2 SO2 and O3 absorption S & R Errors 9 & 10
3 Other atmospheric S & R Error 9
absorption or interference
4 Radiance shot noise R S/N = 800–1000 0.3–0.5 DU (window 1)
5 DU (window 2)
60 DU (window 3)
5 DOAS settings S 1 nm, polynomial order < 11 % (window 1)
< 6 % (window 2)
< 8 % (window 3)
6 Wavelength and S Wavelength calibration Wavelength calibration and spectral shifts
radiometric can be corrected by the
calibration algorithm to less than 5 % effect
on the slant column
Radiometric calibration Intensity offset correction in
Additive errors should principle treats (small)
remain below 2 % radiometric calibration errors
7 Spectral response TBD TROPOMI-specific
function Expected uncertainty: 10 %
8 Other spectral Strongly dependent –
features on interfering signal
9 Background S & R 0.2 DU
correction
∗ R: random; S: systematic.
a given error source V:
σ
2
V =
σ
2
V(rand)
n

+ σ
2
V(syst), (13)
here n is the number of pixels considered. However, they are
hard to separate in practice. Therefore, each of the 20 error
contributions are (tentatively) classified as either “random”
or “systematic” errors, depending on their tendencies to average out in space/time or not.
3.2.1 Errors on the slant column
Error sources that contribute to the total uncertainty on the
slant column originate both from instrument characteristics and uncertainties/limitations on the representation of the
physics in the DOAS slant column fitting algorithm. For the
systematic errors on the slant column, the numbers provided
in Table 5 have been determined based on sensitivity tests
(using the QDOAS software).
With all effects summed in quadrature, the various contributions are estimated to account for a systematic error of
about 20 % + 0.2 DU of the background-corrected slant column (σNs,syst = 0.2 × (Ns − Nback
s
)+ 0.2 DU).
For the random component of the slant column errors, the
error on the slant columns provided by the DOAS fit is considered (hereafter referred to as SCDE) as it is assumed to
be dominated by and representative of the different random
sources of error.
Error source 1: SO2 cross section
Systematic errors on slant columns due to SO2 cross-section
uncertainties are estimated to be around 6 % (Vandaele et
al., 2009) in window 1 (312–326 nm) and window 2 (325–
335 nm) and unknown in window 3 (360–390 nm). In addition, the effect of the temperature on the SO2 cross sections
has to be considered as well. Refer to Sect. 3.2.2 for a discussion of this source of error.
Atmos. Meas. Tech., 10, 119–153, 2017 <www.atmos-meas-tech.net/10/119/2017/>
N. Theys et al.: S-5P SO2 algorithm theoretical basis 133
Table 6. Systematic and random error components contributing to the total uncertainty on the SO2 air mass factor.

# Error Type1 Parameter Typical uncertainty on the AMF

uncertainty
10 AMF wavelength S 10 %
dependence
11 Model atmosphere S O3 profile ∼ 5–10 %
P, T profiles small
12 Forward model S < 5 % < 5 %
13 Surface albedo2 S 0.02 15 % (PBL)
5 % (FT)
1 % (LS)
14 Cloud fraction2 R 0.05 5 % (PBL)
15 % (FT)
1 % (LS)
15 Cloud top pressure2 R 50 hPa 50 % (PBL)
50 % (FT)
1 % (LS)
16 Cloud correction R < 5 % on yearly averaged data
17 Cloud model TBD
18 SO2 profile shape S anthropogenic SO2
20–35 %
volcanic SO2
large (low albedo),
< 50 %
(high albedo)
19 Aerosol S & R Anthropogenic SO2 ≈ 15 %
(Nowlan et al., 2011).
Volcanic SO2
(aerosols: ash/sulfate):
∼ 20 %
(Yang et al., 2010)
20 Temperature R ∼ 5 %
correction
1 R: random; S: systematic. 2 Effect on the AMF estimated from Fig. 6.
Error source 2: O3 and SO2 absorption
Nonlinear effects due to O3 absorption are to a large extent
accounted for using the Taylor expansion of the O3 optical
depth (Puk¯ı¸te et al., 2010). Remaining systematic biases are
then removed using the background correction; hence, residual systematic features are believed to be small (please read
also the discussion on errors 9 and 10). The random component of the slant column error contributes to SCDE.
Nonlinear effects due to SO2 absorption itself (mostly for
volcanic plumes) are largely handled by the triple windows
retrievals, but – as will be discussed in Sect. 4 – the transition between the different fitting windows is a compromise
and there are cases where saturation can still lead to rather
large uncertainties. However, those are difficult to assess on
a pixel-to-pixel basis.
Error source 3: other atmospheric
absorption/interferences
In some geographical regions, several systematic features in
the slant columns remain after the background correction
procedure (see discussion on error 9: background correction
error) and are attributed to spectral interferences not fully accounted for in the DOAS analysis, such as incomplete treatment of the Ring effect. This effect also has a random component and contributes to the retrieved SCD error (SCDE).
<www.atmos-meas-tech.net/10/119/2017/> Atmos. Meas. Tech., 10, 119–153, 2017
134 N. Theys et al.: S-5P SO2 algorithm theoretical basis
Error source 4: radiance shot noise
It has a major contribution to the SCDE and it can be estimated from typical S/N values of S-5P in UV band 3 (800–
1000, according to Veefkind et al., 2012). This translates to
typical SCD random errors of about 0.3–0.5, 5 and 60 DU for
window 1, 2 and 3, respectively. Note that real measurements
are needed to consolidate these numbers.
Error source 5: DOAS settings
Tests on the effect of changing the lower and upper limits
of the fitting windows by 1 nm and the order of the closure
polynomial (4 instead of 5) have been performed. Based on a
selection of orbits for the Kasatochi eruption (wide range of
measured SCDs), the corresponding SCD errors are less than
11, 6 and 8 % for window 1, 2 and 3, respectively.
Error source 6: wavelength and radiometric calibration
Tests on the effect of uncertainties in the wavelength calibration have been performed in the ESA CAMELOT study. The
numbers are for a shift of 1/20th of the spectral sampling in
the solar spectrum and 1/100th of the spectral sampling in
the earthshine spectrum. The shift can be corrected for, but
interpolation errors can still lead to a remaining uncertainty
of a few percent.
Regarding radiometric calibration, the retrieval result is in
principle insensitive to flat (spectrally constant) offsets on the
measured radiance because the algorithm includes an intensity offset correction. From the ESA ONTRAQ study it was
found that additive error signals should remain within 2 % of
the measured spectrum.
Error source 7: spectral response function
Uncertainties in the S-5P instrumental slit functions can lead
to systematic errors on the retrieved SO2 slant columns (to
be determined).
Error source 8: other spectral features
Unknown or untreated instrumental characteristics such as
stray light and polarization sensitivity can introduce spectral
features that may lead to bias in the retrieved slant column
data. To a certain extent these can be prevented by the DOAS
polynomial and the intensity offset correction settings, as
long as the perturbing signals are a smooth function of wavelength. Conversely, high-frequency spectral structures can
have potentially a large impact on SO2 retrievals depending
on their amplitude and whether they interfere with SO2 absorption structures. At the time of writing, it is hard to evaluate these measurement errors. Once the instrument will be
operating, such measurement errors will be characterized and
correct for, either as part of L1b processor or in the form of
pseudo-absorption cross sections in the DOAS analysis.
In the ONTRAQ study, testing sinusoidal perturbation signals showed that the effect of spectral features on the retrieval
result depends strongly on the frequency of the signal. Additive signals with an amplitude of 0.05 % of the measurement
affect the retrieved SO2 slant column by up to 30 %. The effect scales more or less linearly with the signal amplitude.
Error source 9: background/destriping correction
This error source is mostly systematic and important for
anthropogenic SO2 or for monitoring degassing volcanoes.
Based on OMI and GOME-2 test retrievals, the uncertainty
on the background correction is estimated to be < 0.2 DU.
This value accounts for limitations of the background correction and is compatible with residual slant columns values
typically found (after correction) in some clean areas (e.g.,
above the Sahara), or for a possible contamination by volcanic SO2, after a strong eruption.
3.2.2 Errors on the air mass factor
The error estimates on the AMF are listed in Table 6 and are
based on simulations and closed-loop tests using the radiative transfer code LIDORT. One can identify two sources of
errors on the AMF. First, the adopted LUT approach has limitations in reproducing the radiative transfer in the atmosphere
(forward model errors). Secondly, the error on the AMF depends on input parameter uncertainties. This contribution can
be broken down into a squared sum of terms (Boersma et al.,
2004):
σ
2
M =

∂M
∂alb
· σalb2
+

∂M
∂ctp
· σctp2
+

∂M
∂feff
· σfeff2
+

∂M
∂s
· σs
2
, (14)
where σalb, σctp, σfeff, σs are typical uncertainties on the
albedo, cloud top pressure, cloud fraction and profile shape,
respectively.
The contribution of each parameter to the total air mass
factor error depends on the observation conditions. The air
mass factor sensitivities ( ∂M
∂parameter), i.e., the air mass factor derivatives with respect to the different input parameters, can be derived for any particular condition of observation using the altitude-dependent AMF LUT, created with LIDORTv3.3, and using the a priori profile shapes. In practice,
a LUT of AMF sensitivities has been created using reduced
grids from the AMF LUT and a parameterization of the profile shapes based on the profile shape height.
Error source 10: AMF wavelength dependence
Because of strong atmospheric absorbers (mostly ozone) and
scattering processes, the SO2 AMF shows a wavelength dependence. We have conducted sensitivity tests to determine
Atmos. Meas. Tech., 10, 119–153, 2017 <www.atmos-meas-tech.net/10/119/2017/>
N. Theys et al.: S-5P SO2 algorithm theoretical basis 135
Figure 7. Retrieved SO2 slant columns versus simulated SCDs at
a wavelength of 313 nm from synthetic spectra (SZA: 30, 70◦
) in
the spectral range 312–326 nm and for SO2 layers in the boundary layer, upper troposphere and lower stratosphere. The different
points correspond to different values for the line-of-sight angle (0,
45◦
), surface albedo (0.06, 0.8), surface height (0, 5 km) and total
ozone column (350, 500 DU). SO2 vertical columns as input of the
RT simulations are a maximum of 25 DU.
the optimal wavelengths for AMF calculations representative
of each of the three fitting windows. To do so, synthetic radiances and SO2 SCDs have been generated using LIDORT for
typical observations scenarios and at spectral resolution and
sampling compatible with S-5P. The spectra have been analyzed by DOAS and the retrieved SCDs have been compared
to the calculated SCDs at different wavelengths. It appears
from this exercise that 313, 326 and 375 nm provide the best
results, for window 1, 2 and 3, respectively. Figure 7 shows
an illustration of these sensitivity tests in the baseline window; an excellent correlation and slope close to 1 is found for
the scatter plot of retrieved versus simulated slant columns
using an effective wavelength of 313 nm for the AMF. Overall, for low solar zenith angles, the deviations from the truth
are less than 5 % in most cases, except for boundary layer
(BL) SO2 at a 1 DU column level and for low-albedo scenes
(deviations up to 20 %). For high solar zenith angles deviations are less than 10 % in most cases, except for BL SO2 at a
1 DU column level and for low-albedo scenes (underestimation by up to a factor of 2).
Error source 11: model atmosphere
This error relates to uncertainties in the atmospheric profiles
used as input of LIDORT for the weighting function lookup-table calculations.
Although the effect of O3 absorption on the AMF is treated
in the algorithm, the O3 profiles used as input of LIDORT are
not fully representative of the real profiles and typical errors
(including error due to interpolation) of 5–10 % can occur.
A test has been performed by replacing the US standard atmosphere pressure and temperature profiles by high latitude
winter profiles and the impact on the results is found to be
small.
Error source 12: radiative transfer model
This error source is believed to be small, less than 5 % (Hendrick et al., 2006; Wagner et al., 2007).
Error source 13: surface albedo
A typical uncertainty on the albedo is 0.02 (Kleipool et al.,
2008). This translates to an error on the air mass factor after
multiplication by the slope of the air mass factor as a function of the albedo (Eq. 14) and can be evaluated for each
satellite pixel. As an illustration, Fig. 8 shows the expected
dependence of the AMF with albedo and also with the cloud
conditions. From Fig. 8a, one concludes that the retrievals of
SO2 in the BL are much more sensitive to the exact albedo
value than for SO2 higher up in the atmosphere, for this particular example.
More substantial errors can be introduced if the real albedo
differs considerably from what is expected, for example in
the case of the sudden snowfall or ice cover. The snow/ice
cover flag in the L2 file will therefore be useful for such
cases.
Error source 14: cloud fraction
An uncertainty on the cloud fraction of 0.05 is considered.
The corresponding AMF error can be estimated through
Eq. (14; see Fig. 8b) or by analytic derivation from Eqs. (6)–
(8).
Error source 15: cloud top pressure
An uncertainty on the cloud top height of 0.5 km (∼ 50 hPa)
is assumed. The corresponding AMF error can be estimated
through Eq. (14). Figure 8c illustrates the typical behavior
of signal amplification/shielding for a cloud below/above the
SO2 layer. One can see that the error (slope) dramatically
increases when the cloud is at a height similar to the SO2
bulk altitude.
Error source 16: cloud correction
Sensitivity tests showed that applying the independent pixel
approximation or assuming cloud-free pixels makes a difference of only 5 % on yearly averaged data (for anthropogenic
BL SO2 VC with cloud fractions less than 40 %).
Error source 17: cloud model
Cloud as layer (CAL) is the baseline of the S-5P cloud algorithm, but a Lambertian equivalent reflector (LER) implementation will be used for NO2, SO2 and HCHO retrievals.
The error due to the choice of the cloud model will be evaluated during the operational phase.
<www.atmos-meas-tech.net/10/119/2017/> Atmos. Meas. Tech., 10, 119–153, 2017
136 N. Theys et al.: S-5P SO2 algorithm theoretical basis
Figure 8. Air mass factors at 313 nm for SO2 in the boundary layer (BL: 0–1 km), free troposphere and lower stratosphere (FT, LS: Gaussian
profiles with maximum height at 6,15 km; FWHM: 1 km). Calculations are for SZA = 40◦
, Los = 10◦
, RAA = 0
◦
and surface height = 0 km.
AMFs are displayed as a function of the (a) albedo for clear-sky conditions, (b) cloud fraction for albedo = 0.06, cloud albedo = 0.8 and
cloud top height = 2 km and (c) cloud top height for albedo = 0.06, cloud albedo = 0.8 and cloud fraction = 0.3.
Error source 18: profile shape
A major source of systematic uncertainty for most SO2
scenes is the shape of the vertical SO2 distribution. The corresponding AMF error can be estimated through Eq. (14) and
estimation of uncertainty on the profile shape. Note that vertical columns are provided with their averaging kernels, so
that column data might be improved for particular locations
by using more accurate SO2 profile shapes based on input
from models or observations.
For anthropogenic SO2 under clear-sky conditions, sensitivity tests using a box profile from 0 to 1 ± 0.5 km
above ground level, or using the different profiles from the
CAMELOT study (Levelt et al., 2009), give differences in
AMFs in the range of 20–35 %. Note that for particular
conditions SO2 may also be uplifted above the top of the
boundary layer and sometimes reach upper-tropospheric levels (e.g., Clarisse et al., 2011). SO2 weighting functions displayed in Fig. 5 show that the measurement sensitivity is then
increased by up to a factor of 3 and therefore constitutes a
major source of error.
In the SO2 algorithm, the uncertainty on the profile shape
is estimated using one parameter describing the shape of the
TM5 profile: the profile height, i.e., the altitude (pressure)
below which resides 75 % of the integrated SO2 profile. ∂M
∂s
is approached by ∂M
∂sh
, where sh is half of the profile height.
Relatively small variations in this parameter have a strong
impact on the total air mass factors for low-albedo scenes,
because altitude-resolved air mass factors decrease strongly
in the lower troposphere, where the SO2 profiles peak (see,
e.g., Fig. 5).
For volcanic SO2, the effect of the profile shape uncertainty depends on the surface or cloud albedo. For low-albedo
scenes (Fig. 5a), if no external information on the SO2 plume
height is available, it is a major source of error at all wavelengths. Vertical columns may vary by up to a factor of 5.
For high-albedo scenes (Fig. 5b), the error is less than 50 %.
It should be noted that these conditions are often encountered for strong eruptions injecting SO2 well above the cloud
deck (high reflectivity). Further uncertainty on the retrieved
SO2 column may arise if the vertical distribution shows disAtmos. Meas. Tech., 10, 119–153, 2017 <www.atmos-meas-tech.net/10/119/2017/>
N. Theys et al.: S-5P SO2 algorithm theoretical basis 137
tinct layers at different altitudes, due to the different nature
of successive phases of the eruption.
In the SO2 algorithm, three 1 km thick box profiles are
used in the AMF calculations, mostly to represent typical
volcanic SO2 profiles. The error due to the profile shape uncertainty is estimated by varying the box center levels by
100 hPa.
Error source 19: aerosols
The effect of aerosols on the air mass factors are not explicitly considered in the SO2 retrieval algorithm. To some
extent, however, the effect of the non-absorbing part of the
aerosol extinction is implicitly included in the cloud correction (Boersma et al., 2004). Indeed, in the presence of
aerosols, the cloud detection algorithm is expected to overestimate the cloud fraction, resulting partly in a compensation effect for cases where aerosols and clouds are at similar heights. Absorbing aerosols have a different effect on the
air mass factors and can lead to significant errors for high
aerosol optical depths (AODs). In the TROPOMI SO2 product, the absorbing aerosol index field can be used to identify
observations with elevated absorbing aerosols.
Generally speaking, the effect of aerosols on AMF is
highly variable and strongly depends on aerosol properties
(AOD, height and size distribution, single-scattering albedo,
scattering phase function, etc.). Typical AMFs uncertainties
due to aerosols found in the literature are given in Table 6. As
aerosols affect cloud fraction, cloud top height and to some
extent the albedo database used, correlations between uncertainties on these parameters are to be expected.
Error source 20: temperature correction
The DOAS scheme uses an SO2 cross section at only one
temperature (Bogumil et al., 2003, at 203 K), which is in
general not representative of the effective temperature corresponding to the SO2 vertical profile. This effect is in principle accounted for by the temperature correction (which is
applied in practice to the AMFs; see Sect. 2.2.3.7) but with a
certain associated error of ∼ 5 %.
4 Verification
The SO2 retrieval algorithm presented in Sect. 2, and hereafter referred as “prototype algorithm”, has been applied to
OMI and GOME-2 spectra. The results have been extensively
verified and validated against different satellite and groundbased data sets (e.g., Theys et al., 2015; Fioletov et al., 2016;
Wang et al., 2016). Here we report on further scientific verification activities that took place during the ESA S-5P L2WG
project.
In addition to the prototype algorithm, a scientific algorithm (referred as “verification algorithm”) has been developed in parallel. Both algorithms have been applied to synthetic and real (OMI) spectra and results were compared. In
this study, we only present and discuss a selection of results
(for OMI).
4.1 Verification algorithm
The S-5P TROPOMI verification algorithm was developed
in close cooperation between the Max Planck Institute for
Chemistry (MPIC) in Mainz (Germany) and the Institut für
Methodik und Fernerkundung as part of the Deutsches Institut für Luft- und Raumfahrt Oberpfaffenhofen (DLR-IMF).
Like the prototype algorithm (PA), the verification algorithm
(VA) uses a multiple fitting window DOAS approach to avoid
nonlinear effects during the SCD retrieval in the case of high
SO2 concentrations in volcanic plumes. However, especially
the alternatively used fitting windows differ strongly from the
ones used for the PA and are entirely located in the lower UV
range:
– 312.1–324 nm (standard retrieval – SR): similar to baseline PA fitting window, ideal for small columns
– 318.6–335.1 nm (medium retrieval – MR): this fitting
window is essentially located in between the first and
second fitting window of the PA and was mainly introduced to guarantee a smoother transition between the
baseline window and the one used for high SO2 concentrations. The differential SO2 spectral features are still
about 1 order of magnitude smaller than in the baseline
window.
– 323.1–335.1 nm (alternative retrieval – AR): similar to
the intermediate fitting window of the PA. This fitting
window is used in the case of high SO2 concentrations.
Although it is expected that volcanic events with extreme SO2 absorption are still affected by nonlinear absorption in this window, the wavelength range is sufficient for most volcanic events.
Furthermore, the VA selection criteria for the transition from
one window to another are not just based on fixed SO2 SCD
thresholds. The algorithm allows for a slow and smooth transition between different fit ranges by linearly decreasing the
weight of the former fitting window and at the same time increasing the weight of the following fitting window:

1. for SO2 SCD ≤ 4 × 1017 molec cm−2
(≈ 15 DU):
SO2 SCD = SR;
2. for 4 × 1017 molec cm−2 < SO2 SCD < 9 × 1017 molec
cm−2
:
SO2 SCD = SR ×

1 −
SR
9 × 1017 molec cm−2


+ MR ×

SR
9 × 1017 molec cm−2

;
<www.atmos-meas-tech.net/10/119/2017/> Atmos. Meas. Tech., 10, 119–153, 2017
138 N. Theys et al.: S-5P SO2 algorithm theoretical basis

3. for SO2 SCD ≥ 9 × 1017 molec cm−2
(≈ 33 DU):
SO2 SCD = MR;
2. for 9 × 1017 molec cm−2 < SO2 SCD < 4.6 × 1018
molec cm−2
:
SO2 SCD = MR ×

1 −
MR
4.6 × 1018 molec cm−2


+ AR ×

AR
4.6 × 1018 molec cm−2

;

5. for SO2 SCD ≥ 4.6 × 1018 molec cm−2
(≈ 171 DU):
SO2 SCD = AR.
To convert the final SO2 SCDs into vertical column densities, a single-wavelength AMF for each of the three fitting
windows (SO2 SR, MR and AR) is calculated using the LIDORT LRRS v2.3 (Spurr et al., 2008). The AMF depends
on the viewing angles and illumination, surface and cloud
conditions as well as on the O3 total column, which is taken
from the O3 total column retrieval. A cloudy and clear-sky
AMF is calculated using temperature-dependent cross sections for SO2 (Bogumil et al., 2003) and O3 (Brion et al.,
1984): AMF(λ) =
ln
I+SO2
I−SO2

τSO2
with (I+SO2
) and (I−SO2
) being
simulated earthshine spectra with and without including SO2
as a trace gas, respectively. Both AMFs are combined using
the cloud fraction information. Like the PA, the VA is calculated for different a priori SO2 profiles (center of mass at 2.5,
6 and 15 km) and a temperature correction is applied (see
Sect. 2.2.3.7). In contrast to the PA the VA uses Gaussianshaped SO2 profiles with a FWHM of 2.5km rather than box
profiles as in the PA. This choice, however, has only a minor
influence on the AMF.
For further details on the VA, the reader is referred to
the S-5P Science Verification Report (available at https://
earth.esa.int/web/sentinel/user-guides/sentinel-5p-tropomi/
document-library/-/asset_publisher/w9Mnd6VPjXlc/
content/sentinel-5p-tropomi-science-verification-report) for
more detailed description and results.
4.2 Verification results
For the intercomparison, the prototype algorithm and verification algorithm were applied to OMI data for three different
SO2 emission scenarios: moderate volcanic SO2 VCDs on 1
May 2005, caused by the eruption of the Anatahan volcano,
elevated anthropogenic SO2 VCDs, on 1 May 2005, from the
Norilsk copper smelter (Russia), and strongly enhanced SO2
VCDs, on 8 August 2008, after the massive eruption of Mt.
Kasatochi.
In the following, both algorithms use the same assumption
of an SO2 plume located at 15 km altitude for the AMF calculation. Even if this choice is not realistic for some of the presented scenarios, it minimizes the influence of differences in
the a priori settings. Main deviations between prototype and
verification algorithm are therefore expected to be caused by
the usage of different fit windows (determining their sensitivity and fit error) and especially the corresponding transition
criteria.
Figure 9 shows the resulting maps of the SO2 VCD for
the VA (upper panels) and PA (lower panels) for the three
selected test cases. As can be seen, both algorithms result in
similar SO2 VCDs; however, a closer look reveals some differences, such as the maximum VCDs, which are not necessarily appearing at the same locations. For the Anatahan case
for instance, the maximum VCD is seen closer to the volcano
at the eastern end of the plume for the PA, while it appears to
be further downwind for the VA. This effect can be explained
by the corresponding fit windows used for both algorithms,
which may result in deviating SO2 VCDs, especially for SO2
scenarios where the best choice is difficult to assess. This is
illustrated in Fig. 10, showing scatter plots of VA versus PA
SO2 VCDs for the three test cases (Anatahan, Norilsk and
Kasatochi) color-coded differently depending on the fitting
window used for VA (left) and PA (right), respectively. While
the PA uses strictly separated results from the individual fit
windows, the VA allows a smooth transition whenever resulting SO2 SCDs are found to be located in between subsequent
fit ranges.
For all three test cases, it appears that the PA is less affected by data scattering for low SO2 or SO2 free measurements than the VA. For the shortest UV fit windows, both
algorithms mainly agree, but VA VCDs tend to be higher by
10–15 % than the PA VCDs for the Anatahan and Kasatochi
measurements but interestingly not for the Norilsk case. For
SO2 VCDs around 7 DU the PA seems to be slightly affected
by saturation effects in 312–326 nm window, while VA already makes use of a combined SR/MR SCD. For larger SO2
VCDs (> 10 DU), data sets from both algorithms show an increased scattering, essentially resulting from the more intensive use of fitting windows at longer wavelengths (for which
the SO2 absorption is weaker). While it is difficult to conclude which algorithm is closer to the actual SO2 VCDs,
the combined fit windows of the VA probably are better
suited (in some SO2 column ranges) for such scenarios as the
SO2 cross section is generally stronger for lower wavelength
(< 325 nm) when compared to the intermediate fit window of
the PA.
For extremely high SO2 loadings, i.e., for the Kasatochi
plume on 8 August 2008, the DOAS retrievals from PA and
VA require all three fit windows to prevent systematic underestimation of the resulting SO2 SCDs due to nonlinear absorption caused by very high SO2 concentrations within the
volcanic plume. Figure 9 (right panel) shows that the SO2
distribution is similar for both algorithms, including the location of the maximum SO2 VCD.
From Fig. 10 (lowest panel), it can be seen that the VA
shows higher values for SO2 VCDs < 100 DU, for all three
fit windows. For very high SO2 VCDs, it seems that the verAtmos. Meas. Tech., 10, 119–153, 2017 <www.atmos-meas-tech.net/10/119/2017/>
N. Theys et al.: S-5P SO2 algorithm theoretical basis 139
Figure 9. OMI SO2 VCD (expressed in DU) for the verification (upper panels) and prototype algorithms (lower panels) for the three selected
scenarios: during the Anatahan eruption (left), over the Norilsk copper smelter area (center) and for the volcanic eruption of Kasatochi (right).
Note that, for each case, the color bar has been scaled to the maximum SO2 VCD from both algorithms.
ification algorithm is already slightly affected by an underestimation of the SO2 VCD caused by nonlinear radiative
transfer effects in the SO2 AR fit window, while the PA retrievals in the 360–390 nm fit range are insensitive to saturation effects. We note, however, that the Kasatochi plume
also contained significant amounts of volcanic ash and we
cannot rule out a possible retrieval effect of volcanic ash on
the observed differences between PA and VA SO2 results.
Finally ,we have also investigated other cases with extreme
concentrations of SO2, and contrasting results were found
compared to the Kasatochi case. For example, on 4 September 2014, PA retrieved up to 260 DU of SO2 during the Icelandic Bárðarbunga fissure eruption, while VA only found
150 DU (not shown). Compared to Kasatochi, we note that
this specific scenario is very different as for the plume height
(the SO2 plume was typically in the lowermost troposphere
∼ 3 km a.s.l.) and it is likely to play a role in the discrepancy
between PA and VA results.
In summary, we found that the largest differences between
prototype and verification algorithms are due to the fitting
window transitions and differences of measurement sensitivity of the fitting windows used (all subject differently to
nonlinear effects). Verification results have shown that the
prototype algorithm produces reasonable results for all the
expected scenarios, from modest to extreme SO2 columns,
and are therefore adequate for treating the TROPOMI data.
In a future processor update, the method could, however, be
refined.
5 Validation of TROPOMI SO2 product
In this section, we give a brief summary of possibilities (and
limitations) to validate the TROPOMI SO2 product with independent measurements.
Generally speaking, the validation of a satellite SO2 column product is a challenge for several reasons, on top of
which is the representativeness of the correlative data when
compared to the satellite retrievals. Another reason comes
from the wide range of SO2 columns in the atmosphere that
vary from about 1 DU level for anthropogenic SO2 and lowlevel volcanic degassing to 10–1000 DU for medium to extreme volcanic explosive eruptions.
The space-borne measurement of anthropogenic SO2 is
difficult because of the low column amount and reduced measurement sensitivity close to the surface. The SO2 signal is
covered by the competing O3 absorption and the column accuracy is directly affected by the quality of the background
correction applied. Among the many parameters of the SO2
retrieval algorithm that affect the results, the SO2 vertical
profile shape is of utmost importance for any comparison
with correlative data. The SO2 column product accuracy is
also directly impacted by the surface albedo used as input
for the AMF calculation, the cloud correction/filtering and
aerosols. In principle, all these effects will have to be addressed in future validation efforts.
The measurement of volcanic SO2 is facilitated by SO2
columns often larger than for anthropogenic SO2. However,
<www.atmos-meas-tech.net/10/119/2017/> Atmos. Meas. Tech., 10, 119–153, 2017
140 N. Theys et al.: S-5P SO2 algorithm theoretical basis
Figure 10. OMI SO2 VCD (DU) scatter plots for PA (x axis) and VA (y axis) for the three test cases: the Anatahan eruption, Norislk
anthropogenic emissions and the Kasatochi eruption (from top to bottom). The different fit windows used for both algorithms are colorcoded: VA on left panels (blue: SR; purple: SR/MR; green: MR; orange: MR/AR; red: AR), PA on right panels (blue: 312–326 nm; green:
325–335 nm; red: 360–390 nm). For the three scenarios, the prototype and verification algorithms agree fairly well with r
2 ∼ 0.9.
Atmos. Meas. Tech., 10, 119–153, 2017 <www.atmos-meas-tech.net/10/119/2017/>
N. Theys et al.: S-5P SO2 algorithm theoretical basis 141
the total SO2 column is strongly dependent on the height
of the SO2 plume, which is highly variable and usually unknown. For most volcanoes, there is no ground-based equipment to measure SO2 during an appreciable eruption and
even if it is the case, the data are generally difficult to use for
validation. For strong eruptions, volcanic plumes are transported over long distances and can be measured by groundbased and aircraft devices, but generally there are only a
handful of data sets available and the number of coincidences
is rather small.
For both anthropogenic and volcanic SO2 measurements,
the vertical distribution of SO2 is a key parameter limiting
the product accuracy. If reliable (external) information on the
SO2 profile (or profile shape) is available, it is recommended
to recalculate the SO2 vertical columns by using this piece
of information and the column averaging kernels that can be
found in the TROPOMI SO2 L2 files.
5.1 Ground-based measurements
When considering the application of ground-based instruments for the validation of satellite SO2 observations, several
types of instruments are to be considered.
Brewer instruments have the advantage to operate as part
of a network (<http://www.woudc.org>), but the retrieved SO2
columns are generally found inaccurate for the validation of
anthropogenic SO2. Yet in some cases they might be used for
coincidences with volcanic clouds, typically for SO2 VCDs
larger than 5–10 DU. Multi-axis DOAS (MAX-DOAS) or
direct-sun DOAS measurements (e.g., from Pandora instruments) can be used to validate satellite SO2 columns from
anthropogenic emissions (e.g., Theys et al., 2015; Jin et al.,
2016; Wang et al., 2016), but caution must be exercised in
the interpretation of the results because realistic SO2 profile shapes must be used by the satellite retrieval scheme.
While direct-sun DOAS retrievals are independent of the
SO2 profile shape, MAX-DOAS observations carry information on the SO2 vertical distribution, but it is not obvious that the technique is directly applicable to the validation of satellite SO2 retrievals, because the technique is not
able to retrieve the full SO2 profile. Another important limitation comes from the fact that ground-based DOAS and
satellite instruments have very different fields of view and
are therefore probing different air masses. This can cause a
large discrepancy between ground-based and satellite measurements in the case of strong horizontal gradients of the
SO2 column field. DOAS instruments scanning through volcanic plumes are now routinely measuring volcanic SO2
emissions, as part of the Network for Observation of Volcanic and Atmospheric Change (NOVAC; Galle et al., 2010),
for an increasing number of degassing volcanoes. Ongoing
research focusses on calculating SO2 fluxes from those measurements and accounting for nontrivial radiative transfer effects (e.g., light dilution; see Kern et al., 2009). NOVAC flux
data could be used for comparison with TROPOMI SO2 data,
but this requires techniques to convert satellite SO2 vertical column into mass fluxes (see, e.g., Theys et al., 2013,
and references therein; Beirle et al., 2014). Similarly, fastsampling UV cameras are becoming increasingly used to
measure and invert SO2 fluxes and are also relevant to validate TROPOMI SO2 data over volcanoes or anthropogenic
point sources (e.g., power plants). It should be noted, however, that ground-based remote sensing instruments operating nearby SO2 point sources are sensitive to newly emitted SO2 plumes, while a satellite sensor like TROPOMI will
measure aged plumes that have been significantly depleted
in SO2. While in some cases it is possible to compensate for
this effect by estimating the SO2 lifetime, e.g., directly from
the space measurements (Beirle et al., 2014), the general situation is that the SO2 loss rate is highly variable (especially
in volcanic environments), and this can lead to strong discrepancies when comparing satellite and ground-based SO2
fluxes.
In addition to optical devices, there are also in situ instruments measuring surface SO2 mixing ratios. This type of instrument can only validate surface concentrations, and additional information on the SO2 vertical profile (e.g., from
model data) is required to make the link with the satellite
retrieved column. However, in situ instruments are being operated for pollution monitoring in populated areas, and allow
for extended and long-term comparisons with satellite data
(see, e.g., Nowlan et al., 2011).
5.2 Aircraft and mobile measurements
Airborne and mobile instruments provide valuable and complementary data for satellite validation.
In the case of volcanic explosive eruptions, satisfactory
validation results can be obtained by comparing satellite and
fixed ground DOAS measurements of drifting SO2 plumes,
as shown by Spinei et al. (2010), but the comparison generally suffers from the small number of coincidences. Dedicated aircraft campaign flights (e.g., Schumann et al., 2011)
can in principle improve the situation. Their trajectory can
be planned with relative ease to cross sustained eruptive
plumes. However, localized high SO2 concentrations may be
carried away too quickly to be captured by aircraft or have
diluted below the threshold limit for satellite detection before an aircraft can respond. An important database of SO2
aircraft measurements is provided by the CARIBIC/IAGOS
project, which exploits automated scientific instruments operating long-distance commercial flights. Measurements of
volcanic SO2 during the eruptions of Mt. Kasatochi and Eyjafjallajökull and comparison with satellite data have been
reported by Heue et al. (2010, 2011).
An attempt to validate satellite SO2 measurements using a mobile DOAS instrument for a fast moving (stratospheric) volcanic SO2 plume was presented by Carn and
Lopez (2011). Although the agreement between both data
sets was found reasonable, the comparison was complicated
<www.atmos-meas-tech.net/10/119/2017/> Atmos. Meas. Tech., 10, 119–153, 2017
142 N. Theys et al.: S-5P SO2 algorithm theoretical basis
Figure 11. Comparison of SO2 SCDs between prototype algorithm
and operational processor for the OMI test data of 8 August 2008.
by the relatively fast displacement of the volcanic cloud with
respect to the ground spectrometer and clear heterogeneity on
scales smaller than a satellite pixel. For degassing volcanoes
or new fissure eruptions, mobile DOAS traverse measurements under the plume offer unique opportunities to derive
volcanic SO2 fluxes that could be used to validate satellite
measurements.
For polluted regions, measurements of anthropogenic
SO2 by airborne nadir-looking DOAS sensors are able to
produce high-spatial-resolution mapping of the SO2 column field (e.g., during the AROMAT campaigns, http://
uv-vis.aeronomie.be/aromat/) that could be used to validate
TROPOMI SO2 product or give information on horizontal
gradients of the SO2 field (e.g., in combination with coincident mobile DOAS measurements) that would be particularly useful when comparing satellite and MAX-DOAS data
(see discussion in Sect. 5.1). Equally important are also limbDOAS or in situ instruments to provide information on the
vertical distribution of SO2 which is crucial for satellite validation (e.g., Krotkov et al., 2008).
5.3 Satellite measurements
Intercomparison of satellite SO2 measurements generally
provides a convenient and easy way to evaluate at a glance
the quality of a satellite product, for instance by comparing
SO2 maps. Often, it also provides improved statistics and geographical representativeness, but it poses a number of problems because, when different satellite sensors are compared,
they have also different overpass times, swaths, spatial resolutions and measurement sensitivities to SO2.
For volcanic SO2, satellite measurements often provide the
only data available for the first hours to days after an eruption event and satellite intercomparison is thus the only practical way to assess the quality of the retrievals. To overcome
sampling issues mentioned above, intercomparison of SO2
masses integrated over the measured volcanic plume is often performed. For TROPOMI, current satellite instruments
will be an important source of data for cross-comparisons.
Although non-exhaustive, the following is a list of satellite
sensors that could be used: OMI, OMPS, GOME-2 and IASI
(MetOp-A, -B, and the forthcoming -C), AIRS, CrIS, VIIRS and MODIS. As mentioned above, the intercomparison
of satellite SO2 products is difficult and in this respect the
plume altitude is a key factor of the satellite SO2 data accuracy. Comparison of TROPOMI and other satellite SO2 products will benefit not only from the advent of scientific algorithms for the retrieval of SO2 plume heights but also from
the use of volcanic plume height observations using space lidar instruments (e.g., CALIOP and the future EarthCare mission).
For both anthropogenic SO2 and volcanic degassing SO2,
the satellite UV sensors OMI, GOME-2 and OMPS can be
compared to TROPOMI SO2 data by averaging data over
certain polluted regions. This procedure will give valuable
information on the data quality, but, in some cases, the comparison will suffer from differences in spatial resolution. A
more robust and in-depth comparison would be to use different TROPOMI SO2 data sets generated by different retrieval
algorithms and investigate the differences in the various retrieval steps (spectral fitting, corrections, radiative transfer
simulations, error analysis).
6 Conclusions
Based on the heritage from GOME, SCIAMACHY, GOME2 and OMI, a DOAS retrieval algorithm has been developed
for the operational retrieval of SO2 vertical columns from
TROPOMI level 1b measurements in the UV spectral range.
Here we describe its main features.
In addition to the traditionally used fitting window of 312–
326 nm, the new algorithm allows for the selection of two additional fitting windows (325–335 and 360–390 nm), reducing the risk of saturation and ensuring accurate SO2 column
retrieval even for extreme SO2 concentrations as observed
for major volcanic events. The spectral fitting procedure also
includes an advanced wavelength calibration scheme and a
spectral spike removal algorithm.
After the slant column retrieval, the next step is a background correction, which is empirically based on the O3 slant
column (for the baseline fitting window) and across-track position and accounts for possible across-track dependencies
and instrumental degradation.
The SO2 slant columns are then converted into vertical
columns by means of air mass factor calculations. The latter
is based on weighting function look-up tables with dependencies on the viewing geometry, clouds, surface pressure,
albedo and ozone and is applied to pre-defined box profiles
Atmos. Meas. Tech., 10, 119–153, 2017 <www.atmos-meas-tech.net/10/119/2017/>
N. Theys et al.: S-5P SO2 algorithm theoretical basis 143
and TM5 CTM forecast profiles. In addition, the algorithm
computes DOAS-type averaging kernels and a full error analysis of the retrieved columns.
In this paper we have also presented verification results using an independent algorithm for selected OMI scenes with
enhanced SO2 columns. Overall, the prototype algorithm
agrees well with the verification algorithm, demonstrating
its ability in retrieving accurately medium to very high SO2
columns. We have discussed the advantages and limitations
of both prototype and verification algorithms.
Based on the experience with GOME-2 and OMI, the
TROPOMI SO2 algorithm is expected to have a comparable level of accuracy. Due to its high signal-to-noise ratio,
TROPOMI will be capable of at least achieving comparable
retrieval precision as its predecessors but at a much finer spatial resolution of 7 km × 3.5 km at best. For single measurements, the user requirements for tropospheric SO2 concentrations will not be met, but improved monitoring of strong
pollution and volcanic events will be possible by spatial and
temporal averaging the increased number of observations of
TROPOMI. Nevertheless, it will require significant validation work and here we have discussed some of the inherent challenges for both volcanic and anthropogenic SO2 retrievals. Correlative measurements from ground-based, aircraft/mobile, and satellite instruments will be needed over
different regions and various emission scenarios to assess and
characterize the quality of TROPOMI SO2 retrievals.
The baseline algorithm presented here, including all its
modules (slant column retrieval, background correction, air
mass factor calculation and error analysis), has been fully
implemented in the S-5P operational processor UPAS by the
DLR team. Figure 11 illustrates the status of the implementation for one day of OMI test data, as an example for the
slant columns retrievals. A nearly perfect agreement is found
between SCD results over 4 orders of magnitude. A similar
match between prototype algorithm and operational processor is found for all other retrieval modules.
For more information on the TROPOMI SO2 L2 data files,
the reader is referred to the S-5P SO2 Product User Manual
(Pedergnana et al., 2016).
7 Data availability
The TROPOMI SO2 retrieval algorithm has been tested
on OMI L1 and L2 operational data, publicly available
from the NASA Goddard Earth Sciences (GES) Data and
Information Services Center (<http://disc.sci.gsfc.nasa.gov/>
Aura/OMI/omso2.shtml). The static auxiliary datasets used
as input of the TROPOMI SO2 retrieval algorithm are
publicly available. The links to the data sets are in the
references included in Table A2. Other underlying research data are available upon request from Nicolas Theys
(<theys@aeronomie.be>).
<www.atmos-meas-tech.net/10/119/2017/> Atmos. Meas. Tech., 10, 119–153, 2017
144 N. Theys et al.: S-5P SO2 algorithm theoretical basis
Appendix A: Feasibility, information on data product
and ancillary data
High-level data product description
In addition to the main product results, such as SO2 slant
column, vertical column and air mass factor, the level 2 data
files will contain several additional parameters and diagnostic information. Table A1 gives a minimum set of data fields
that will be present in the level 2 data. A one-orbit SO2 column level 2 file will be about 640 MB. More details about
the operational level 2 product based on the NetCDF data
format and the CF metadata convention are provided in the
SO2 Product User Model (Pedergnana et al., 2016).
It should be noted that the averaging kernels are given only
for the a priori profiles from the TM5 CTM (to save space).
The averaging kernels for the box profiles can be estimated
by scaling the provided averaging kernel (corresponding to
TM5 profiles): AKbox(p) = AK(p). Following the AK formulation of Eskes and Boersma (2004), the scaling factor is
given simply by AMF ratios: AMFTM5 / AMFbox.
Auxiliary information
The algorithm relies on several external data sets. These can
be either static or dynamic. An overview is given in Tables A2 and A3.
Atmos. Meas. Tech., 10, 119–153, 2017 <www.atmos-meas-tech.net/10/119/2017/>
N. Theys et al.: S-5P SO2 algorithm theoretical basis 145
Table A1. List of output fields in the TROPOMI SO2 products. nAlong × nAcross corresponds to the number of pixels in an orbit along
track and across track, respectively; n.u.: no unit.
Name/data Symbol Unit Description Data type Number of entries per
observation
Date n.u. Date and time of the measurement YYMMDDHHMMSS.MS
characters nAlong
Latitudes lat degree Latitudes of the four pixel corners + center float 5 × nAlong × nAcross
Longitudes long degree Longitudes of the four pixel corners + center
float 5 × nAlong × nAcross
SZA θ0 degree Solar zenith angle float nAlong × nAcross
VZA θ degree Viewing zenith angle float nAlong × nAcross
RAA ϕ degree Relative azimuth angle float nAlong × nAcross
SCD Ns mol m−2 SO2 slant column density float nAlong × nAcross
SCDcorr Nc
s mol m−2 SO2 slant column density background corrected
float nAlong × nAcross
VCD Nv mol m−2 SO2 vertical column density
(4 values)
float 4 × nAlong × nAcross
Wdow flag Wflag n.u. Flag for the fitting window used (1, 2, 3) integer nAlong × nAcross
AMF M n.u. Air mass factor (4 values) float 4 × nAlong × nAcross
Cloud-free AMF Mclear n.u. Cloud-free air mass factor (4 values) float 4 × nAlong × nAcross
Cloudy AMF Mcloud n.u. Fully cloudy air mass factor (4 values) float 4 × nAlong × nAcross
CF fc n.u. Cloud fraction float nAlong × nAcross
CRF 8 n.u. Cloud radiance fraction float nAlong × nAcross
CP pcloud Pa Cloud top pressure float nAlong × nAcross
CH zcloud m Cloud top height float nAlong × nAcross
CA Acloud n.u. Cloud top albedo float nAlong × nAcross
Albedo As n.u. Surface albedo float nAlong × nAcross
Aerosol index AAI n.u. Absorbing aerosol index float nAlong × nAcross
Chi-squared chi2 n.u. Chi-squared of the fit float nAlong × nAcross
VCD error σ Nv mol m−2 Total error on the vertical column (individual measurement)
float 4 × nAlong × nAcross
SCD random error σ Ns_rand mol m−2 Random error on the slant column float nAlong × nAcross
SCD systematic
error
σ Ns_syst mol m−2 Systematic error on the slant column float nAlong × nAcross
AMF random error σMrand n.u. Random error on the air mass factor (4 values)
float 4 × nAlong × nAcross
AMF systematic
error
σMsyst n.u. Systematic error on the air mass factor (4
values)
float 4 × nAlong × nAcross
Averaging kernel AK n.u. Total column averaging kernel (for a priori
profile from CTM)
float 34 × nAlong × nAcross
Averaging kernel
scalings for box
profiles
scaling box n.u. Factors to apply to the averaging kernel
function to obtain the corresponding averaging kernels for the three box profiles
float 3 × nAlong × nAcross
SO2 profile na n.u. A priori profile from CTM (volume mixing
ratio)
float 34 × nAlong × nAcross
Surface altitude zs m Digital elevation map float nAlong × nAcross
Surface pressure ps Pa Effective surface pressure of the satellite
pixel
float nAlong × nAcross
TM5 level coefficient a
Ai Pa TM5 pressure level coefficients that effectively define the mid-layer levels (from
ECMWF)
float 24
TM5 level coefficient b
Ai n.u. float 24
<www.atmos-meas-tech.net/10/119/2017/> Atmos. Meas. Tech., 10, 119–153, 2017
146 N. Theys et al.: S-5P SO2 algorithm theoretical basis
Table A2. Static auxiliary data for the S-5P SO2 algorithm.
Name/data Symbol Unit Source Pre-process Comments
needs
Absorption cross sections
SO2 σSO2
cm2 molec−1 Bogumil et al. (2003),
203, 223, 243, 293 K
Hermans et al. (2009),
all temperatures
Convolution at the
instrumental spectral resolution using the provided
slit function
Ozone σo3218 σo3243 cm2 molec−1 Brion et al. (1998);
218 and 243 K
BrO σBrO cm2 molec−1 Fleischmann et
al. (2004), 223 K
NO2 σNO2
cm2 molec−1 Vandaele et al. (1998),
220 K
–
O4 (O2-O2) σO4
cm5 molec−2 Greenblatt et
al. (1990)
High-resolution
reference solar
spectrum
Es W m−2 nm−1 Chance and Kurucz
(2010)
– –
Ring effect σringev1σringev2 cm2 molec−1 Two Ring cross sections generated internally
A high-resolution
reference solar
spectrum and
the instrument
slit function are
needed to generate
the data set
Calculated in an
ozone containing
atmosphere for low
and high SZA, using LIDORT_RRS
(Spurr et al.,

2008) and a standard atmosphere
(CAMELOT European Pollution
atmospheric
profile)
Nonlinear O3
absorption
effect
σo3l σo3sq nm cm2 molec−1
cm4 molec−2
Two pseudo-cross
sections generated
internally
The O3 cross
section at 218 K is
needed
Calculated from
the Taylor
expansion of the
wavelength and
the O3 optical
depth (Puk¯ıte et al.,
2)

Instrument slit
function
SF n.u. Slit function by
wavelength/detector
– Values between
300 and 400 nm
Surface albedo As n.u. OMI-based monthly
minimum LER (update of Kleipool et al.,
2008)
–
Digital elevation
map
zs
m
GMTED2010
(Danielson et al.,
2011)
Average over the
ground pixel area.
Atmos. Meas. Tech., 10, 119–153, 2017 <www.atmos-meas-tech.net/10/119/2017/>
N. Theys et al.: S-5P SO2 algorithm theoretical basis 147
Table A2. Continued.
Name/data Symbol Unit Source Pre-process Comments
needs
SO2 profile na n.u. One-kilometer-thick box profiles,
with three different peak altitudes,
representing different altitude
regimes:
boundary layer: from the surface altitude to 1 km above it;
free troposphere: centered around
7 km altitude;
lower stratosphere: centered around
15 km altitude
Daily SO2 profiles forecast from
TM5
– TM5 profiles from the
last available day if the
TM5 profiles of the current day are not available
Look-up table
of pressureresolved AMFs
m n.u. Calculated internally with the LIDORTv3.3 RTM (Spurr, 2008)
– For the different fitting
windows (312–326,
325–335, 360–390 nm),
the assumed vertical column is 5, 100, 500 DU,
respectively
Temperature
correction
parameters
α K
−1 Bogumil et al. (2003) – –
<www.atmos-meas-tech.net/10/119/2017/> Atmos. Meas. Tech., 10, 119–153, 2017
148 N. Theys et al.: S-5P SO2 algorithm theoretical basis
Table A3. Dynamic auxiliary data for the S-5P SO2 algorithm.
Name/data Symbol Unit Source Pre-process Backup if not
needs available
S-5P level 1B I mol s−1 m−2 nm−1
sr−1 S-5P L1b product – No retrieval
Earth radiance
S-5P level 1B E0 mol s−1 m−2 nm−1 S-5P L1b product Wavelength recalibrated Use previous
sun irradiance using a high-resolution measurement
reference solar spectrum
S-5P cloud fc n.u. –
fraction S-5P operational cloud product
S-5P cloud top pcloud Pa based on a Lambertian cloud No retrieval
pressure model (Loyola et al., 2016)
S-5P cloud top Acloud n.u. UPAS processor
albedo
SO2 profile na n.u. Daily forecast from TM5 – Use TM5 CTM
CTM run at KNMI. profile from last
available day
Temperature profile T K Daily forecast from TM5 – Use TM5 CTM
profile CTM run at KNMI profile from last
available day
S-5P absorbing AAI n.u. S-5P operational AAI product – Missing
aerosol index (Zweers, 2016) information flag
Used for flagging
KNMI processor
Snow/ice flag n.u. Near-real-time global Ice – Use snow/
and Snow Extent (NISE) ice climatology
data from NASA
Atmos. Meas. Tech., 10, 119–153, 2017 <www.atmos-meas-tech.net/10/119/2017/>
N. Theys et al.: S-5P SO2 algorithm theoretical basis 149
Table A4. Acronyms and abbreviations.
AAI Absorbing aerosol index
AK Averaging kernel
AMF Air mass factor
AOD Aerosol optical depth
AR Alternative retrieval
BrO Bromine monoxide
CAL Cloud as layer
CAMELOT Composition of the Atmospheric Mission concEpts and SentineL Observation Techniques
CAPACITY Composition of the Atmosphere: Progress to Applications in the user CommunITY
CCD Charge-coupled device
CRB Clouds as Reflecting Boundaries
CTM Chemical transport model
DOAS Differential optical absorption spectroscopy
DU Dobson unit (1 DU = 2.6867 × 1016 molecules cm−2
)
ECMWF European Centre for Medium-Range Weather Forecast
ESA European Space Agency
FT Free troposphere
FWHM Full width at half maximum
GMES Global Monitoring for Environment and Security
GOME-2 Global Ozone Monitoring Experiment–2
HCHO Formaldehyde
IPA Independent pixel approximation
IR Infrared
L2WG Level-2 Working Group
LER Lambertian equivalent reflector
LIDORT LInearized Discrete Ordinate Radiative Transfer
LOS Line-of-sight angle
LS Lower stratosphere
LUT Look-up table
MAX-DOAS Multi-axis DOAS
MR Medium retrieval
NO2 Nitrogen dioxide
NOVAC Network for Observation of Volcanic and Atmospheric Change
NRT Near-real time
OCRA Optical Cloud Recognition Algorithm
O3 Ozone
OMI Ozone Monitoring Instrument
OMPS Ozone Mapping Profiler Suite
PA Prototype algorithm
(P)BL Planetary boundary layer
PCA Principal component analysis
ROCINN Retrieval Of Cloud Information using Neural Networks
RRS Rotational Raman scattering
RTM Radiative transfer model
RAA Relative azimuth angle
S-5P Sentinel-5 Precursor
SCIAMACHY SCanning Imaging Absorption spectroMeter for Atmospheric ChartograpHY
SCD Slant column density
SCDE Slant column density error
S/N Signal-to-noise ratio
SO2 Sulfur dioxide
SR Standard retrieval
SWIR Shortwave infrared
SZA Solar zenith angle
TOMS Total Ozone Mapping Spectrometer
TROPOMI Tropospheric Monitoring Instrument
UPAS Universal Processor for UV/VIS Atmospheric Spectrometers
UV Ultraviolet
VA Verification algorithm
VC(D) Vertical column density
WF Weighting function
<www.atmos-meas-tech.net/10/119/2017/> Atmos. Meas. Tech., 10, 119–153, 2017
150 N. Theys et al.: S-5P SO2 algorithm theoretical basis
Acknowledgements. This work has been performed in the frame
of the TROPOMI project. We acknowledge financial support
from ESA S-5P, Belgium Prodex TRACE-S5P projects, and the
Bayerisches Staatsministerium für Wirtschaft und Medien, Energie
und Technologie (grant 07 03/893 73/ 5 /2013).
Edited by: J. Kim
Reviewed by: two anonymous referees
References
Afe, O. T., Richter, A., Sierk, B., Wittrock, F., and Burrows, J.
P.: BrO emissions from volcanoes: a survey using GOME and
SCIAMACHY measurements, Geophys. Res. Lett., 31, L24113,
doi:10.1029/ 2004GL020994, 2004.
Beirle, S., Hörmann, C., Penning de Vries, M., Dörner, S., Kern,
C., and Wagner, T.: Estimating the volcanic emission rate and
atmospheric lifetime of SO2 from space: a case study for Kilauea volcano, Hawai’i, Atmos. Chem. Phys., 14, 8309–8322,
doi:10.5194/acp-14-8309-2014, 2014.
Bobrowski, N., Kern, C., Platt, U., Hörmann, C., and Wagner, T.: Novel SO2 spectral evaluation scheme using the 360–
390 nm wavelength range, Atmos. Meas. Tech., 3, 879–891,
doi:10.5194/amt-3-879-2010, 2010.
Boersma, K. F., Eskes, H. J., and Brinksma, E. J.: Error analysis for
tropospheric NO2 retrieval from space, J. Geophys. Res., 109,
D04311, doi:10.1029/2003JD003962, 2004.
Bogumil, K., Orphal, J., Homann, T., Voigt, S., Spietz, P., Fleischmann, O., Vogel, A., Hartmann, M., Bovensmann, H., Frerick, J., and Burrows, J. P.: Measurements of molecular absorption spectra with the SCIAMACHY Pre-Flight Model: instrument characterization and reference data for atmospheric remotesensing in the 230–2380 nm region, J. Photoch. Photobio. A, 157,
167–184, 2003.
Bovensmann, H., Peuch, V.-H., van Weele, M., Erbertseder, T., and
Veihelmann, B.: Report Of The Review Of User Requirements
For Sentinels-4/-5, ESA, EOP-SM/2281/BV-bv, issue: 2.1, 2011.
Brenot, H., Theys, N., Clarisse, L., van Geffen, J., van Gent, J.,
Van Roozendael, M., van der A, R., Hurtmans, D., Coheur, P.-F.,
Clerbaux, C., Valks, P., Hedelt, P., Prata, F., Rasson, O., Sievers,
K., and Zehner, C.: Support to Aviation Control Service (SACS):
an online service for near-real-time satellite monitoring of volcanic plumes, Nat. Hazards Earth Syst. Sci., 14, 1099–1123,
doi:10.5194/nhess-14-1099-2014, 2014.
Brion, J., Daumont, D., and Malicet, J.: New measurements of the
absolute absorption cross-sections of ozone at 294 and 223 K in
the 310–350 nm spectral range, J. Phys., 45, L57–L60, 1984.
Brion, J., Chakir, A., Charbonnier, J., Daumont, D., Parisse, C.,
and Malicet, J.: Absorption spectra measurements for the ozone
molecule in the 350–830 nm region, J. Atmos. Chem., 30, 291–
299, doi:10.1023/A:1006036924364, 1998.
Carn, S. A. and Lopez, T. M.: Opportunistic validation of sulfur dioxide in the Sarychev Peak volcanic eruption cloud, Atmos. Meas. Tech., 4, 1705–1712, doi:10.5194/amt-4-1705-2011,
2011.
Carn, S. A., Clarisse, L., and Prata, A. J.: Multi-decadal satellite
measurements of global volcanic degassing, J. Volcanol. Geoth.
Res., 311, 99–134, doi:10.1016/j.jvolgeores.2016.01.002, 2016.
Chance, K. and Spurr, R. J.: Ring effect studies: Rayleigh scattering
including molecular parameters for rotational Raman scattering,
and the Fraunhofer spectrum, Appl. Opt., 36, 5224–5230, 1997.
Chance, K. and Kurucz, R. L.: An improved high-resolution solar
reference spectrum for earth’s atmosphere measurements in the
ultraviolet, visible, and near infrared, J. Quant. Spectrosc. Ra.,
111, 1289–1295, 2010.
Clarisse, L., Fromm, M., Ngadi, Y., Emmons, L., Clerbaux, C.,
Hurtmans, D., and Coheur, P.-F.: Intercontinental transport of
anthropogenic sulfur dioxide and other pollutants; an infrared
remote sensing case study, Geophys. Res. Lett., 38, L19806,
doi:10.1029/2011GL048976, 2011.
Danielson, J. J. and Gesch, D. B.: Global multi-resolution terrain elevation data 2010 (GMTED2010): US Geological Survey OpenFile Report 2011–1073, 26 pp., 2011.
De Smedt, I., Müller, J.-F., Stavrakou, T., van der A, R., Eskes,
H., and Van Roozendael, M.: Twelve years of global observations of formaldehyde in the troposphere using GOME and
SCIAMACHY sensors, Atmos. Chem. Phys., 8, 4947–4963,
doi:10.5194/acp-8-4947-2008, 2008.
De Smedt, I., Yu, H., Danckaert, T., Theys, N., van Gent, J.,
Van Roozendael, M., Richter, A., Hilboll, A., Loyola, D.,
and Veefkind, P.: Formaldehyde retrievals from TROPOMI onboard Sentinel-5 Precursor: Algorithm Theoretical Basis, Atmos.
Meas. Tech., in preparation, 2016.
Eisinger, M. and Burrows, J. P.: Tropospheric sulfur dioxide observed by the ERS-2 GOME instrument, Geophys. Res. Lett.,
25, 4177–4180, 1998.
Eskes, H. J. and Boersma, K. F.: Averaging kernels for DOAS totalcolumn satellite retrievals, Atmos. Chem. Phys., 3, 1285–1291,
doi:10.5194/acp-3-1285-2003, 2003.
Fioletov, V. E., McLinden, C. A., Krotkov, N., Yang, K., Loyola,
D. G., Valks, P., Theys, N., Van Roozendael, M., Nowlan, C. R.,
Chance, K., Liu, X., Lee, C., and Martin, R. V.: Application of
OMI, SCIAMACHY, and GOME-2 satellite SO2 retrievals for
detection of large emission sources, J. Geophys. Res.-Atmos.,
118, 11399–11418, doi:10.1002/jgrd.50826, 2013.
Fioletov, V. E., McLinden, C. A., Krotkov, N., Li, C., Joiner, J.,
Theys, N., Carn, S., and Moran, M. D.: A global catalogue
of large SO2 sources and emissions derived from the Ozone
Monitoring Instrument, Atmos. Chem. Phys., 16, 11497–11519,
doi:10.5194/acp-16-11497-2016, 2016.
Galle, B., Johansson, M., Rivera, C., Zhang, Y., Kihlman, M., Kern,
C., Lehmann, T., Platt, U., Arellano, S., and Hidalgo, S.: Network
for Observation of Volcanic and Atmospheric Change (NOVAC)
– A global network for volcanic gas monitoring: Network layout and instrument description, J. Geophys. Res., 115, D05304,
doi:10.1029/2009JD011823, 2010.
Greenblatt, G. D., Orlando, J. J., Burkholder, J. B., and Ravishankara, A. R.: Absorption measurements of oxygen between 330 and 1140 nm, J. Geophys. Res., 95, 18577–18582,
doi:10.1029/JD095iD11p18577, 1990.
He, H., Vinnikov, K. Y., Li, C., Krotkov, N. A., Jongeward, A. R.,
Li, Z., Stehr, J. W., Hains, J. C. and Dickerson, R. R.: Response of
SO2 and particulate air pollution to local and regional emission
controls: A case study in Maryland, Earth’s Future, 4, 94–109,
doi:10.1002/2015EF000330, 2016.
Heue, K.-P., Brenninkmeijer, C. A. M., Wagner, T., Mies, K., Dix,
B., Frieß, U., Martinsson, B. G., Slemr, F., and van Velthoven,
Atmos. Meas. Tech., 10, 119–153, 2017 <www.atmos-meas-tech.net/10/119/2017/>
N. Theys et al.: S-5P SO2 algorithm theoretical basis 151
P. F. J.: Observations of the 2008 Kasatochi volcanic SO2 plume
by CARIBIC aircraft DOAS and the GOME-2 satellite, Atmos.
Chem. Phys., 10, 4699–4713, doi:10.5194/acp-10-4699-2010,
2010.
Heue, K.-P., Brenninkmeijer, C. A. M., Baker, A. K., RautheSchöch, A., Walter, D., Wagner, T., Hörmann, C., Sihler, H.,
Dix, B., Frieß, U., Platt, U., Martinsson, B. G., van Velthoven,
P. F. J., Zahn, A., and Ebinghaus, R.: SO2 and BrO observation in the plume of the Eyjafjallajökull volcano 2010: CARIBIC
and GOME-2 retrievals, Atmos. Chem. Phys., 11, 2973–2989,
doi:10.5194/acp-11-2973-2011, 2011.
Hendrick, F., Van Roozendael, M., Kylling, A., Petritoli, A.,
Rozanov, A., Sanghavi, S., Schofield, R., von Friedeburg, C.,
Wagner, T., Wittrock, F., Fonteyn, D., and De Mazière, M.: Intercomparison exercise between different radiative transfer models used for the interpretation of ground-based zenith-sky and
multi-axis DOAS observations, Atmos. Chem. Phys., 6, 93–108,
doi:10.5194/acp-6-93-2006, 2006.
Hermans, C., Vandaele, A. C., and Fally, S.: Fourier transform measurements of SO2 absorption cross sections: I.
Temperature dependence in the 24 000–29 000 cm−1
(345–
420 nm) region, J. Quant. Spectrosc. Ra., 110, 756–765,
doi:10.1016/j.jqsrt.2009.01.031, 2009.
Hörmann, C., Sihler, H., Bobrowski, N., Beirle, S., Penning de
Vries, M., Platt, U., and Wagner, T.: S ystematic investigation
of bromine monoxide in volcanic plumes from space by using
the GOME-2 instrument, Atmos. Chem. Phys., 13, 4749–4781,
doi:10.5194/acp-13-4749-2013, 2013.
Huijnen, V., Williams, J., van Weele, M., van Noije, T., Krol, M.,
Dentener, F., Segers, A., Houweling, S., Peters, W., de Laat, J.,
Boersma, F., Bergamaschi, P., van Velthoven, P., Le Sager, P., Eskes, H., Alkemade, F., Scheele, R., Nédélec, P., and Pätz, H.-W.:
The global chemistry transport model TM5: description and evaluation of the tropospheric chemistry version 3.0, Geosci. Model
Dev., 3, 445–473, doi:10.5194/gmd-3-445-2010, 2010.
Jin, J., Ma, J., Lin, W., Zhao, H., Shaiganfar, R., Beirle, S., and
Wagner, T.: MAX-DOAS measurements and satellite validation
of tropospheric NO2 and SO2 vertical column densities at a rural
site of North China, Atmos. Environ., 133, 12–25, 2016.
Kelder, H., van Weele, M., Goede, A., Kerridge, B., Reburn, J.,
Bovensmann, H., Monks, P., Remedios, J., Mager, R., Sassier,
H., and Baillon, Y.: Operational Atmospheric Chemistry Monitoring Missions – CAPACITY: Composition of the Atmosphere:
Progress to Applications in the user CommunITY, Final Report
of ESA contract no. 17237/03/NL/GS, 2005.
Kern, C., Deutschmann, T., Vogel, A., Wöhrbach, M., Wagner, T.,
and Platt, U.: Radiative transfer corrections for accurate spectroscopic measurements of volcanic gas emissions, B. Volcanol.,
72, 233–247, 2009.
Khokhar, M. F., Frankenberg, C., Van Roozendael, M., Beirle, S.,
Kühl, S., Richter, A., Platt, U., and Wagner, T.: Satellite Observations of Atmospheric SO2 from Volcanic Eruptions during the
Time Period of 1996 to 2002, J. Adv. Space Res., 36, 879–887,
doi:10.1016/j.asr.2005.04.114, 2005.
Kleipool, Q. L., Dobber, M. R., de Haan, J. F., and Levelt, P. F.:
Earth surface reflectance climatology from 3 years of OMI data,
J. Geophys. Res., 113, D18308, doi:10.1029/2008JD010290,
2008.
Krotkov, N. A., Carn, S. A., Krueger, A. J., Bhartia, P. K., and
Yang, K.: Band residual difference algorithm for retrieval of SO2
from the Aura Ozone Monitoring Instrument (OMI), IEEE Trans.
Geosci. Remote Sensing, AURA Special Issue, 44, 1259–1266,
doi:10.1109/TGRS.2005.861932, 2006.
Krotkov, N., McClure, B., Dickerson, R., Carn, S., Li, C., Bhartia, P.
K., Yang, K., Krueger, A., Li, Z., Levelt, P., Chen, H., Wang, P.,
and Lu, D.: Validation of SO2 retrievals from the Ozone Monitoring Instrument over NE China, J. Geophys. Res., 113, D16S40,
doi:10.1029/2007JD008818, 2008.
Krotkov, N. A., McLinden, C. A., Li, C., Lamsal, L. N., Celarier,
E. A., Marchenko, S. V., Swartz, W. H., Bucsela, E. J., Joiner,
J., Duncan, B. N., Boersma, K. F., Veefkind, J. P., Levelt, P. F.,
Fioletov, V. E., Dickerson, R. R., He, H., Lu, Z., and Streets,
D. G.: Aura OMI observations of regional SO2 and NO2 pollution changes from 2005 to 2015, Atmos. Chem. Phys., 16, 4605–
4629, doi:10.5194/acp-16-4605-2016, 2016.
Krueger, A. J.: Sighting of El Chichon sulfur dioxide clouds with
the Nimbus 7 total ozone mapping spectrometer, Science, 220,
1377–1379, 1983.
Langen, J., Meijer, Y., Brinksma, E., Veihelmann, B., and Ingmann,
P.: GMES Sentinels 4 and 5 Mission Requirements Document
(MRD), ESA, EO-SMA-/1507/JL, issue: 3, 2011.
Lee, C., Martin, R. V., van Donkelaar, A., O’Byrne, G., Krotkov, N.,
Richter, A., Huey, L. G., and Holloway, J. S.: Retrieval of vertical columns of sulfur dioxide from SCIAMACHY and OMI: Air
mass factor algorithm development, validation, and error analysis, J. Geophys. Res., 114, D22303, doi:10.1029/2009JD012123,
2009.
Levelt, P., Veefkind, J., Kerridge, B., Siddans, R., de Leeuw, G.,
Remedios, J., and Coheur, P.: Observation Techniques and Mission Concepts for Atmospheric Chemistry (CAMELOT), Report,
European Space Agency, Noordwijk, the Netherlands, 2009.
Li, C., Joiner, J., Krotkov, N. A., and Bhartia, P. K.: A fast
and sensitive new satellite SO2 retrieval algorithm based
on principal component analysis: Application to the ozone
monitoring instrument, Geophys. Res. Lett., 40, 6314–6318,
doi:10.1002/2013GL058134, 2013.
Loyola, D., Garcia, S.G., Lutz, R., and Spurr, R.: S5P Cloud Products ATBD, available at: <https://sentinel.esa.int/web/sentinel/>
technical-guides/sentinel-5p/appendices/referencesandhttp:
//www.tropomi.eu/documents/level-2-products (last access: 6
January 2017), 2016.
Martin, R. V., Chance, K., Jacob, D. J., Kurosu, T. P., Spurr, R.
J. D., Bucsela, E., Gleason, J .F., Palmer, P. I., Bey, I., Fiore,
A.M., Li, Q., Yantosca, R. M., and Koelemeijer, R. B. A.: An
improved retrieval of tropospheric nitrogen dioxide from GOME,
J. Geophys. Res., 107, 4437, doi:10.1029/2001JD001027, 2002.
McLinden, C. A., Fioletov, V., Shephard, M. W., Krotkov, N., Li,
C., Martin, R. V., Moran, M. D., and Joiner, J.: Space-based detection of missing sulfur dioxide sources of global air pollution,
Nat. Geosci., 9, 496–500, doi:10.1038/ngeo2724, 2016.
Nowlan, C. R., Liu, X., Chance, K., Cai, Z., Kurosu, T. P., Lee, C.,
and Martin, R. V.: Retrievals of sulfur dioxide from the Global
Ozone Monitoring Experiment 2 (GOME-2) using an optimal estimation approach: Algorithm and initial validation, J. Geophys.
Res., 116, D18301, doi:10.1029/2011JD015808, 2011.
Palmer, P. I., Jacob, D. J., Chance, K. V., Martin, R. V., Spurr, R.
J. D., Kurosu, T. P., Bey, I., Yantosca, R., and Fiore, A.: Air
<www.atmos-meas-tech.net/10/119/2017/> Atmos. Meas. Tech., 10, 119–153, 2017
152 N. Theys et al.: S-5P SO2 algorithm theoretical basis
mass factor formulation for spectroscopic measurements from
satellites: Application to formaldehyde retrievals from the Global
Ozone Monitoring Experiment, J. Geophys. Res., 106, 14539–
14550, doi:10.1029/2000JD900772, 2001.
Pedergnana, M., Loyola, D., Apituley, A., Sneep, M., and
Veefkind, P.: S5P Level 2 Product User Manual Sulfur Dioxide SO2, available at: <https://sentinel.esa.int/web/sentinel/>
technical-guides/sentinel-5p/appendices/referencesandhttp:
//www.tropomi.eu/documents/level-2-products (last access: 6
January 2017), 2016.
Platt, U. and Stutz, J.: Differential Optical Absorption Spectroscopy (DOAS), Principle and Applications, ISBN 3-340-
21193-4, Springer Verlag, Heidelberg, 2008.
Puk¯ıte, J., Kühl, S., Deutschmann, T., Platt, U., and Wagner, T.:
Extending differential optical absorption spectroscopy for limb
measurements in the UV, Atmos. Meas. Tech., 3, 631–653,
doi:10.5194/amt-3-631-2010, 2010.
Richter, A., Wittrock, F., Schönhardt, A., and Burrows, J. P.: Quantifying volcanic SO2 emissions using GOME2 measurements,
Geophys. Res. Abstr., EGU2009-7679, EGU General Assembly
2009, Vienna, Austria, 2009.
Richter, A., Begoin, M., Hilboll, A., and Burrows, J. P.: An improved NO2 retrieval for the GOME-2 satellite instrument, Atmos. Meas. Tech., 4, 1147–1159, doi:10.5194/amt-4-1147-2011,
2011.
Rix, M., Valks, P., Hao, N., Loyola, D. G., Schlager, H., Huntrieser,
H. H., Flemming, J., Koehler, U., Schumann, U., and Inness,
A.: Volcanic SO2, BrO and plume height estimations using
GOME-2 satellite measurements during the eruption of Eyjafjallajökull in May 2010, J. Geophys. Res., 117, D00U19,
doi:10.1029/2011JD016718, 2012.
Sanders, A. and de Haan, J.: S5P ATBD of the Aerosol Layer
Height product, available at: <https://sentinel.esa.int/web/sentinel/>
technical-guides/sentinel-5p/appendices/referencesandhttp:
//www.tropomi.eu/documents/level-2-products (last access: 6
January 2017), 2016.
Schumann, U., Weinzierl, B., Reitebuch, O., Schlager, H., Minikin,
A., Forster, C., Baumann, R., Sailer, T., Graf, K., Mannstein, H.,
Voigt, C., Rahm, S., Simmet, R., Scheibe, M., Lichtenstern, M.,
Stock, P., Rüba, H., Schäuble, D., Tafferner, A., Rautenhaus, M.,
Gerz, T., Ziereis, H., Krautstrunk, M., Mallaun, C., Gayet, J.-
F., Lieke, K., Kandler, K., Ebert, M., Weinbruch, S., Stohl, A.,
Gasteiger, J., Groß, S., Freudenthaler, V., Wiegner, M., Ansmann,
A., Tesche, M., Olafsson, H., and Sturm, K.: Airborne observations of the Eyjafjalla volcano ash cloud over Europe during air
space closure in April and May 2010, Atmos. Chem. Phys., 11,
2245–2279, doi:10.5194/acp-11-2245-2011, 2011.
Spinei, E., Carn, S. A., Krotkov, N. A., Mount, G. H., Yang,
K., and Krueger, A. J.: Validation of ozone monitoring instrument SO2 measurements in the Okmok volcanic plume over
Pullman, WA in July 2008, J. Geophys. Res., 115, D00L08,
doi:10.1029/2009JD013492, 2010.
Spurr, R.: LIDORT, and VLIDORT: Linearized pseudo-spherical
scalar and vector discrete ordinate radiative transfer models for
use in remote sensing retrieval problems, Light Scattering Reviews, 3, edited by: Kokhanovsky, A., Springer, 2008.
Spurr, R., de Haan, J. F., van Oss, R., and Vasilkov, A.: Discrete Ordinate Radiative Transfer in a Stratified Medium with First Order
Rotational Raman Scattering, J. Quant. Spectros. Ra., 109, 404–
425, doi:10.1016/j.jqsrt.2007.08.011, 2008.
Theys, N., Campion, R., Clarisse, L., Brenot, H., van Gent, J., Dils,
B., Corradini, S., Merucci, L., Coheur, P.-F., Van Roozendael,
M., Hurtmans, D., Clerbaux, C., Tait, S., and Ferrucci, F.: Volcanic SO2 fluxes derived from satellite data: a survey using OMI,
GOME-2, IASI and MODIS, Atmos. Chem. Phys., 13, 5945–
5968, doi:10.5194/acp-13-5945-2013, 2013.
Theys, N., De Smedt, I., van Gent, J., Danckaert, T., Wang, T.,
Hendrick, F., Stavrakou, T., Bauduin, S., Clarisse, L., Li, C.,
Krotkov, N. A., Yu, H., and Van Roozendael, M.: Sulfur dioxide vertical column DOAS retrievals from the Ozone Monitoring Instrument: Global observations and comparison to groundbased and satellite data, J. Geophys. Res.-Atmos., 120, 2470–
2491, doi:10.1002/2014JD022657, 2015.
Thomas, W., Erbertseder, T., Ruppert, T. van Roozendael, M.,
Verdebout, J., Balis, D., Meleti, C., and Zerefos, C.: On the
retrieval of volcanic sulfur dioxide emissions from GOME
backscatter measurements, J. Atmos. Chem., 50, 295–320,
doi:10.1007/s10874-005-5544-1, 2005.
Vandaele, A. C., Hermans, C., Simon, P. C., Carleer, M., Colin,
R., Fally, S., Mérienne, M. F., Jenouvrier, A., and Coquart,
B.: Measurements of the NO2 absorption cross-section from
42 000 cm−1
to 10 000 cm−1
(238–1000 nm) at 220 K and
294 K, J. Quant. Spectrosc. Ra., 59, 171–184, 1998.
Vandaele, A. C., Hermans, C., and Fally, S.: Fourier transform measurements of SO2 absorption cross sections: II.
Temperature dependence in the 29 000–44 000 cm−1
(227–
345 nm) region, J. Quant. Spectrosc. Ra., 110, 2115–2126,
doi:10.1016/j.jqsrt.2009.05.006, 2009.
van der A, R. J., Mijling, B., Ding, J., Koukouli, M. E., Liu, F.,
Li, Q., Mao, H., and Theys, N.: Cleaning up the air: Effectiveness of air quality policy for SO2 and NOx emissions in China,
Atmos. Chem. Phys. Discuss., doi:10.5194/acp-2016-445, in review, 2016.
van Geffen, J., van Roozendaal, M., Rix, M., and Valks, P.: Initial
Validation of GOME-2 GDP 4.2 SO2 Total Columns–ORR B,
TN-IASB-GOME2-O3MSAF-SO2-01, September, 2008.
van Geffen, J. H. G. M., Boersma, K. F., Eskes, H. J.,
Maasakkers, J. D., and Veefkind, J. P. : S5P NO2 data products ATBD, available at: <https://sentinel.esa.int/web/sentinel/>
technical-guides/sentinel-5p/appendices/referencesandhttp:
//www.tropomi.eu/documents/level-2-products (last access: 6
January 2017), 2016.
van Weele, M., Levelt, P., Aben, I., Veefkind, P., Dobber, M., Eskes, H., Houweling, S., Landgraf, J., and Noordhoek, R.: Science Requirements Document for TROPOMI. Volume 1, KNMI
& SRON, RS-TROPOMI-KNMI-017, issue: 2.0, 2008.
Veefkind, J. P., Aben, I., McMullan, K., Förster, H., de Vries,
J., Otter, G., Claas, J., Eskes, H. J., de Haan, J. F., Kleipool,
Q., van Weele, M., Hasekamp, O., Hoogeven, R., Landgraf,
J., Snel, R., Tol, P., Ingmann, P., Voors, R., Kruizinga, B.,
Vink, R., Visser, H., and Levelt, P. F.: TROPOMI on the ESA
Sentinel-5 Precursor: A GMES mission for global observations
of the atmospheric composition for climate, air quality and
ozone layer applications, Remote Sens. Environ., 120, 70–83,
doi:10.1016/j.rse.2011.09.027, 2012.
Atmos. Meas. Tech., 10, 119–153, 2017 <www.atmos-meas-tech.net/10/119/2017/>
N. Theys et al.: S-5P SO2 algorithm theoretical basis 153
Vountas, M., Rozanov, V. V., and Burrows, J. P.: Ring effect: impact
of rotational Raman scattering on radiative transfer in earth’s atmosphere, J. Quant. Spectrosc. Ra., 60, 943–961, 1998.
Wagner, T., Burrows, J. P., Deutschmann, T., Dix, B., von Friedeburg, C., Frieß, U., Hendrick, F., Heue, K.-P., Irie, H., Iwabuchi,
H., Kanaya, Y., Keller, J., McLinden, C. A., Oetjen, H., Palazzi,
E., Petritoli, A., Platt, U., Postylyakov, O., Pukite, J., Richter,
A., van Roozendael, M., Rozanov, A., Rozanov, V., Sinreich,
R., Sanghavi, S., and Wittrock, F.: Comparison of box-airmass-factors and radiances for Multiple-Axis Differential Optical Absorption Spectroscopy (MAX-DOAS) geometries calculated from different UV/visible radiative transfer models, Atmos. Chem. Phys., 7, 1809–1833, doi:10.5194/acp-7-1809-2007,
2007.
Wang, Y., Beirle, S., Lampel, J., Koukouli, M., De Smedt, I., Theys,
N., Xie, P. H., Van Roozendael, M., and Wagner, T.: Validation of OMI and GOME-2A and GOME-2B tropospheric NO2,
SO2 and HCHO products using MAX-DOAS observations from
2011 to 2014 in Wuxi, China, Atmos. Chem. Phys. Discuss.,
doi:10.5194/acp-2016-735, in review, 2016.
Yang, K., Krotkov, N., Krueger, A., Carn, S., Bhartia, P. K.,
and Levelt,P.: Retrieval of Large Volcanic SO2 columns
from the Aura Ozone Monitoring Instrument (OMI): Comparisons and Limitations, J. Geophys. Res., 112, D24S43,
doi:10.1029/2007JD008825, 2007.
Yang, K., Liu, X., Bhartia, P., Krotkov, N., Carn, S., Hughes, E.,
Krueger, A., Spurr, R., and Trahan, S.: Direct retrieval of sulfur
dioxide amount and altitude from spaceborne hyperspectral UV
measurements: Theory and application, J. Geophys. Res., 115,
D00L09, doi:10.1029/2010JD013982, 2010.
Yang, K., Dickerson, R. R., Carn, S. A., Ge, C., and Wang, J.:
First observations of SO2 from the satellite Suomi NPP OMPS:
Widespread air pollution events over China, Geophys. Res. Lett.,
40, 4957–4962, doi:10.1002/grl.50952, 2013.
Zhou, Y., Brunner, D., Boersma, K. F., Dirksen, R., and Wang, P.:
An improved tropospheric NO2 retrieval for OMI observations
in the vicinity of mountainous terrain, Atmos. Meas. Tech., 2,
401–416, doi:10.5194/amt-2-401-2009, 2009.
Zweers, S.: S5P ATBD for the UV aerosol index, available
at: <https://sentinel.esa.int/web/sentinel/technical-guides/>
sentinel-5p/appendices/references and <http://www.tropomi>.
eu/documents/level-2-products (last access: 6 January 2017),
2016.
Zweers, S., Levelt, P. F., Veefkind, J. P., Eskes, H., de Leeuw, G,
Tamminen, J., Coheur, P. F., Prunet, P., and Camy-Peyret, C.:
TRAQ Performance Analysis and Requirements Consolidation
for the Candidate Earth Explorer Mission TRAQ, Final report,
KNMI, RP-ONTRAQ-KNMI-051, issue: 1.0, 2010.
<www.atmos-meas-tech.net/10/119/2017/> Atmos. Meas. Tech., 10, 119–153, 2017
