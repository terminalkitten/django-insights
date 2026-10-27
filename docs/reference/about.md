---
title: About
description: Why Django Insights exists, and when it is the right tool.
sidebar:
  order: 4
---

## Use cases

Insights are gathered from the current state of your app. Django Insights is not meant as a realtime, incrementing data source: you should be able to gather the insights again from your actual data at any moment.

| Yes                                                            | No                                         |
| -------------------------------------------------------------- | ------------------------------------------ |
| How many users, how many users invited per year                | How many GET requests for URL X per second |
| How many reports per day, how many messages sent on Wednesdays | A realtime profit target percentage        |

## Background

I work at a small company that was renewing parts of its product. To gain insight into its usage over different periods we tried a few solutions: periodic CSV files from queries, and data sent to a dashboard at regular intervals.

We ended up with many exports spread out over multiple people. Exporting data directly from the database was also a security risk, as it meant constantly moving possibly sensitive information. After several months of CSV files, which were often outdated and needed conversion by other (paid) tools, we looked for something better.

I wanted an easy file in each of our apps to write "insights" in, so Django Insights was born. The insights go into a local SQLite database that can be shared on request, and as a plus, these files can be tracked by a security officer.

## Ideas

- Connect to other data sources and export to other file formats (Arrow, NDJSON).

## License

MIT. See [LICENSE](https://github.com/terminalkitten/django-insights/blob/main/LICENSE).
