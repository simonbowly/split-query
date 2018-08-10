
# Next Generation

Want to generalise this code for plotting, machine learning, data mirroring.
In particular the API should be a generic interface; internals are not so pandas-specific (consider than an implementation detail) and part of the API translates between formats.

Given a `dataset` object which handles filtering and caching on the remote-side...

* Return a pandas dataframe after filtering.

```python
    (
        dataset
        .filter(
            df.timestamp.between(datetime(2018, 1, 1), datetime(2018, 2, 1))
            & df.tag.isin(['tag1', 'tag2']))
        .df()
    )
```

* Mirror the dataset by running a HTTP server.
The `dataset` object only requests and caches data it needs then provides an API to request it.

```python
    (
        dataset
        .serve_http()
    )
```

* Serve up transformed data by running a HTTP server.
Control caching of the downloaded or transformed data.
To be used as part of a data workflow with intermediary transforms by servers.

```python
    (
        dataset
        .transform()
        .cache()
        .serve_http()
    )
```

* Interface to matplotlib, altair, etc for plotting.

```python
    (
        dataset
        .filter(
            df.timestamp.between(datetime(2018, 1, 1), datetime(2018, 2, 1))
            & df.tag.isin(['tag1', 'tag2']))
        .pivot(index='datetime', columns='tag', values='value')
        .plot()
    )
```
