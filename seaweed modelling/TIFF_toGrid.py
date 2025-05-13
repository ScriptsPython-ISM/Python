import rasterio
import numpy as np

def depth_grid():
    with rasterio.open("marseille_depth.tif") as src:
        depth_data = src.read(1)
    from rasterio.warp import reproject, Resampling
    from rasterio.transform import from_bounds
    
    target_shape = (100, 100)
    target_transform = from_bounds(*src.bounds, width=target_shape[1], height=target_shape[0])
    resampled_depth = np.empty(target_shape, dtype=np.float32)
    
    reproject(
        source=depth_data,
        destination=resampled_depth,
        src_transform=src.transform,
        src_crs=src.crs,
        dst_transform=target_transform,
        dst_crs=src.crs,
        resampling=Resampling.bilinear
        )
    depth_above_sea_level = -resampled_depth
    
    depth_above_sea_level = np.clip(depth_above_sea_level, 0, None)

    return depth_above_sea_level

def plot():
    import matplotlib.pyplot as plt
    
    plt.imshow(depth_grid(), cmap='Blues')
    plt.title("Depth Below Sea Level")
    plt.colorbar(label="Depth (m)")
    plt.show()