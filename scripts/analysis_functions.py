import ee
import scripts.fire_info as fi
#TODO: gic was the original module for all things imageCollection handling.. 
#   we transitioned to using something similar that Collect Earth Online uses because its cleaner code.. 
#   we eventually would like there to be only one module related to imageCollection handling (filtering,merging,compositing)..
#   original gic is still used for imageColl compositing
import scripts.get_image_collections as gic
#   gic2 is used for imageColl filtering/merging
import scripts.get_image_collections2 as gic2

def nbr(image:ee.Image)-> ee.Image:
    return image.normalizedDifference(['NIR','SWIR2']).multiply(1000)

def dnbr(pre:ee.Image, post : ee.Image)-> ee.Image:
    return pre.subtract(post)

def rdnbr(pre:ee.Image, nrt : ee.Image)-> ee.Image:
    pre_nbr = nbr(pre)
    ntr_nbr = nbr(nrt)
    denominator = pre_nbr.divide(1000).abs().sqrt()
    numerator = dnbr(pre_nbr,ntr_nbr)
    out = numerator.divide(denominator)

    return out.rename('RdNBR')

def miller_thresholds(rdnbr :ee.Image)-> ee.Image:
    '''generates miller thresholds from 0-3
    0 : #very low or unburned
    1 : low
    2 : moderate
    3 : high

    Args:
        rdnbr (ee.Image): Relative NBR img

    Returns:
        ee.Image: [description]
    '''

#Miller, J. D., & Thode, A. E. (2007). Quantifying burn severity in a heterogeneous landscape 
# with a relative version of the delta Normalized Burn Ratio (dNBR). 
# Remote sensing of Environment, 109(1), 66-80.
    serv = rdnbr.where(rdnbr.lte(69),0) \
            .where(rdnbr.gte(69).And(rdnbr.lte(315)),1) \
            .where(rdnbr.gt(315).And(rdnbr.lte(640)),2) \
            .where(rdnbr.gt(640),3).rename('MillersThresholds')
    
    return serv

def miller_thresholds4(rdnbr :ee.Image)-> ee.Image:
    '''generates miller thresholds from 1-4
    1 : #very low or unburned
    2 : low
    3 : moderate
    4 : high

    Args:
        rdnbr (ee.Image): Relative NBR img

    Returns:
        ee.Image: [description]
    '''

#Miller, J. D., & Thode, A. E. (2007). Quantifying burn severity in a heterogeneous landscape 
# with a relative version of the delta Normalized Burn Ratio (dNBR). 
# Remote sensing of Environment, 109(1), 66-80.
    serv = rdnbr.where(rdnbr.lte(69),1) \
            .where(rdnbr.gte(69).And(rdnbr.lte(315)),2) \
            .where(rdnbr.gt(315).And(rdnbr.lte(640)),3) \
            .where(rdnbr.gt(640),4) \
            .rename('MillersThresholds')
    
    return serv

def bs_calc_new(feat: ee.Feature):
    fire = ee.Feature(feat)
    # fire_geom = fire.geometry()
    
    fire = ee.Feature(fi.set_windows(fire))
    region = fire.geometry()
    # mode = fire.get('mode')
    pre_start = fire.get('pre_start')
    pre_end = fire.get('pre_end')
    post_start = fire.get('post_start')
    post_end = fire.get('post_end')
    
    sensor = "landsat"
    pre_collection = gic2.getLandsatToa(pre_start,pre_end,region)
    pre_img = gic.get_composite(pre_collection,gic.make_pre_composite,pre_start,pre_end)

    post_collection = gic2.getLandsatToa(post_start,post_end,region)
    post_img = gic.get_composite(post_collection,gic.make_nrt_composite, sensor) 
    
    rdnbr_calc = rdnbr(pre_img,post_img)
    miller = miller_thresholds(rdnbr_calc)
    
    return ee.Image(miller).clip(region).select('MillersThresholds').toByte()

