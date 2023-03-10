class BucketType:
    TIMESERIES = 1
    HISTOGRAM = 2
    SCATTERPLOT = 3
    BARCHART = 4
    BUCKET_TYPES = (
        (TIMESERIES, 'timeseries'),
        (HISTOGRAM, 'histogram'),
        (SCATTERPLOT, 'scatterplot'),
        (BARCHART, 'barchart'),
    )
