from bs4 import BeautifulSoup
import requests
import pytz
from datetime import datetime
from functools import lru_cache
import time
from ..services.translator import TranslatorService
from flask import current_app
from ..models.article import DailyNewsletter
import logging

@lru_cache(maxsize=128)
def get_newsletter(date=None):
    if date is None:
        et = pytz.timezone('US/Eastern')
        date = datetime.now(et).strftime('%Y-%m-%d')
    
    # 先查询数据库
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        newsletter = DailyNewsletter.objects(date=date_obj).first()
        if newsletter:
            logging.info(f"Found newsletter for {date} in database")
            return newsletter.sections
    except Exception as e:
        logging.error(f"Error querying database: {str(e)}")
    
    # 如果数据库中没有，则获取新数据
    articles = fetch_tldr_content(date)
    if articles:
        try:
            newsletter = DailyNewsletter(
                date=date_obj,
                sections=articles
            )
            newsletter.save()
            logging.info(f"Saved newsletter for {date} to database")
        except Exception as e:
            logging.error(f"Error saving to database: {str(e)}")
    
    return articles

def fetch_tldr_content(date=None):
    if date is None:
        et = pytz.timezone('US/Eastern')
        date = datetime.now(et).strftime('%Y-%m-%d')
    
    url = f"https://tldr.tech/tech/{date}"
    logging.info(f"Fetching content from: {url}")
    
    try:
        response = requests.get(url)
        logging.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = []
            
            sections = soup.find_all('section')
            logging.info(f"Found {len(sections)} sections")
            
            for section in sections:
                header = section.find('h3', class_='text-center font-bold')
                if not header:
                    continue
                
                section_title = header.text.strip()
                if "sponsor" in section_title.lower():
                    continue
                
                logging.info(f"Processing section: {section_title}")
                section_content = []
                
                for article in section.find_all('article', class_='mt-3'):
                    title_elem = article.find('h3')
                    if not title_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    if "sponsor" in title.lower():
                        continue
                    
                    translator = TranslatorService(current_app.config['DEEPL_API_KEY'])
                    
                    content = article.find('div', class_='newsletter-html')
                    content_html = ''.join(str(tag) for tag in content.contents) if content else ""
                    
                    # 翻译标题和内容
                    title_zh = translator.translate_to_chinese(title)
                    content_html_zh = translator.translate_to_chinese(content_html)
                    
                    link = article.find('a', class_='font-bold')
                    url = link['href'] if link else ""
                    
                    logging.info(f"Processed article: {title}")
                    
                    # 构建双语内容
                    article_content = {
                        'title': title_zh,
                        'title_en': title,
                        'content': content_html_zh,
                        'content_en': content_html,
                        'url': url
                    }
                    section_content.append(article_content)
                
                if section_content:
                    articles.append({
                        'section': section_title,
                        'articles': section_content
                    })
            
            logging.info(f"Returning {len(articles)} articles")
            return articles
            
    except Exception as e:
        logging.error(f"Error fetching content: {str(e)}")
        return []