# def rdnbr_only_calc(feat: ee.Feature):
#     fire = ee.Feature(fi.set_windows(feat))

#     pre_start = fire.get('pre_start')
#     pre_end = fire.get('pre_end')
#     post_start = fire.get('post_start')
#     post_end = fire.get('post_end')
    
#     ##region = fire.geometry() #multiple # to prevent unneeded pylance problem
#     sensor = "landsat"
#     pre_collection = gic2.getLandsatToa(pre_start,pre_end,region)
#     pre_img = gic.get_composite(pre_collection,gic.make_pre_composite,pre_start,pre_end)

#     post_collection = gic2.getLandsatToa(post_start,post_end,region)
#     post_img = gic.get_composite(post_collection,gic.make_nrt_composite, sensor) 
    
#     rdnbr_calc = rdnbr(pre_img,post_img)
    
#     return ee.Image(rdnbr_calc).clip(region)

def bs_calc_v2309(feat: ee.Feature):

    #set the pre and post fire windows, using the simulation version of the function
    fire = ee.Feature(fi.set_windows_sim(feat))

    pre_start = fire.get('pre_start')
    pre_end = fire.get('pre_end')
    post_start = fire.get('post_start')
    post_end = fire.get('post_end')
    
    region = fire.geometry()
    #sensor = "landsat"

    pre_collection = gic2.getLandsatToaRobust(pre_start,pre_end,region)
    pre_img = gic.get_composite(pre_collection,gic.make_mean_composite,pre_start,pre_end)

    post_collection = gic2.getLandsatToaRobust(post_start,post_end,region)
    post_img = gic.get_composite(post_collection,gic.make_mean_composite,post_start,post_end) 
    
    #  dev note: composite returns an image with no bands when no data, so need to handle 
    #            otherwise rdnbr() will error on no 'NIR' band available
    #  plan: create a nodata image as a placeholder
    #        rdnbr_calc only use bands 'NIR','SWIR2', so only those made
    #   logic test: base on the size of the bandname list, as there will be an image returned from get composite
    post_img_band_size = post_img.bandNames().size()
    post_img = post_img.set('pci_size', post_img_band_size)
    pci_nodata = ee.Image.constant(0).selfMask() \
        .addBands(ee.Image.constant(0).selfMask()) \
        .rename(['NIR','SWIR2']) \
        .set('pci_size', post_img_band_size) 
    #filter to only use when no bands in composite
    pci_nodata_filt = ee.ImageCollection(pci_nodata).filter(ee.Filter.eq('pci_size', 0))
    post_data_filt = ee.ImageCollection(post_img).filter(ee.Filter.neq('pci_size', 0))
    #merge two together (one or the other will be empty)
    pc_img_merge = ee.ImageCollection(post_data_filt).merge(pci_nodata_filt)
    #take first (will only ever be 1 image)
    post_img_robust = ee.Image(pc_img_merge.first())

    #Calculate RdNBR and Severity classes
    rdnbr_calc = rdnbr(pre_img,post_img_robust) #band name 'RdNBR' 
    miller = miller_thresholds4(rdnbr_calc) #band name 'MillersThresholds'

    #create image with both bands ('RdNBR' and 'MillersThresholds')
    # copies some properties over, includes a flag if there was enough data for a post fire window composite 
    combined = rdnbr_calc \
        .addBands(miller.toByte()) \
        .clip(region) \
        .set('fire_id', fire.get('fire_id'), 'post_fire_calc', post_img_band_size.neq(0))  
    return ee.Image(combined)
    
# def bs_calc_v2309_db(feat: ee.Feature):
#     # DEBUGGING FUNCTION. NOT MAPPED. SINGLE FIRE.

#     #set the pre and post fire windows, using the simulation version of the function
#     fire = ee.Feature(fi.set_windows_sim(feat))

#     pre_start = fire.get('pre_start')
#     pre_end = fire.get('pre_end')
#     post_start = fire.get('post_start')
#     post_end = fire.get('post_end')
    
