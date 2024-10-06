import requests
import json
import time
import rasterio
from rasterio.enums import Resampling
import numpy as np
from PIL import Image
from matplotlib import cm, colors
import matplotlib.pyplot as plt
from skimage.transform import resize
from skimage import io
from rasterio.windows import Window
import math

average_moist = []
global incrementer
incrementer = 0

try:
    with open("geodata.json", 'r') as file:
        data = json.load(file)
        exp_zoom = data[0]
        exp_center = data[1]
        exp_box = data[2]

except FileNotFoundError:
    print("file not found")

def save_mapbox_satellite_image(api_key, lat, lon, zoom, size, file_name):

    url = f"https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/{lon},{lat},{zoom}/{size}?access_token={api_key}"

    # make the request to Mapbox
    response = requests.get(url)

    # save the image if the request was successful
    if response.status_code == 200:
        with open(file_name, 'wb') as f:
            f.write(response.content)
        print(f"Satellite image saved as {file_name}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

api_key = "pk.eyJ1IjoiaGVpa29zY2htaXR6IiwiYSI6ImNtMXMxNGN0ajAxeTEya3M2ejFjajAxeTcifQ.1FJY9PDekSfQEHGk-0olgw"  # Replace with your Mapbox key
save_mapbox_satellite_image(api_key, exp_center[0], exp_center[1], exp_zoom-1, "800x800", "mapbox_satellite.jpg")

time.sleep(3)

palette = list(reversed([(0.83, 0.24, 0.30),(0.96, 0.43, 0.26),
                        (0.99, 0.68, 0.38),(0.99,0.88,0.545),
                        (0.9,0.96,0.60),(0.67,0.86,0.64),
                        (0.4,0.76,0.65),(0.2,0.56,0.74)]))




def get_moisture(filename, passedPalette, seeder):

    with rasterio.open(filename) as src:

        raster_bounds = src.bounds
        # convert to raster's row and col; CAREFUL because coordinates are flipped  
        row_min, col_min = src.index(exp_box[0][1], exp_box[1][0])
        row_max, col_max = src.index(exp_box[1][1], exp_box[0][0])

        if row_min == row_max and col_min == col_max:  # check if its the same point on geotiff
            print("Bounding box collapsed to a single point.")
            
            small = src.read(1, window=((row_min, row_min + 1), (col_min, col_min + 1)))

        else:
            small = src.read(1, window=((row_min, row_max), (col_min, col_max)))

        window = Window(col_min,row_min,(col_max-col_min),(row_max-row_min))
        transform = src.window_transform(window)
        out_meta = src.meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": 800,
            "width": 800,
            "transform": transform
        })

        # save tiff of the small section
        with rasterio.open('small.tif', 'w', **out_meta) as dst:
            dst.write(small, 1)  # Write the first band

    time.sleep(1)

    # coloring the tif and saving as png
    tiff_image = Image.open("small.tif")
    small = np.array(tiff_image)

    
    # checker if map includes water (which is -9999 value)
    min_value = np.nanmin(small)
    if min_value < -5000:
        small[small == min_value] = min_value + 9999

    min_val = 0
    max_val = np.nanmax(small)
    average_moist.append(np.median(small))
    normalized_data = (small - min_val) / (max_val - min_val) 

    # custom colormap to fit giovanni soil moisture
    cmap = colors.LinearSegmentedColormap.from_list("", passedPalette)
    colored_data = cmap(normalized_data)

    # converting to 8-bit
    colored_image = (colored_data[:, :, :3] * 255).astype(np.uint8) 
    image = Image.fromarray(colored_image)
    image.save(f'{filename}.png')


get_moisture('SM2019-10cm.tif', palette, 1)
get_moisture('SM2024-10cm.tif', palette, 1)
with open('ch10.json', 'w') as file:
    data = ((average_moist[1]-average_moist[0])*100/average_moist[0]).item()
    average_moist=[]
    json.dump(data, file)
