
# create mixin for search?
# https://developers.notion.com/reference/post-search


""" Search
POST
https://api.notion.com/v1/search
Searches all original pages, databases, and child pages/databases that are shared with the integration. It will not return linked databases, since these duplicate their source databases.

The query parameter matches against the page titles. If the query parameter is not provided, the response will contain all pages (and child pages) in the results.

The filter parameter can be used to query specifically for only pages or only databases.

The response may contain fewer than page_size of results. See Pagination for details about how to use a cursor to iterate through the list.

Integration capabilities

This endpoint is accessible from by integrations with any level of capabilities. The database and page objects returned will adhere to the limitations of the integration's capabilities. For more information on integration capabilities, see the capabilities guide.

Limitations of search
The search endpoint works best when it's being used to query for pages and databases by name. It is not optimized for the following use cases:

Exhaustively enumerating through all the documents a bot has access to in a workspace. Search is not guaranteed to return everything, and the index may change as your integration is iterating through pages and databases resulting in unstable results.
Searching or filtering within a particular database. This use case is much better served by finding the database ID and using the Query a database endpoint.
Immediate and complete results. Search indexing is not immediate. If an integration performs a search quickly after a page is shared with the integration (such as immediately after a user performs OAuth), the response may not contain the page.
When an integration needs to present a user interface that depends on search results, we recommend including a Refresh button to retry the search. This will allow users to determine if the expected result is present or not, and give them a means to try again.
Optimizations and recommended ways to use search
Search tends to work best when the request is as specific as possible. Where possible, we recommend filtering by object (such as page or database) and providing a text query to help narrow down results.

If search is very slow, specifying a smaller page_size can help. (The default page_size is 100.)

Our implementation of the search endpoint includes an optimization where any pages or databases that are directly shared with a bot (rather than shared via an ancestor) are guaranteed to be returned. If your use case requires pages or databases to immediately be available in search without an indexing delay, we recommend that you share relevant pages/databases with your integration directly.
"""