#     ##region = fire.geometry()
#     #sensor = "landsat"

#     pre_collection = gic2.getLandsatToaRobust(pre_start,pre_end,region)
#     pre_img = gic.get_composite(pre_collection,gic.make_mean_composite,pre_start,pre_end)
#     #all bands in pre_img: ['BLUE', 'GREEN', 'RED', 'NIR', 'SWIR1', 'TEMP', 'SWIR2', 'QA_PIXEL', 'NDVI', 'NBR', 'EVI', 'constant', 'BRIGHTNESS', 'GREENNESS', 'WETNESS', 'GV', 'Shade', 'NPV', 'Soil', 'Cloud', 'NDFI', 'NDWI', 'NDMI', 'LSAVI', 'date']

#     post_collection = gic2.getLandsatToaRobust(post_start,post_end,region)
#     # gic2.getLandsatToa should return an empty image collection if no data is available
#         #  dev note: assumption is that gic.get_composite is the part that is failing if post_collection is empty
#         #  plan: create a nodata image as a placeholder
#         #        rdnbr_calc only use bands 'NIR','SWIR2', so only those made
#         # pc_size = post_collection.select('NIR').size()
#         # pc_nodata = ee.Image.constant(0).selfMask() \
#         #     .addBands(ee.Image.constant(0).selfMask()) \
#         #     .rename(['NIR','SWIR2']) \
#         #     .set('pc_size', pc_size) \
#         #     .set('system:time_start', ee.Date(post_end).millis()) #most likely no longer need (used in make_nrt_composite)
#         # #filter to only use when no images were returned
#         # pc_nodata_filt = ee.ImageCollection(pc_nodata).filter(ee.Filter.eq('pc_size', 0))
#         # #merge two together (one or the other will be empty)
#         # post_collection_robust = post_collection.merge(pc_nodata_filt)
#         # #continue with compositing
#     post_img = gic.get_composite(post_collection,gic.make_mean_composite,post_start,post_end) 

#     #  dev note: composite returns an image with no bands when no data, so need to handle 
#     #            otherwise rdnbr() will error on no 'NIR' band available
#     #  plan: create a nodata image as a placeholder
#     #        rdnbr_calc only use bands 'NIR','SWIR2', so only those made
#     #   logic test: base on the size of the bandname list, as there will be an image returned from get composite
#     post_img_band_size = post_img.bandNames().size()
#     post_img = post_img.set('pci_size', post_img_band_size)
#     pci_nodata = ee.Image.constant(0).selfMask() \
#         .addBands(ee.Image.constant(0).selfMask()) \
#         .rename(['NIR','SWIR2']) \
#         .set('pci_size', post_img_band_size) 
#     #filter to only use when no bands in composite
#     pci_nodata_filt = ee.ImageCollection(pci_nodata).filter(ee.Filter.eq('pci_size', 0))
#     post_data_filt = ee.ImageCollection(post_img).filter(ee.Filter.neq('pci_size', 0))
#     #merge two together (one or the other will be empty)
#     pc_img_merge = ee.ImageCollection(post_data_filt).merge(pci_nodata_filt)
#     #take first (will only ever be 1 image)
#     post_img_robust = ee.Image(pc_img_merge.first())

#     #Calculate RdNBR and Severity classes
#     rdnbr_calc = rdnbr(pre_img,post_img_robust) #band name 'RdNBR' 
#     miller = miller_thresholds4(rdnbr_calc) #band name 'MillersThresholds'

#     #create image with both bands ('RdNBR' and 'MillersThresholds')
#     # copies some properties over. Make sure to set up if switching to NIFC
#     combined = rdnbr_calc \
#         .addBands(miller.toByte()) \
#         .clip(region) \
#         .set('fire_id', fire.get('fire_id'))
#     return ee.Image(combined)

    
def bs_get_windows(feat: ee.Feature):
    #set the pre and post fire windows, using the simulation version of the function
    fire = ee.Feature(fi.set_windows_sim(feat))

    return fire

