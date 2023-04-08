# Welcome to Django Insights

## Django Insights: Overview and Usage

Django Insights is a Django app that provides a easy way to generate application insights and store them in a SQLite database. These insights can be used to inform decisions about application design and to identify trends over time.

Examples of the types of insights you can gather include:

- number of users
- number of users invited in the past year
- number of reports generated per day
- number of messages sent on Wednesdays

While Django Insights can be used gather insights from your current application state, it is not suitable for tracking real-time metrics such as:

- number of GET requests for a specific URL per second
- real-time profit target percentage
