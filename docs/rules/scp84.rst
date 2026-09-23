.. _scp84:

==============================
SCP84: Missing provider params
==============================

What it does
============

When using :doc:`scrapy-zyte-api <scrapy-zyte-api:index>` together with
:doc:`scrapy-poet <scrapy-poet:index>`, reports :reqmeta:`zyte_api_automap`
params set without :reqmeta:`zyte_api_provider` params on a request whose
callback, defined in the same module, takes page object or item parameters,
i.e. parameters whose type hint comes from :doc:`web-poet <web-poet:index>`,
scrapy-poet or :doc:`zyte-common-items <zyte-common-items:index>`.


Why is this bad?
================

Such a callback gets its response from the automap request and its page
objects from a separate request that the scrapy-poet provider sends. The
provider ignores automap params, so a param meant for the whole request, such
as ``geolocation``, applies to one of those requests and not to the other.


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

        def parse_product(self, response, product: Product):
            yield product

Set the param for both requests:

.. code-block:: python

    yield Request(
        "https://toscrape.com/",
        self.parse_product,
        meta={
            "zyte_api_automap": {"geolocation": "ie"},
            "zyte_api_provider": {"geolocation": "ie"},
        },
    )
