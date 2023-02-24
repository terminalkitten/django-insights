class BucketType:
    TIME_SERIES = 1
    HISTOGRAM = 2
    SCATTERPLOT = 3
    BUCKET_TYPES = (
        (TIME_SERIES, 'timeseries'),
        (HISTOGRAM, 'histogram'),
        (SCATTERPLOT, 'scatterplot'),
    )
