import ee


def set_dates_recent_fixed(feat: ee.Feature):
    '''construct pre and post start and end dates using recent fire mode '''
    '''post window is a fixed 90-day window immediately post fire'''

    fire_date = ee.Date(feat.getString('Discovery'))
    
    pre_start = fire_date.advance(-365, 'day') # 1 year prior to discovery (same day as Discovery)
    pre_start_readable = ee.String(ee.Date(pre_start).format('YYYYMMdd')) 
    
    pre_end = fire_date.advance(-275, 'day')  # 1 year prior, 90 days after discovery
    pre_end_readable = ee.String(ee.Date(pre_end).format('YYYYMMdd'))

    post_start = fire_date.advance(1, 'day')  # actual fire discovery date ## do same Date.advance routine as others
    post_start_readable = ee.String(ee.Date(post_start).format('YYYYMMdd'))

    #nominal end date, actual window may be shorter, depending on run date 
    # i.e. post_end may be a future date
    post_end = fire_date.advance(90, 'day')   # 90 days after discovery
    post_end_readable = ee.String(ee.Date(post_end).format('YYYYMMdd'))
    
    return feat.set('pre_start',pre_start,'pre_start_readable',pre_start_readable,
                    'pre_end',pre_end, 'pre_end_readable',pre_end_readable,
                    'post_start',post_start, 'post_start_readable',post_start_readable,
                    'post_end',post_end, 'post_end_readable',post_end_readable,
                    'double_check','fixed')


def set_dates_recent_sliding(feat: ee.Feature):
    '''construct pre and post start and end dates using historic fire mode'''
    '''instead of using fixed window post fire, this slides along with the current (or sim) date, most RECENT 90 days'''
    ''' note: does not make allowances for latency in data availability'''
    ''' note: if less than 90 days since fire, takes range from fire to run/sim date'''
    '''Requires to be called from set_windows_sim or variant of it that has the 'run_date' property on each feature'''

    run_date = ee.Date(feat.getString('run_date'))
    fire_date = ee.Date(feat.getString('Discovery'))

    #post window will drive the other dates
    post_end = run_date
    post_end_readable = ee.String(ee.Date(post_end).format('YYYYMMdd'))

    #nominal post is a 90 window to run date
    post_start90 = run_date.advance(-90, 'day')
    #avoid edge case where less than 90 days between fire and run date
    #take the latest date between the start of a 90 day window or the fire date
    post_start = ee.Date(post_start90.millis().max(fire_date.advance(1,'day').millis())) 
    post_start_readable = ee.String(ee.Date(post_start).format('YYYYMMdd'))

    #pre window start is a year before, but always of the intended window (post_start90)
    pre_start = post_start90.advance(-365, 'day')
    pre_start_readable = ee.String(ee.Date(pre_start).format('YYYYMMdd')) 

    pre_end = post_end.advance(-365, 'day')
    pre_end_readable = ee.String(ee.Date(pre_end).format('YYYYMMdd')) 
    
    return feat.set('pre_start',pre_start,'pre_start_readable',pre_start_readable,
                        'pre_end',pre_end, 'pre_end_readable',pre_end_readable,
                        'post_start',post_start, 'post_start_readable',post_start_readable,
                        'post_end',post_end, 'post_end_readable',post_end_readable,
                        'double_check','sliding')


