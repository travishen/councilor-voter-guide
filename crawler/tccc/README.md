```
scrapy runspider suggestions.py -o ../../data/tccc/suggestions.json -s FEED_EXPORT_ENCODING=utf-8
scrapy runspider councilors.py -o ../../data/tccc/councilors.json -s FEED_EXPORT_ENCODING=utf-8
scrapy runspider councilors_terms.py -o ../../data/tccc/councilors_terms.json -s FEED_EXPORT_ENCODING=utf-8
scrapy runspider bills.py -o ../../data/tccc/bills.json -s FEED_EXPORT_ENCODING=utf-8
scrapy runspider meeting_minutes.py -o ../../data/tccc/meeting_minutes.json -s FEED_EXPORT_ENCODING=utf-8
```
