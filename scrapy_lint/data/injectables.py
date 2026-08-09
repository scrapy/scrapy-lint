from packaging.version import Version

# web-poet page inputs, mapped to the package and version that first provided
# them for dependency injection.
INJECTABLES = {
    "HttpClient": ("scrapy-poet", Version("0.4.0")),
    "HttpRequest": ("scrapy-poet", Version("0.17.0")),
    "HttpResponse": ("scrapy-poet", Version("0.4.0")),
    "PageParams": ("scrapy-poet", Version("0.4.0")),
    "RequestUrl": ("scrapy-poet", Version("0.4.0")),
    "ResponseUrl": ("scrapy-poet", Version("0.6.0")),
    "Stats": ("scrapy-poet", Version("0.15.0")),
}
