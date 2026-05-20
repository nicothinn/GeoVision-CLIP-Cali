Statistics for Spatio-Temporal Data
Introduction, Visualization, Descriptive Methods
Christopher K. Wikle
University of Missouri
Department of Statistics
May 2012
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 1 / 47
Statistics for Spatio-Temporal Data
This series of lectures is
based loosely on the 2011
John Wiley & Sons book by
Noel Cressie and Chris
Wikle:
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 2 / 47
Spatio-Temporal Processes and Data
Data from spatio-temporal processes are common in the
real-world, representing variety of interactions across
processes and scales of variability.
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 3 / 47
Spatio-Temporal Processes and Data
Spatio-temporal data are not new. Consider the digitally
restored Lienzo de Quauhquechollan from the indigenous
people of Guatemala who documented the spatio-temporal
history of the Spanish conquest from 1527 to 1530.
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 4 / 47
Spatio-Temporal Processes and Data
Although it may be informative to see snapshots of spatial
events in time (see the Missouri River scene below), to
understand the process, we must know something about
the behavior from one time-period to the next.
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 5 / 47
Goals of Spatio-Temporal Data Analysis
In statistical spatio-temporal data analysis, we seek to
characterize the process in the presence of uncertain and
(often) incomplete observations and system knowledge for
the purposes of:
Prediction in space (interpolation)
Prediction in time (forecasting)
Assimilation of observations and mechanistic models
Inference on controlling process parameters
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 6 / 47
Spatio-Temporal Statistical Modeling
From a statistician’s perspective, what makes it
“statistical”?
Uncertainty in data, model, and the associated
parameters
Estimation of parameters and prediction of processes
We also often make a distinction between “stochastic”
and “statistical”
The former concerns random structures in models
The latter concerns estimation and prediction given
data
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 7 / 47
Spatio-Temporal Statistical Modeling
Traditionally, there are two primary approaches to
spatio-temporal modeling:
Descriptive (marginal): Characterize the first and
second moment behavior of the process
I Several different processes could imply the same marginal
structure; problematic if non-Gaussian
I Most useful when process knowledge is limited
Dynamic (conditional): Current values of the process
at a location evolve from past values of the process at
various locations
I Closer to the etiology of the phenomenon under study
I Most useful if there is a priori knowledge available concerning
process behavior
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 8 / 47
Outline of this Short Course
Introduction and Exploratory/Descriptive Methods for
Spatio-Temporal Data
Essential Time Series and Spatial Statistics Concepts
Marginal Approaches for Spatio-Temporal Modeling
Hierarchical Modeling
Dynamic Spatio-Temporal Models
Examples
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 9 / 47
Outline of this talk
Notation
Exploratory and Descriptive Methods for
Spatio-Temporal Data
Motivation for Spatio-Temporal Statistical Modeling
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 10 / 47
Notation: Spatio-Temporal Processes
Let {Y (s;t) : s ∈ Ds ⊂ R
d
,t ∈ Dt ⊂ R} denote a
spatio-temporal random process, where Ds
is the spatial
domain of interest, Dt the temporal domain of interest, s
is a spatial location and t a time.
When we refer to discrete time, we will typically write
Yt(s) (i.e., a subscript t)
A purely spatial process is then: Y (s) and a time series is
either Y (t) (continuous time) or Yt (discrete time).
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 11 / 47
Notation: Distributions and Vectors/Matrices
It has become customary in hierarchical modeling to
denote “distributions” using bracket notation. E.g.,
[Z] - a continuous or discrete distribution for random
variable Z
[Z, Y ] - a joint distribution of random variable Z and
Y
[Z|Y ] - a conditional distribution of Z given Y = y
We also typically denote vectors and matrices by a bold
font: e.g., Y, β.
We use a prime notation to represent a vector or matrix
transpose: e.g., Y0
.
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 12 / 47
Exploratory Methods for Spatio-Temporal Data
Reference: Chapter 5 of Statistics for Spatio-Temporal
Data
For purposes of illustration, we consider primarily two
datasets:
Sea Surface Temperature (SST): Primarily a data set
of 2 degree by 2 degree gridded dataset of monthly
anomalies (differences from long-term averages) for
the period January 1970 - December 2003.
Eurasian Collared Dove (Streptopelia decaocto):
Yearly counts from the North American Breeding Bird
Survey from 1986 - 2003.
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 13 / 47
Exploratory Methods: Visualization
For spatio-temporal data for Ds ⊂ R
2
and Dt ⊂ R, we
would ideally be interested in examining the evolution of
the spatial data through time. An animation (or movie)
can be quite useful, especially for dynamical features in
the data (e.g., waves).
(sst movie)
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 14 / 47
Visualization: Marginal and Conditional Plots
Space (1-D)/Time Plots:
Consider the Hovm¨oller
diagram, which presents a
2-D plot, but one dimension
represents 1-D space and
the other dimension
represents time. Consider
the SST anomaly data
averaged between 1◦ S and
1
◦ N and plotted from 130E
to 80W longitude for the
years 1996 - 2003.
Longitude
← Time (Year)
140E 160E 180 160W 140W 120W 100W 80W
1997
1998
1999
2000
2001
2002
2003
−3
−2
−1
0
1
2
3
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 15 / 47
Visualization: Marginal and Conditional Plots
Time-Series Plots:
It is typically helpful
to plot time series
associated with
various spatial
locations or regions of
space. Consider the
SST anomaly
averages over regions
of the Pacific
associated with the El
Ni˜no and La Ni˜na
phenomena.
1950 1955 1960 1965 1970 1975 1980 1985 1990 1995 2000
−3
−2
−1
0
1
2
3
4
Year
Deg C
Nino 3 Index
Nino 4 Index
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 16 / 47
Visualization: Marginal and Conditional Plots
Time-Series Plots:
As another example,
consider a plot of the
invasive Eurasian
Collared Dove (ECD)
counts aggregated
across all spatial
locations and plotted
for each year from
1986 - 2003. 1986 1988 1990 1992 1994 1996 1998 2000 2002 2004
0
200
400
600
800
1000
1200
1400
Year
Eurasian Collared Dove Count
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 17 / 47
Visualization: Marginal and Conditional Plots
Spatial Maps:
Just as it is useful to look
at time series for individual
spatial locations or for
spatial regions, it is also
useful to look at spatial
maps for given times,
sequences of times, or
aggregates over time.
Consider the monthly SST
anomaly maps for February
1998 through January
1999. Each map shows
2,261 ocean pixels at
2
◦ × 2
◦
resolution.
Longitude
Latitude
Feb 98
140E 160E 180 160W 140W 120W 100W 80W
30S
20S
10S
0
10N
20N
30N
Longitude
Latitude
Mar 98
140E 160E 180 160W 140W 120W 100W 80W
30S
20S
10S
0
10N
20N
30N
Longitude
Latitude
Apr 98
140E 160E 180 160W 140W 120W 100W 80W
30S
20S
10S
0
10N
20N
30N
Longitude
Latitude
May 98
140E 160E 180 160W 140W 120W 100W 80W
30S
20S
10S
0
10N
20N
30N
Longitude
Latitude
Jun 98
140E 160E 180 160W 140W 120W 100W 80W
30S
20S
10S
0
10N
20N
30N
Longitude
Latitude
Jul 98
140E 160E 180 160W 140W 120W 100W 80W
30S
20S
10S
0
10N
20N
30N
Longitude
Latitude
Aug 98
140E 160E 180 160W 140W 120W 100W 80W
30S
20S
10S
0
10N
20N
30N
Longitude
Latitude
Sep 98
140E 160E 180 160W 140W 120W 100W 80W
30S
20S
10S
0
10N
20N
30N
Longitude
Latitude
Oct 98
140E 160E 180 160W 140W 120W 100W 80W
30S
20S
10S
0
10N
20N
30N
Longitude
Latitude
Nov 98
140E 160E 180 160W 140W 120W 100W 80W
30S
20S
10S
0
10N
20N
30N
Longitude
Latitude
Dec 98
140E 160E 180 160W 140W 120W 100W 80W
30S
20S
10S
0
10N
20N
30N
Longitude
Latitude
Jan 99
140E 160E 180 160W 140W 120W 100W 80W
30S
20S
10S
0
10N
20N
30N
−2 0 2
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 18 / 47
Visualization: Marginal and Conditional Plots
Spatial Maps:
It is also useful to look at a
sequence of maps when
the data are not on a
regular grid, such as for
the Eurasian Collared Dove
data. Consider the 3-yearly
sequence of yearly BBS
sampling-route counts
from 1988-2003. The ECD
relative abundance is
represented by both the
size and color of the
circles.
1988
1991
1994
1997
2000
2003 0
20
40
60
80
100
120
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 19 / 47
Empirical Covariance/Correlation
The previous visualization was concerned with the data
directly. Since a key component of spatio-temporal data is
the dependence between observations (in space and/or
time), it can be useful to plot summaries of this
dependence. Plots of empirical spatio-temporal covariance
(or correlation) matrices can be informative. First, we
define the empirical covariance and correlation.
Assume we have observations:
Zt = (Z(s1;t), . . . , Z(sm;t))0
,
for t = 1, . . . ,T.
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 20 / 47
Empirical Covariance/Correlation (cont.)
An m × m empirical (averaged over time) lag-τ spatial covariance
matrix is given by:
Cˆ
(τ)
Z =
1
T − τ
X
T
t=τ+1
(Zt − µˆ Z
)(Zt−τ − µˆ Z
)
0
, τ = 0, 1, . . . ,T − 1,
where the empirical spatial mean, ˆµZ
, is given by:
µˆ Z =
1
T
X
T
t=1
Zt
.
The empirical lag-τ spatial correlation matrix is given by:
Rˆ
(τ)
Z = Dˆ −1/2
Z Cˆ
(τ)
Z Dˆ −1/2
Z
,
where Dˆ
Z ≡ diag(Cˆ
(0)
Z
) is a diagonal matrix with the spatially indexed
empirical variances on the main diagonal.
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 21 / 47
Visualization: Empirical Covariance/Correlation (cont.)
Covariance Matrix
Image Plot:
Consider the empirical
lag-0 covariance matrix for
SST anomalies for
locations in a domain
along the equator in the
western Pacific Ocean as
presented as an image plot.
Longitude
Longitude
(a)
140E 160E 180 160W 140W 120W 100W 80W
140E
160E
180
160W
140W
120W
100W
80W
−0.2
0
0.2
0.4
0.6
0.8
1
1.2
1.4
1.6
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 22 / 47
Visualization: Empirical Covariance/Correlation (cont.)
Correlation Matrix
Image Plot:
Now, consider an image
plot of the empirical lag-0
correlation matrix for SST
anomalies for locations in a
domain along the equator
in the western Pacific
Ocean.
Longitude
Longitude
(b)
140E 160E 180 160W 140W 120W 100W 80W
140E
160E
180
160W
140W
120W
100W
80W
−0.4
−0.2
0
0.2
0.4
0.6
0.8
1
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 23 / 47
Empirical Cross-Covariance/Correlation Matrices
We may also be interested in the empirical cross-covariance or
cross-correlation matrices between two data sets, Zt and
Xt = (X(x1;t), . . . , X(xl
: t))0
, for t = 1, . . . ,T, where the locations
in the two data sets need not coincide (and, thus, may not be of the
same dimension). An m × l empirical lag-τ cross-covariance matrix is
given by
Cˆ
(τ)
Z,X =
1
T − τ
X
T
t=τ+1
(Zt − µˆ Z
)(Xt−τ − µˆ X
)
0
,
where ˆµX
is defined analogously as ˆµZ
. Similarly, the empirical lag-τ
cross-correlation matrix is given by
Rˆ
(τ)
Z,X = Dˆ −1/2
Z Cˆ
(τ)
Z,XDˆ −1/2
X
,
where DX = diag(Cˆ
(0)
X
).
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 24 / 47
Visualization: Empirical Cross-Correlation Matrix
Cross-Correlation Matrix Image
Plot:
Consider the lag-6 cross-correlation
for the special case of l = 1, where
the X-variable is the near-surface
zonal (i.e., east-west) wind
component at 155◦E, 5◦N and the
Z-variable is the monthly anomaly
for each of the pixels in the
tropical Pacific region 6 months
later. In this case, since X
corresponds to one location, we
can plot the cross-correlation
matrix as a spatial map.
Longitude
Latitude
140E 160E 180 160W 140W 120W 100W 80W30S
20S
10S
0
10N
20N
30N
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 25 / 47
Empirical Spatio-Temporal Covariance Matrix
As we will see later, the joint spatio-temporal covariance structure is
critical for optimal prediction. Thus, it is important to examine the
empirical covariance function at various space and time lags.
Assuming that the first moment depends on space but not on time,
and the second moment depends only on the spatial and temporal lag
differences, the estimated spatio-temporal covariance at spatial lag h
and time lag τ is:
Cˆ
Z (h; τ ) ≡
1
|Ns (h)|
1
|Nt(τ )|
X
si,sj∈Ns (h)
X
t,r∈Nt (τ)
(Z(si
;t) − µˆZ (si))(Z(sj
;r) − µˆZ (sj)),
where ˆµZ (si) ≡ (1/T)
PT
t=1 Z(si
;t), Ns (h) refers to the pairs of
spatial locations with spatial lag within some tolerance of of h, Nt(τ )
refers to the pairs of time points with time lag within some tolerance
of τ , and |N(·)| refers to the number of elements (cardinality) of the
set N(·).
From this formula, we can construct the lag-τ empirical covariance
matrices Cˆ(τ)
, τ = 0, 1, 2, . . ..
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 26 / 47
Visualization: Empirical Spatio-Temporal Covariance
Spatio-Temporal Covariance
Matrix Image Plot:
Consider the SST anomaly data set
with spatial lags (h) in degrees and
temporal lags (τ ) in months. In
this case, we show both an image
plot and a contour plot - both are
equally informative but have
individual strengths and weaknesses
with respect to visualization.
Spatial Lag (deg)
Time Lag (month)
(a)
0 20 40 60 80 100
0
5
10
15
20
0
0.05
0.1
0.15
0.2
0.25
0.3
0.35
0.4
0
0.05
0.05
0.1
0.15
0.2
0.25
0.3
Spatial Lag
Time Lag
(b)
0 20 40 60 80 100
0
5
10
15
20
0
0.05
0.1
0.15
0.2
0.25
0.3
0.35
0.4
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 27 / 47
Empirical Orthogonal Functions (EOFs)
As will be discussed later, dimension reduction is an integral part of
spatio-temporal modeling. As in classical multivariate analysis, one of
the most effective methods of dimension reduction comes from a
spectral decomposition of the empirical variance/covariance matrix
(i.e., principal components). Although there are analogous
decompositions for continuous space/time (e.g., the Karhunen-Lo´eve
decomposition), we focus on the discrete case here.
Specifically, if Zt = (Zt(s1), . . . , Zt(sm))0
for t = 1, . . . ,T, consider
the spectral decomposition of the empirical lag-0 covariance matrix:
Cˆ
(0)
Z = ΨΛΨ0
,
where Ψ is the matrix of eigenvectors and Λ is the diagonal matrix of
eigenvalues.
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 28 / 47
Empirical Orthogonal Functions (cont.)
Each column of Ψ, say ψk
, corresponds to a spatial map
ψk = (ψk (s1), . . . , ψk (sm))0
. This map, called the k-th empirical
orthogonal function (EOF), is analogous to the “loadings” in
traditional principal component analysis. That is, we can define new
variables at(k) = ψ
0
kZt
, for k = 1, . . . , m. The time series, at(k) are
then the principal component time series.
In this case, the EOF eigenvectors are orthogonal, Ψ0Ψ = I and ψ1
is
the vector that allows var(at(1)) to be maximized, ψ2
is the vector
that maximizes var(at(2)) subject to the orthogonality constraint, etc.
Thus, as with traditional principal component analysis,
var(at(k)) = λk , k = 1, . . . , m. In practice, if there is substantial
spatial dependence, most of the variability in the Zt data set can be
expressed in terms of just a few of the principal component time
series.
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 29 / 47
EOF Analysis
Consider a plot of the cumulative variance accounted for by the first
100 EOFs for the monthly Pacific SST anomaly data from January
1970 through December 2002.
0 10 20 30 40 50 60 70 80 90 100
30
40
50
60
70
80
90
100
EOF
Percent
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 30 / 47
Visualization: EOFs
First EOF and PC time series for
SST anomaly data (38.8% of
variation):
Longitude
Latitude
(a)
140E 160E 180 160W 140W 120W 100W 80W
30S
20S
10S
0
10N
20N
30N
−0.1
−0.05
0
0.05
0.1
1970 1975 1980 1985 1990 1995 2000
−20
−10
0
10
20
Year
deg C
(b)
Second EOF and PC time series for
SST anomaly data (9.3% of
variation):
Longitude
Latitude
(c)
140E 160E 180 160W 140W 120W 100W 80W
30S
20S
10S
0
10N
20N
30N
−0.2
−0.1
0
0.1
0.2
1970 1975 1980 1985 1990 1995 2000
−10
−5
0
5
10
Year
deg C
(d)
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 31 / 47
Visualization: EOFs
Third EOF and PC time series for
SST anomaly data (8.5% of
variation):
Longitude
Latitude
(a)
140E 160E 180 160W 140W 120W 100W 80W
30S
20S
10S
0
10N
20N
30N
−0.1
0
0.1
1970 1975 1980 1985 1990 1995 2000
−10
−5
0
5
10
Year
deg C
(b)
Fourth EOF and PC time series for
SST anomaly data (4.2% of
variation):
Longitude
Latitude
(c)
140E 160E 180 160W 140W 120W 100W 80W
30S
20S
10S
0
10N
20N
30N
−0.1
0
0.1
1970 1975 1980 1985 1990 1995 2000
−5
0
5
Year
deg C
(d)
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 32 / 47
EOFs: Further Discussion
There are several additional points to make concerning EOF analysis.
One can just as easily consider eigenvector/eigenvalue
decomposition of the empirical temporal covariance matrix. In
this case, the eigenvectors represent time series and the
projections of the data onto the eigenvectors correspond to
spatial random fields.
Calculation of spatial EOFs when m > T: When the number of
spatial locations exceeds the number of time replicates then the
empirical spatial covariance matrix is not positive-definite.
However, one can still obtain EOFs up to T − 1 by considering
the spectral decomposition of the temporal covariance matrix
and applying some simple transformations, or via a singular value
decomposition on the original data matrix (see Section 5.3.4 in
C&W 2011).
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 33 / 47
EOFs: Further Discussion (cont.)
EOF analysis implicitly assumes that the spatial areas of
influence are the same for each data point. If that is not the
case, one should consider the Karhunen-Lo´eve integral equation
representation of EOFs (see Section 5.3.1 in C&W 2011).
We can also consider: multivariate EOFs, extended EOFs,
complex EOFs, Hilbert EOFs, etc. (see Section 5.5 in C&W
2011).
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 34 / 47
Spatio-Temporal LISAs
Local Indicators of Spatial Association (LISAs) (Anselin, 1995)
decompose global statistics into components such that:
each component is associated with a spatial coordinate
an average of the local components yields the global component.
In a purely spatial setting, LISA applied to an empirical covariance
function can show unusual components at various locations, allowing
a visualization of spatial outliers or departures from stationarity.
Similar visualizations can be used for LISAs in the spatio-temporal
setting. Consider the following examples.
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 35 / 47
Spatio-Temporal LISAs: Example 1
Consider the temporal empirical
covariances for the monthly SST
anomaly data from January 1970
to December 2002. The figure
shows a spatial plot of these
temporal empirical autocovariances
at lag τ = 1 (month). The El Ni˜no
region is prominent.
Longitude
Latitude
140E 160E 180 160W 140W 120W 100W 80W
30S
20S
10S
0
10N
20N
30N
0
0.5
1
1.5
2
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 36 / 47
Spatio-Temporal LISAs: Example 2
Recall that the empirical (averaged over time) lag-τ spatial
covariance matrix is based on the sum of component matrices
(Zt − µˆz
)(Zt−τ − µˆz
)
0
. Here, we consider the first EOF from the
sum of these component matrices over the 12 months of each year for
the period January 1970 - December 2002, which gives 33 different
covariance matrices. The eigenvalue and associated eigenvector are
LISAs because they approximate the empirical spatial covariance
matrix from that year, and the overall empirical covariance matrix is
constructed from a linear combination of these submatrices.
We consider plots of the leading eigenvalue for each year and the
EOF maps for two example years.
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 37 / 47
Spatio-Temporal LISAs: Example 2
LISA plot showing the eigenvalue
of the leading EOF for the monthly
SST anomaly data for consecutive
12-month periods starting January
1970. For presentation, the leading
eigenvalue is normalized by the
total variance to show the percent
variance accounted for by the
leading EOF for each year.
1970 1975 1980 1985 1990 1995 2000
20
30
40
50
60
70
80
Time
Percent of Total Variance
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 38 / 47
Spatio-Temporal LISAs: Example 2
The spatial map of the leading
EOF of the monthly SST anomaly
data associated with the yearly
LISA analysis for (a) 1981 and (b)
1982. Note, 1982 was a significant
El Ni˜no year and 1981 was not.
Longitude
Latitude
(a)
140E 160E 180 160W 140W 120W 100W 80W
30S
20S
10S
0
10N
20N
30N
−1
−0.5
0
0.5
1
Longitude
Latitude
(b)
140E 160E 180 160W 140W 120W 100W 80W
30S
20S
10S
0
10N
20N
30N
−1
−0.5
0
0.5
1
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 39 / 47
Spatio-Temporal Parallel Coordinate Plots
The Parallel Coordinates plot is a way to visualize multivariate data
(e.g., Inselberg, 1985). Visually,
the vertical axes are placed in parallel according to some
predetermined order
each component of a given multivariate observation is plotted on
its respective axis
a piecewise straight line is drawn between corresponding values
on each axis
color can be a useful way to separate groups
Note, in high-dimensional spatio-temporal data, these plots can be so
“busy” that they are difficult to interpret due to the “visual clutter.”
One way to reduce this clutter is to collapse the m spatial locations
into fewer components - such as EOFs. In this case, the vertical axis
then represents a particular EOF rather than a location in physical
space. Consider an example with the SST anomaly data.
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 40 / 47
Spatio-Temporal Parallel Coordinate Plot: Example
Parallel coordinate plot for
the monthly Pacific SST
anomalies. The data were
projected onto the first six
EOFs and the associated
principal components
represent the x-axis
coordinates. Each connected
line represents the values of
these EOF variables for a
given month (from January
1970–December 2000). Lines
associated with different
decades are indicated by
different colors.
EOF 1 EOF 2 EOF 3 EOF 4 EOF 5 EOF −20
−15
−10
−5
0
5
10
15
20
25
1971−19801981−19901991−2000Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 41 / 47
Spatio-Temporal Canonical Correlation Analysis (ST-CCA)
Canonical correlation analysis (CCA) is a long-standing multivariate
statistical method that obtains linear combinations of two sets of
data such that the correlations are maximal. This can be extended to
the spatio-temporal context.
Consider two spatio-temporal datasets:
Zt = (Zt(s1), . . . , Zt(sm))0
: t − 1, . . . ,T,
Xt = (Xt(x1), . . . , Xt(xl))0
: t − 1, . . . ,T,
where the spatial domain may be different, but we assume that the
temporal domain is the same for both datasets.
We seek a linear combination of the data vectors at(k) = ξ
0
kZt and
bt(k) = ψ
0
kXt
, where ξk = (ξk (1), . . . , ξk (m))0
and
ψk = (ψk (1), . . . , ψk (l))0
are both spatial maps such that the
correlation (i.e., the k-th canonical correlation, r
2
k
) between at(k) and
bt(k) is maximal.
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 42 / 47
ST-CCA (cont.)
Specifically, we do this such that at(1) and bt(1) give the maximum
correlation, and then find the next set at(2), bt(2) such that the
canonical correlation is maximized subject to being uncorrelated with
at(1), bt(1), etc.
Define Cˆ
(0)
Z
, Cˆ
(0)
X
as the empirical lag-0 spatial covariance matrices for
Z and X, respectively, and Cˆ
(0)
Z,X
as the empirical lag-0 spatial
cross-covariance matrix between Z and X. Then, let ξ˜
k
and ψ˜
k be
the left and right singular vectors, respectively, associated with the
k-th singular vector r
2
k
from the singular value decomposition of
(Cˆ
(0)
Z
)
−1/2Cˆ
(0)
Z,X
(Cˆ
(0)
X
)
−1/2
.
Then, it can be shown that ξˆ
k = (Cˆ
(0)
Z
)
−1/2ξ˜
k
, ψˆ
k = (Cˆ
(0)
X
)
−1/2ψ˜
k
,
and at(k) = ξ
0
kZt
, bt(k) = ψ
0
kXt
.
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 43 / 47
ST-CCA: Example
To illustrate the exploratory application of ST-CCA, consider the
tropical Pacific SST anomalies averaged over January through March
for each year form 1970 through 1999.
In addition, consider a dataset from the U.S. Fish and Wildlife Service
Breeding Population Survey (BPS) for the same period. This survey
has been conducted each year (since 1955) and consists of 18-mile
linear segments (1/4 mile wide) over which an aircraft pilot and an
observer count and speciate the waterfowl population. We are
interested in Mallard duck counts. The breeding habitat is sensitive to
precipitation and there is a strong link between the tropical Pacific
SST and precipitation in North America. Thus, it is hypothesized
that there is a possibly strong relationship between the SST
anomalies and the breeding population count.
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 44 / 47
ST-CCA Example (cont.)
(a) First CCA pattern for the
SST anomalies (ξ1
). (b)
First CCA pattern for the
Mallard pair counts (ψ1
).
Longitude
Latitude
(a)
140E 160E 180 160W 140W 120W 100W 80W
30S
20S
10S
0
10N
20N
30N
−5
0
5
x 10−3120W 110W 100W
45N
50N
55N
60N
(b)
−4
−2
0
2
4
x 10−3
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 45 / 47
ST-CCA Example (cont.)
Time series of first canonical
variables for yearly SST
anomalies (at(1), blue solid
line) and for yearly counts of
breeding Mallard pairs (bt(1),
red dashed line). Note, the
correlation between these
two time series is 0.96.
1970 1975 1980 1985 1990 1995 2000
−2
−1.5
−1
−0.5
0
0.5
1
1.5
2
2.5
3
Year
SST
Indicated Mallard Pair Counts
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 46 / 47
Other Visualizations
Note, there are many other visualization and exploratory
methods for spatio-temporal data that could be
considered. For example, Cressie and Wikle (2011) discuss
some of these in Chapter 5:
Spatial and Spatio-Temporal Spectral Analysis
Spatial and Spatio-Temporal Cross-Spectral Analysis
Principal Oscillation Pattern (POP) Analysis
Spatio-Temporal Field Comparison
Christopher K. Wikle (UMC) Statistics for Spatio-Temporal Data May 2012 47 / 47
