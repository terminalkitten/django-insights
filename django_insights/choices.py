class BucketType:
    TIMESERIES = 1
    HISTOGRAM = 2
    SCATTERPLOT = 3
    BUCKET_TYPES = (
        (TIMESERIES, 'timeseries'),
        (HISTOGRAM, 'histogram'),
        (SCATTERPLOT, 'scatterplot'),
    )
