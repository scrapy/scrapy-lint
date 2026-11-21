.. _scp83:

============================
SCP83: Unused automap params
============================

What it does
============

When using :doc:`scrapy-zyte-api <scrapy-zyte-api:index>` together with
:doc:`scrapy-poet <scrapy-poet:index>`, reports :reqmeta:`zyte_api_automap`
params on a request whose callback, defined in the same module, type-hints a
parameter as :class:`~scrapy_poet.DummyResponse`.


Why is this bad?
================

:class:`~scrapy_poet.DummyResponse` tells scrapy-poet that the callback does
not use the response, so scrapy-poet skips the download and the params are
never sent to Zyte API. The page objects that the callback does use are
fetched by the scrapy-poet provider, which reads :reqmeta:`zyte_api_provider`.

The params look like they apply, but they do not. A ``geolocation`` meant to
determine which version of a website to scrape is silently ignored, and the
data you get back is not the data you asked for.


Example
=======

.. code-block:: python

    class MySpider(Spider):
        async def start(self):
            yield Request(
                "https://toscrape.com/",
                self.parse_product,
                meta={"zyte_api_automap": {"geolocation": "ie"}},
            )

        def parse_product(self, response: DummyResponse, product: Product):
            yield product

Use :reqmeta:`zyte_api_provider`:

.. code-block:: python

    yield Request(
        "https://toscrape.com/",
        self.parse_product,
        meta={"zyte_api_provider": {"geolocation": "ie"}},
    )


Known limitations
=================

A page object can declare :class:`~web_poet.page_inputs.http.HttpResponse` as
a dependency, in which case scrapy-poet does download the response and the
automap params do apply. Finding that out means following imports across
files, which this rule does not do, so mark the file with
:ref:`per-file-ignores` if you hit it.
