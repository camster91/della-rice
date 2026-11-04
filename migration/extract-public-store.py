"""Read-only capture of Della's public sitemap content; never reads account data.

Requires requests and beautifulsoup4. No Shopify writes are performed.
"""
from pathlib import Path
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
from collections import defaultdict
from html import escape
import csv, hashlib, json, re, requests, sys, xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent
CACHE=Path('/tmp/della-public-migration-cache'); CACHE.mkdir(exist_ok=True)
NS={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
HOST='dellarice.com'

def fetch(url):
    if urlparse(url).hostname not in {HOST,'www.'+HOST}: raise ValueError('Out-of-scope source host')
    cache=CACHE/(hashlib.sha256(url.encode()).hexdigest()+'.html')
    if cache.exists(): return cache.read_text()
    response=requests.get(url,timeout=35,headers={'User-Agent':'DellaRiceMigration/1.0 (read-only content inventory)'})
    response.raise_for_status()
    if urlparse(response.url).hostname not in {HOST,'www.'+HOST}: raise ValueError('Unexpected cross-host redirect')
    cache.write_text(response.text)
    return response.text

def nodes(soup):
    result=[]
    for node in soup.select('script[type="application/ld+json"]'):
        try:
            data=json.loads(node.string or node.get_text())
            if isinstance(data,dict): result.extend(data.get('@graph',[data]))
            elif isinstance(data,list):result.extend(data)
        except (ValueError,TypeError): pass
    return result

def of_type(node,name):
    return name in (node.get('@type',[]) if isinstance(node.get('@type'),list) else [node.get('@type')])

def meta(soup,name):
    node=soup.find('meta',attrs={'name':name})
    return node.get('content','') if node else ''

def clean(fragment):
    if fragment is None:return ''
    soup=BeautifulSoup(str(fragment),'html.parser')
    for element in soup.select('script,style,noscript,form,nav,header,footer,button,.print-btn,.elementor-widget-divider'):
        element.decompose()
    allowed={'p','h1','h2','h3','h4','h5','h6','ul','ol','li','strong','b','em','i','br','a','img','figure','figcaption','table','thead','tbody','tr','th','td','blockquote','hr'}
    for element in list(soup.find_all(True)):
        if element.name not in allowed:
            element.unwrap();continue
        attrs={}
        if element.name=='a':
            href=urljoin('https://dellarice.com/',element.get('href',''))
            if href.startswith(('https://','http://','mailto:','tel:')):attrs={'href':href}
            else:element.unwrap();continue
        elif element.name=='img':
            src=element.get('data-src') or element.get('data-lazy-src') or element.get('src','')
            if not src.startswith(('https://','http://')):element.decompose();continue
            attrs={'src':src,'alt':element.get('alt',''),'loading':'lazy'}
            for key in ('width','height'):
                if str(element.get(key,'')).isdigit():attrs[key]=element[key]
        element.attrs=attrs
        if element.name=='h1':element.name='h2'
    for element in list(soup.find_all(['p','h2','h3','h4','h5','h6'])):
        if not element.get_text(strip=True) and not element.find('img'):element.decompose()
    return str(soup).strip()

def shared(url,soup):
    canonical=soup.select_one('link[rel="canonical"]')
    return {'source_url':url,'source_canonical':canonical.get('href') if canonical else url,
            'source_title':soup.title.get_text(strip=True) if soup.title else '',
            'source_meta_description':meta(soup,'description'),'source_robots':meta(soup,'robots')}

def product(url,soup):
    graph=nodes(soup); data=next((n for n in graph if of_type(n,'Product')),None)
    if not data:raise ValueError('No Product structured data')
    title=soup.select_one('h1.product_title')
    offers=data.get('offers',{}); offers=offers[0] if isinstance(offers,list) and offers else offers
    if offers.get('@type')=='AggregateOffer':raise ValueError('Variable/aggregate product needs authenticated variant export')
    if soup.select_one('form.variations_form'):raise ValueError('Variable product needs authenticated variant export')
    gallery=[]
    for image in soup.select('.woocommerce-product-gallery__image a'):
        src=image.get('href');alt=image.img.get('alt','') if image.img else ''
        if src and urlparse(src).hostname in {HOST,'www.'+HOST}:gallery.append({'url':src,'alt':alt})
    if not gallery:
        for image in data.get('image',[]):
            src=image.get('url') if isinstance(image,dict) else image
            if src:gallery.append({'url':src,'alt':title.get_text(strip=True) if title else ''})
    sku=soup.select_one('.sku');button=soup.select_one('button[name="add-to-cart"]')
    desc=soup.select_one('.woocommerce-product-details__short-description')
    weight=data.get('weight') or {}
    if weight.get('unitCode')=='KGM':grams=int(Decimal(str(weight['value']))*1000)
    elif weight.get('unitCode')=='GRM':grams=int(Decimal(str(weight['value'])))
    else:grams=None
    return {**shared(url,soup),'handle':urlparse(url).path.strip('/').split('/')[-1],
            'source_product_id':button.get('value') if button else None,
            'title':title.get_text(' ',strip=True) if title else data['name'],
            'description_html':clean(desc),'schema_description':data.get('description',''),
            'category':data.get('category',''),'price':str(offers.get('price','')),
            'currency':offers.get('priceCurrency'),'source_availability':offers.get('availability'),
            'sku':sku.get_text(strip=True) if sku else data.get('sku'),
            'weight_grams':grams,'source_dimensions':{k:data.get(k) for k in ['height','width','depth']},
            'images':gallery,'inventory_quantity':None,'barcode':data.get('gtin13') or data.get('gtin12'),
            'capture_status':'public_source_verified','shopify_status':'not_imported'}

def content(url,soup,kind):
    handle=urlparse(url).path.strip('/').split('/')[-1] or 'home'
    fragment=soup.select_one('[data-elementor-type="wp-post"]') or soup.select_one('[data-elementor-type="wp-page"]') or soup.select_one('.elementor-location-single') or soup.select_one('main') or soup.select_one('#content')
    if fragment is None:
        # Some Elementor pages render several sibling containers; exclude shared shells.
        candidates=[n for n in soup.select('[data-elementor-type]') if n.get('data-elementor-type') not in {'header','footer','popup'}]
        fragment=max(candidates,key=lambda n:len(n.get_text()),default=None)
    videos=[]
    if fragment:
        for element in fragment.select('[data-settings]'):
            try:
                settings=json.loads(element.get('data-settings','{}'))
                for key in ['youtube_url','vimeo_url','hosted_url']:
                    value=settings.get(key)
                    if isinstance(value,dict):value=value.get('url')
                    if isinstance(value,str) and value.startswith('https://'):videos.append(value)
            except ValueError:pass
    body=clean(fragment)
    for video in dict.fromkeys(videos):body+=f'<p><a href="{escape(video,quote=True)}">Watch the recipe video</a></p>'
    title=soup.select_one('.elementor-location-single h1') or soup.select_one('h1')
    base=shared(url,soup)
    title_text=title.get_text(' ',strip=True) if title else re.split(r' - Della Rice| \| Della Rice',base['source_title'])[0]
    text=BeautifulSoup(body,'html.parser').get_text(' ',strip=True)
    return {**base,'handle':handle,'title':title_text,'kind':kind,'body_html':body,'video_urls':list(dict.fromkeys(videos)),
            'images':[dict(url=i.get('src'),alt=i.get('alt','')) for i in BeautifulSoup(body,'html.parser').find_all('img')],
            'content_hash':hashlib.sha256(re.sub(r'\s+',' ',text).casefold().encode()).hexdigest(),
            'content_characters':len(text),'shopify_status':'not_imported'}

def run():
    index=ET.fromstring(fetch('https://dellarice.com/sitemap_index.xml'))
    urls=[]
    for node in index.findall('s:sitemap/s:loc',NS):
        sitemap=ET.fromstring(fetch(node.text))
        for child in sitemap.findall('s:url/s:loc',NS):
            url=child.text
            kind='product' if '/product/' in urlparse(url).path else 'recipe' if '/recipe/' in urlparse(url).path else 'page'
            urls.append((url,kind))
    products=[];pages=[];recipes=[];errors=[]
    def parse(item):
        url,kind=item;soup=BeautifulSoup(fetch(url),'html.parser')
        return kind,product(url,soup) if kind=='product' else content(url,soup,kind)
    with ThreadPoolExecutor(max_workers=4) as pool:
        tasks={pool.submit(parse,item):item for item in urls}
        for n,future in enumerate(as_completed(tasks),1):
            try:
                kind,record=future.result();{'product':products,'page':pages,'recipe':recipes}[kind].append(record)
            except Exception as exc:errors.append({'source_url':tasks[future][0],'error':str(exc)})
            if n%25==0:print(f'Captured {n}/{len(urls)} URLs',flush=True)
    for name,records in [('products',products),('pages',pages),('recipes',recipes)]:
        records.sort(key=lambda x:x['source_url']);(ROOT/f'{name}.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'capture-errors.json').write_text(json.dumps(errors,indent=2)+'\n')
    currencies=sorted(set(x['currency'] for x in products));assert currencies==['USD'],f'Unexpected currencies: {currencies}'
    columns=['URL handle','Title','Description','Vendor','Type','Tags','Published on online store','Status','Option1 name','Option1 value','Price','Weight value (grams)','Weight unit for display','Requires shipping','Product image URL','Image position','Image alt text','SEO title','SEO description','Collection']
    with (ROOT/'products-draft-USD.csv').open('w',newline='',encoding='utf-8') as file:
        writer=csv.DictWriter(file,fieldnames=columns,lineterminator='\n');writer.writeheader()
        for p in products:
            row={'URL handle':p['handle'],'Title':p['title'],'Description':p['description_html'],'Vendor':'Della Rice','Type':p['category'],'Tags':p['category'],'Published on online store':'false','Status':'draft','Option1 name':'Title','Option1 value':'Default Title','Price':p['price'],'Weight value (grams)':p['weight_grams'] if p['weight_grams'] is not None else '', 'Weight unit for display':'oz','Requires shipping':'true','SEO title':p['source_title'][:70].rsplit(' ',1)[0] if len(p['source_title'])>70 else p['source_title'],'SEO description':p['source_meta_description'][:320].rsplit(' ',1)[0] if len(p['source_meta_description'])>320 else p['source_meta_description'],'Collection':p['category']}
            images=p['images'] or [{}]
            row.update({'Product image URL':images[0].get('url',''),'Image position':1,'Image alt text':images[0].get('alt','')});writer.writerow(row)
            for position,image in enumerate(images[1:],2):writer.writerow({'URL handle':p['handle'],'Product image URL':image['url'],'Image position':position,'Image alt text':image['alt']})
    duplicate_groups=defaultdict(list)
    for r in recipes:
        if r['content_characters']>0:duplicate_groups[r['content_hash']].append(r['source_url'])
    duplicates=[v for v in duplicate_groups.values() if len(v)>1]
    (ROOT/'recipe-duplicate-groups.json').write_text(json.dumps(duplicates,indent=2)+'\n')
    product_map={urlparse(p['source_url']).path:'/products/'+p['handle'] for p in products}
    page_map={'/':'/','/store/':'/collections/all','/shop/':'/collections/all','/about/':'/pages/about','/about-us/':'/pages/about','/contact-us/':'/pages/contact','/where-to-buy/':'/pages/where-to-buy','/wholesale/':'/pages/wholesale','/cart/':'/cart','/checkout/':'/checkout','/my-account/':'/account'}
    with (ROOT/'redirect-candidates.csv').open('w',newline='') as file:
        writer=csv.writer(file,lineterminator='\n');writer.writerow(['Redirect from','Redirect to'])
        for source,target in sorted({**product_map,**{urlparse(r['source_url']).path:'/blogs/recipes/'+r['handle'] for r in recipes},**page_map}.items()):
            if source!=target:writer.writerow([source,target])
    summary={'sitemap_urls':len(urls),'products':len(products),'product_images':sum(len(p['images']) for p in products),'pages':len(pages),'recipes':len(recipes),'recipe_duplicate_groups':len(duplicates),'errors':len(errors),'source_currencies':currencies,'shopify_imported':False,'note':'Public content only. Private stock counts, unpublished products, customers, orders, coupons, tax and payment settings require authenticated export. Verify Shopify currency is USD before importing prices. All product rows are draft and unpublished.'}
    (ROOT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__':run()
