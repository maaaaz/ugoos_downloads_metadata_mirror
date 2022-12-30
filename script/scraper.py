#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import argparse
import requests
import functools
import concurrent.futures
import json
import csv

import code
import pprint

from os import path
from lxml.html.soupparser import fromstring as fromstringhtml

# Script version
VERSION = '1.0'

# Options definition
parser = argparse.ArgumentParser(description="version: " + VERSION)
parser.add_argument('-o', '--output-dir', help='Output directory (default: current working directory)', default = os.getcwd())

# Globals
UGOOS_BASE_URL = 'https://ugoos.com'

def sort_results_by_index_desc(data):
    try:
        return int(data['id'])
        
    except KeyError:
        return 0

def scrape(product, output_dir):
    global UGOOS_BASE_URL
    
    product_id = product.xpath('string(./a/@id)')
    product_name = product.xpath('string(./a/span/text())')
    product_downloads_url = UGOOS_BASE_URL + '/getfiles?product_id=%s' % product_id
    
    data_scraped = json.loads(requests.get(product_downloads_url).content)
    
    if data_scraped:
        if isinstance(data_scraped, dict):
            data_scraped = list(data_scraped.values())
        
        print(f'product_id:{product_id} | "{product_name}" | {len(data_scraped)} entries')
        
        data_scraped.sort(key=sort_results_by_index_desc, reverse=True)
        
        output_file = os.path.abspath(os.path.join(output_dir, "%s_%s.txt"%(product_id, product_name)))
        with open(output_file, mode='w', encoding='utf-8') as fd_output:
            pprint.pprint(data_scraped, stream=fd_output)
        
    return data_scraped

def generate_synthesis(futs, output_dir):
    global UGOOS_BASE_URL
    output_file = os.path.abspath(os.path.join(output_dir, "ugoos_downloads_summary.csv"))
    
    keys = ['product_id', 'product_name', 'update_id', 'title', 'file', 'link', 'file_size', 'stick', 'category_id', 'created_at', 'updated_at']
    
    with open(output_file, mode='w', encoding='utf-8') as fd_output:
        spamwriter = csv.writer(fd_output, delimiter=',', quoting=csv.QUOTE_ALL, lineterminator='\n')
        spamwriter.writerow(keys)
        
        for product, fut in futs:
            product_name = product.xpath('string(./a/span/text())')
            for product_entry in fut.result():
                output_line = [product_entry['product_id'], 
                               product_name, product_entry['id'],
                               product_entry['title'],
                               "%s" % (UGOOS_BASE_URL + '/' + product_entry['file']) if product_entry['file'] else None,
                               product_entry['link'],
                               product_entry['file_size'],
                               product_entry['stick'],
                               product_entry['category_id'],
                               product_entry['created_at'],
                               product_entry['updated_at']]
                               
                spamwriter.writerow(output_line)
            spamwriter.writerow([]) 

def main():
    global parser, UGOOS_BASE_URL
    
    options = parser.parse_args()
    
    products_data = []
    
    download_page_url = UGOOS_BASE_URL + '/downloads'
    products_data = fromstringhtml(requests.get(download_page_url).content).xpath('//div[@class="product__card"]')
    
    if products_data:
        print("[+] %s products\n" % len(products_data))
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futs = [ (product, executor.submit(functools.partial(scrape, product, options.output_dir)))
                    for product in products_data ]
            
            if futs: 
                generate_synthesis(futs, options.output_dir)
        
    return
    
if __name__ == "__main__" :
    main()