def set_dates_recent_expanding(feat: ee.Feature):
    '''construct pre and post start and end dates using historic fire mode'''
    '''instead of using fixed 90 day window post fire, this expands with how much data is available to current(or sim)'''
    ''' note: does not make allowances for latency in data availability'''
    '''Requires to be called from set_windows_sim or variant of it that has the 'run_date' property on each feature'''
    feature = ee.Feature(feat)

    run_date = ee.Date(feat.getString('run_date'))
    fire_date = ee.Date(feat.getString('Discovery'))

    #post window: from discovery+1 to run date
    post_start = fire_date.advance(1, 'day')
    post_start_readable = ee.String(ee.Date(post_start).format('YYYYMMdd'))

    post_end = run_date
    post_end_readable = ee.String(ee.Date(post_end).format('YYYYMMdd'))

    #pre window: can usually subtract a year from post window dates
    pre_start = post_start.advance(-365, 'day')
    pre_start_readable = ee.String(ee.Date(pre_start).format('YYYYMMdd'))
    # However, for shortened post windows due to timing of Discovery and run/sim date, 
    # we need a minimum window size or can/will run into no data issues in pre-window period.
    # Picking a 90-day window to be consistent with fixed/original and sliding window calculations 
    pre_end_365 = post_end.advance(-365, 'day')
    pre_end_90_365 = post_start.advance(90, 'day').advance(-365, 'day') 
    pre_end = ee.Date(pre_end_365.millis().max(pre_end_90_365.millis()))
    pre_end_readable = ee.String(ee.Date(pre_end).format('YYYYMMdd'))
    
    return feature.set('pre_start',pre_start, 'pre_start_readable',pre_start_readable,
                        'pre_end',pre_end, 'pre_end_readable',pre_end_readable,
                        'post_start',post_start, 'post_start_readable',post_start_readable,
                        'post_end',post_end, 'post_end_readable',post_end_readable,
                        'double_check','expanding')


def set_dates_historic_mode(feat: ee.Feature):
    '''construct pre and post start and end dates using recent fire mode'''
    feature = ee.Feature(feat)
    
    pre_start = ee.Date(feature.getString('Discovery')).advance(-455, 'day') # 1 year prior, 90 days before fire discovery
    pre_start_readable = ee.String(ee.Date(pre_start).advance(-455, 'day').format('YYYYMMdd')) # 1 year prior, 90 days before fire discovery

    pre_end = ee.Date(feature.getString('Discovery')).advance(-365, 'day')  # 1 year prior
    pre_end_readable = ee.String(ee.Date(pre_end).format('YYYYMMdd'))  # 1 year prior

    post_start = ee.Date(feature.getString('Discovery')).advance(275, 'day') # 1 year later, 90 days before fire discovery
    post_start_readable = ee.String(ee.Date(post_start).format('YYYYMMdd')) # 1 year later, 90 days before fire discovery

    post_end = ee.Date(feature.getString('Discovery')).advance(365, 'day') # 1 year later
    post_end_readable = ee.String(ee.Date(post_end).format('YYYYMMdd')) # 1 year later

    return feature.set('pre_start',pre_start, 'pre_start_readable',pre_start_readable,
                        'pre_end',pre_end, 'pre_end_readable',pre_end_readable,
                        'post_start',post_start, 'post_start_readable',post_start_readable,
                        'post_end',post_end, 'post_end_readable',post_end_readable,
                        'double_check', 'historical')


def set_windows_run(feat: ee.Feature):
    '''sets pre/post date windows in the feature's properties following ruleset based on recency of Fire Date'''
    '''uses a date property on each feature for either the default of today or a simulated run as if on past date'''
    fire = ee.Feature(feat)
    fire_date = ee.Date(fire.getString('Discovery'))
    # Get run date (set in main function, formatted same as Discovery)
    run_date = ee.Date(fire.getString('run_date'))
    difference = run_date.difference(fire_date,'day')

    # if fire date is more than a year ago we can use historical mode (1 yr pre 1 yr post) 
    # otherwise we have to use recent mode
    mode = ee.Algorithms.If(difference.gte(365),ee.String('historical'),ee.String('recent'))
    fire = fire.set('mode',mode)
    # get recent window type 
    recent_type = fire.get('recent_type')

    #Split for historic mode, and 3 types of recent mode
    fire = ee.Algorithms.If(condition = ee.String(mode).equals('historical'), 
        trueCase = set_dates_historic_mode(fire), 
        #if not historical, then recent mode
        falseCase = ee.Algorithms.If(condition = ee.String(recent_type).equals('expanding'), 
            trueCase = set_dates_recent_expanding(fire), 
            falseCase = ee.Algorithms.If(condition = ee.String(recent_type).equals('sliding'), 
                trueCase = set_dates_recent_sliding(fire), 
                #'fixed' recent mode, default
                falseCase = set_dates_recent_fixed(fire))))
    
    return fire
