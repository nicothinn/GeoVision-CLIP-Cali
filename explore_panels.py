import xarray as xr
import numpy as np

# Explore MODIS panel
print('=== MODIS MCD19A2 Panel ===')
modis = xr.open_zarr('dataset_sit2/MODIS_MCD_panel', consolidated=True)
print(modis)
print()
print('Dimensions:', dict(modis.dims))
print('Coords:', {k: v.values for k, v in modis.coords.items()})
print()
# Check a slice
print('First time:', str(modis.time.values[0]))
print('Last time:', str(modis.time.values[-1]))
print('Num times:', len(modis.time))
print()
# Check band info
print('Bands:', modis.band.values)
aod = modis.isel(time=0, band=0)
print('AOD shape:', aod.shape)
print('AOD range:', float(aod.min()), '-', float(aod.max()))
print('AOD has NaN:', bool(np.isnan(aod.values).any()))

print()
print('=== ERA-5 Panel ===')
era5 = xr.open_zarr('dataset_sit2/ERA-5_panel', consolidated=True)
print(era5)
print()
print('Dimensions:', dict(era5.dims))
print('Bands:', era5.band.values)
print('Num times:', len(era5.time))
print('First time:', str(era5.time.values[0]))
