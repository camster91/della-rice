"""Prepare supported Shopify content payloads and a media inventory; no remote writes."""
from pathlib import Path
from urllib.parse import urlparse, urljoin
from collections import defaultdict
import csv,json
from bs4 import BeautifulSoup

R=Path(__file__).resolve().parent
products=json.loads((R/'products.json').read_text())
pages=json.loads((R/'pages.json').read_text())
recipes=json.loads((R/'recipes.json').read_text())
duplicates=json.loads((R/'recipe-duplicate-groups.json').read_text())
duplicate_urls={url for group in duplicates for url in group}
known={
 '/':'/', '/store/':'/collections/all','/shop/':'/collections/all',
 '/about/':'/pages/about','/about-us/':'/pages/about','/contact-us/':'/pages/contact',
 '/where-to-buy/':'/pages/where-to-buy','/find-us/':'/pages/where-to-buy','/wholesale/':'/pages/wholesale',
 '/new-home/':'/','/new-home-markup-revision-draft/':'/',
 '/store-markup-revision-draft/':'/collections/all',
 '/about-us-markup-revision-draft/':'/pages/about',
 '/contact-faq-markup-revision-draft/':'/pages/contact',
 '/where-to-buy-markup-revision-draft/':'/pages/where-to-buy',
 '/wholesale-markup-revision-draft/':'/pages/wholesale',
 '/privacy/':'/policies/privacy-policy','/terms/':'/policies/terms-of-service',
 '/refund_returns/':'/policies/refund-policy'
}
excluded={'/cart/','/checkout/','/my-account/','/product-markup-revision-draft/'}
for p in products:known[urlparse(p['source_url']).path]='/products/'+p['handle']
for p in recipes:known[urlparse(p['source_url']).path]='/blogs/recipes/'+p['handle']
for p in pages:
 path=urlparse(p['source_url']).path
 if path not in known and path not in excluded:known[path]='/pages/'+p['handle']

def rewrite(html):
 soup=BeautifulSoup(html,'html.parser')
 for a in soup.find_all('a',href=True):
  u=urlparse(urljoin('https://dellarice.com/',a['href']))
  path=u.path if u.path.endswith('/') else u.path+'/'
  if u.hostname in {'dellarice.com','www.dellarice.com'} and path in known:
   a['href']=known[path]+('#'+u.fragment if u.fragment else '')
 return str(soup)

payload=[]
for p in pages:
 path=urlparse(p['source_url']).path;target=known.get(path)
 kind='policy' if target and target.startswith('/policies/') else 'page'
 payload.append({'source_url':p['source_url'],'source_handle':p['handle'],'destination_path':target,
  'title':p['title'],'body_html':rewrite(p['body_html']),
  'is_published':False,'resource_kind':kind,'seo':{'title':p['source_title'],'description':p['source_meta_description']},
  'migration_action':'exclude_dynamic_or_review_mockup' if path in excluded else 'already_recreated_design' if target in {'/','/collections/all','/pages/about','/pages/contact','/pages/where-to-buy','/pages/wholesale'} else 'merchant_review_policy' if kind=='policy' else 'create_draft_page',
  'media_status':'requires_shopify_cdn_copy','source_robots':p['source_robots']})
(R/'page-import-staging.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
articles=[]
for p in recipes:
 articles.append({'source_url':p['source_url'],'source_handle':p['handle'],'destination_path':known[urlparse(p['source_url']).path],
  'blog_handle':'recipes','title':p['title'],'handle':p['handle'],'body_html':rewrite(p['body_html']),
  'is_published':False,'video_urls':p['video_urls'],'seo':{'title':p['source_title'],'description':p['source_meta_description']},
  'duplicate_review_required':p['source_url'] in duplicate_urls,'media_status':'requires_shopify_cdn_copy'})
(R/'recipe-import-staging.json').write_text(json.dumps(articles,ensure_ascii=False,indent=2)+'\n')

media=defaultdict(lambda:{'references':[]})
for kind,records in [('product',products),('page',pages),('recipe',recipes)]:
 for p in records:
  for image in p['images']:
   url=image['url']
   if url and urlparse(url).hostname in {'dellarice.com','www.dellarice.com'}:
    media[url]['references'].append({'kind':kind,'handle':p['handle'],'alt':image.get('alt','')})
  if kind!='product':
   soup=BeautifulSoup(p['body_html'],'html.parser')
   for a in soup.find_all('a',href=True):
    url=a['href']
    if urlparse(url).hostname in {'dellarice.com','www.dellarice.com'} and urlparse(url).path.lower().endswith(('.pdf','.zip','.jpg','.jpeg','.png','.webp','.svg')):
     media[url]['references'].append({'kind':kind,'handle':p['handle'],'label':a.get_text(' ',strip=True)})
(R/'media-manifest.json').write_text(json.dumps([{'source_url':url,**data,'shopify_url':None,'copy_status':'pending'} for url,data in sorted(media.items())],ensure_ascii=False,indent=2)+'\n')
with (R/'redirect-candidates.csv').open('w',newline='') as file:
 w=csv.writer(file,lineterminator='\n');w.writerow(['Redirect from','Redirect to'])
 for source,target in sorted(known.items()):
  if source!=target:w.writerow([source,target])
summary={'products':len(products),'product_gallery_references':sum(len(p['images']) for p in products),
 'source_pages':len(pages),'source_recipes':len(recipes),'unique_media_files':len(media),
 'recipe_duplicate_groups':len(duplicates),'recipes_in_duplicate_groups':len(duplicate_urls),
 'proposed_new_pages':sum(x['migration_action']=='create_draft_page' for x in payload),
 'review_required_policies':sum(x['resource_kind']=='policy' for x in payload),
 'target_currency_check':'must_confirm_USD_before_product_import','shopify_write_status':'not_started_browser_unavailable'}
(R/'import-readiness.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