get_moisture('SM2019-40cm.tif', palette, 1)
get_moisture('SM2024-40cm.tif', palette, 1)
with open('ch40.json', 'w') as file:
    data = ((average_moist[1]-average_moist[0])*100/average_moist[0]).item()
    average_moist=[]
    json.dump(data, file)

get_moisture('SM2019-100cm.tif', palette, 1)
get_moisture('SM2024-100cm.tif', palette, 1)
with open('ch100.json', 'w') as file:
    data = ((average_moist[1]-average_moist[0])*100/average_moist[0]).item()
    average_moist=[]
    json.dump(data, file)



from colormath.color_objects import LabColor
from colormath.color_diff import delta_e_cie2000
from skimage.segmentation import slic
from skimage.segmentation import mark_boundaries
from skimage.util import img_as_float
from skimage import io, measure, color, data, graph, segmentation, img_as_ubyte
import matplotlib.pyplot as plt
import argparse
import cv2 as cv

def _weight_mean_color(graph, src, dst, n):
    """
    graph : RAG
        The graph under consideration.
    src, dst : int
        The vertices in `graph` to be merged.
    n : int
        A neighbor of `src` or `dst` or both.
    Returns
    -------
    data : dict
        A dictionary with the `"weight"` attribute set as the absolute
        difference of the mean color between node `dst` and `n`.
    """
    diff = graph.nodes[dst]['mean color'] - graph.nodes[n]['mean color']
    diff = np.linalg.norm(diff)
    
    return {'weight': diff}

def rgb_to_hex(nlist):
    return "#{:02x}{:02x}{:02x}".format(int(nlist[0]), int(nlist[1]), int(nlist[2]))
cluster_dict = {}


def merge_mean_color(graph, src, dst):
    """
    This method computes the mean color of `dst`.
    ----------
    graph : RAG
        The graph under consideration.
    src, dst : int
        The vertices in `graph` to be merged.
    """
    graph.nodes[dst]['total color'] += graph.nodes[src]['total color']
    graph.nodes[dst]['pixel count'] += graph.nodes[src]['pixel count']
    graph.nodes[dst]['mean color'] = (
        graph.nodes[dst]['total color'] / graph.nodes[dst]['pixel count']
    )
    global incrementer
    cluster_dict[f"{rgb_to_hex(graph.nodes[dst]['mean color'])}"] = f"cluster{incrementer}"
    
    incrementer += 1


img = io.imread("mapbox_satellite.jpg")
img = cv.GaussianBlur(img, (3,3), cv.BORDER_DEFAULT)
labels = segmentation.slic(img, compactness=20, n_segments=100, start_label=1)
g = graph.rag_mean_color(img, labels)

labels2 = graph.merge_hierarchical(
    labels,
    g,
    thresh=20,
    rag_copy=False,
    in_place_merge=True,
    merge_func=merge_mean_color,
    weight_func=_weight_mean_color,
)

out = color.label2rgb(labels2, img, kind='avg', bg_label=0)
out = segmentation.mark_boundaries(out, labels2, (0, 0, 0))
fig, axes = plt.subplots(1, 2, figsize=(10, 5))
axes[0].imshow(out)
axes[1].imshow(img)
plt.show()

# SAVING THE MASK
out_uint8 = (out * 255).astype(np.uint8)
cv.imwrite("merged_superpixel.png", cv.cvtColor(out_uint8, cv.COLOR_RGB2BGR))
mask_normalized = img_as_ubyte(labels2 / labels2.max())  # Convert to 8-bit format
io.imsave('merged_superpixel_mask.png', mask_normalized)

with open("regions.txt", 'w') as file:
    file.write("{\n")  # Start the dictionary
    keys = list(cluster_dict.keys())  # Get all keys
    
    for i, key in enumerate(keys):
        # Write each key-value pair
        if i == 0:
            file.write(f'\t"{key}" : "{cluster_dict[key]}"')
        else:
            file.write(f'"{key}" : "{cluster_dict[key]}"')
        if i < len(keys) - 1:  # If it's not the last key-value pair
            file.write("\n\t,")  # Add a comma at the start of the new line
        
    file.write("\n}")  # End the dictionary
