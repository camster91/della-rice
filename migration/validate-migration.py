"""Validate staging records without importing or changing either store."""
from pathlib import Path
from collections import Counter
from urllib.parse import urlparse
import csv,json
from bs4 import BeautifulSoup

R=Path(__file__).resolve().parent
summary=json.loads((R/'summary.json').read_text())
products=json.loads((R/'products.json').read_text())
pages=json.loads((R/'pages.json').read_text())
recipes=json.loads((R/'recipes.json').read_text())
errors=json.loads((R/'capture-errors.json').read_text())
assert not errors,errors
assert len(products)+len(pages)+len(recipes)==summary['sitemap_urls']
assert len({p['source_url'] for p in products+pages+recipes})==summary['sitemap_urls']
assert {p['currency'] for p in products}=={'USD'}
assert all(p['title'] and p['price'] and p['description_html'] and p['images'] for p in products)
assert len({p['source_product_id'] for p in products})==len(products)
assert len({p['handle'] for p in products})==len(products)
rows=list(csv.DictReader((R/'products-draft-USD.csv').open()))
first=[r for r in rows if r['Title']]
assert len(first)==len(products)
assert len(rows)==sum(len(p['images']) for p in products)
by_handle={p['handle']:p for p in products}
for row in first:
 p=by_handle[row['URL handle']]
 assert row['Status']=='draft' and row['Published on online store']=='false'
 assert row['Title']==p['title'] and row['Price']==p['price']
 assert row['Type']==p['category'] and row['Collection']==p['category']
 assert int(row['Weight value (grams)'])==p['weight_grams']
 assert row['Option1 name'] and row['Option1 value']
 assert len(row['SEO title'])<=70 and len(row['SEO description'])<=320
for kind,records in [('product',products),('page',pages),('recipe',recipes)]:
 for record in records:
  html=record.get('body_html',record.get('description_html',''))
  soup=BeautifulSoup(html,'html.parser')
  assert not soup.find(['script','style','form']),record['source_url']
  assert not soup.find(attrs={'onclick':True}),record['source_url']
  if kind=='recipe': assert record['content_characters']>100,record['source_url']
for p in products:
 for image in p['images']:assert urlparse(image['url']).hostname in {'dellarice.com','www.dellarice.com'}
result={'status':'passed','captured_source_urls':summary['sitemap_urls'],'product_rows':len(first),'product_image_rows':len(rows),
 'category_counts':dict(Counter(p['category'] for p in products)), 'prices_currency':'USD',
 'source_weights_grams':dict(Counter(str(p['weight_grams']) for p in products)),
 'capture_errors':0,'all_products_draft_and_unpublished':True,'shopify_import_verified':False,
 'limitations':['No destination write has occurred.','Inventory/SKUs/customers/orders require authenticated export.','Product media URLs are source references; Shopify image copy is unverified.','Animation rendering requires restored browser access.']}
(R/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
