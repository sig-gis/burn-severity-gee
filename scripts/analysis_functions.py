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

def rdnbr_only_calc(feat: ee.Feature):
    fire = ee.Feature(fi.set_windows(feat))

    pre_start = fire.get('pre_start')
    pre_end = fire.get('pre_end')
    post_start = fire.get('post_start')
    post_end = fire.get('post_end')
    
    region = fire.geometry()
    sensor = "landsat"
    pre_collection = gic2.getLandsatToa(pre_start,pre_end,region)
    pre_img = gic.get_composite(pre_collection,gic.make_pre_composite,pre_start,pre_end)

    post_collection = gic2.getLandsatToa(post_start,post_end,region)
    post_img = gic.get_composite(post_collection,gic.make_nrt_composite, sensor) 
    
    rdnbr_calc = rdnbr(pre_img,post_img)
    
    return ee.Image(rdnbr_calc).clip(region)

def bs_calc_v2309(feat: ee.Feature):
    fire = ee.Feature(fi.set_windows_sim(feat))

    pre_start = fire.get('pre_start')
    pre_end = fire.get('pre_end')
    post_start = fire.get('post_start')
    post_end = fire.get('post_end')
    
    region = fire.geometry()
    sensor = "landsat"
    pre_collection = gic2.getLandsatToa(pre_start,pre_end,region)
    pre_img = gic.get_composite(pre_collection,gic.make_pre_composite,pre_start,pre_end)

    post_collection = gic2.getLandsatToa(post_start,post_end,region)
    post_img = gic.get_composite(post_collection,gic.make_nrt_composite, sensor) 
    
    rdnbr_calc = rdnbr(pre_img,post_img) #band name 'RdNBR' # 'RDNBR'?
    miller = miller_thresholds4(rdnbr_calc) #band name 'MillersThresholds'
    
    #create image with both bands
    combined = rdnbr_calc.select('RdNBR') \
        .addBands(miller.select('MillersThresholds').toByte()) \
        .clip(region)
    
    return ee.Image(combined)
    
    
   
