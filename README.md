!["Django Insights"](docs/img/banner.png)

## Background

I'm currently working at a small company that is in the process of renewing some parts of our product. To gain insight into the usage over different periods, we have tried a few solutions. We initially attempted to periodically generate CSV files from queries, as well as send data to a dashboard at regular intervals.

However, these methods were quite cumbersome, and I was looking for a more streamlined solution. I wanted an easy-to-configure file within our various apps that would allow me to create "insights" easily.

So we ended up with multiple CSV files that where spread out over multiple people. Additionally, exporting data directly from the database also posed a security risk, as it required constant movement of possible sensitive information. After several months of working with CSV files, which were often outdated and required conversion by other (paid) tools, we where looking for a better solution.

So Django Insights was born, we decided to switch to a local SQLite database which we could share on request and could by tracked by our security officer.

## Features

Some of it’s stand out features are:

## Installation

Installing with:

```bash
pip install 'django-insights'
```

## Usage

Write more about using code in other projects

Migrate insights database:

```bash
$ workon myapp
$ python manage.py migrate insights --database=insights
```

## Documentation

Write more about where to find documentation

## Ideas

-

## Is it any good?

[Yes.](http://news.ycombinator.com/item?id=3067434)

## License

The MIT License
