import requests

url = 'https://folkets-lexikon.csc.kth.se/folkets/folkets_sv_en_public.xml'
response = requests.get(url)

with open('swe.xml', 'wb') as f:
    f.write(response.content)
