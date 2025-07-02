import time
import random
import requests
from bs4 import BeautifulSoup
import re
import json
import threading
from urllib.parse import urljoin, urlparse
import logging
from fake_useragent import UserAgent

# إعدادات التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ad_automation.log'),
        logging.StreamHandler()
    ]
)

class ServerAdAutomation:
    def __init__(self):
        self.revenue = 0.0
        self.session_revenue_target = 0.5
        self.running = True
        self.session = requests.Session()
        self.ua = UserAgent()
        self.close_keywords = ["close", "exit", "dismiss", "x", "✕", "✖", "❌", "關閉", "关闭", "閉じる", "اغلاق"]
        self.ad_click_patterns = [
            r'ad\d+', 'ad_', 'banner', 'adsbox', 'ad-unit', 'ad_container', 'ad-wrapper',
            'ad-slot', 'adlink', 'adtext', 'advert', 'sponsor', 'promo', 'advertisement'
        ]
        self.visited_urls = set()
        
    def get_random_headers(self):
        """إنشاء رؤوس HTTP عشوائية لمحاكاة متصفحات مختلفة"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
    
    def rotate_user_agent(self):
        """تغيير وكيل المستخدم بشكل عشوائي"""
        self.session.headers.update({'User-Agent': self.ua.random})
    
    def is_ad_element(self, element):
        """فحص ما إذا كان العنصر هو إعلان"""
        # فحص من خلال السمات الشائعة للإعلانات
        attrs = element.attrs
        classes = ' '.join(attrs.get('class', [])).lower()
        id_ = attrs.get('id', '').lower()
        
        # البحث عن أنماط معروفة في الإعلانات
        for pattern in self.ad_click_patterns:
            if re.search(pattern, classes) or re.search(pattern, id_):
                return True
        
        # فحص الروابط الشائعة للإعلانات
        if element.name == 'a':
            href = attrs.get('href', '').lower()
            ad_domains = ['doubleclick.net', 'googleadservices.com', 'ad.doubleclick.net']
            if any(domain in href for domain in ad_domains):
                return True
                
        return False
    
    def is_close_element(self, element):
        """فحص ما إذا كان العنصر هو زر إغلاق"""
        # فحص النص الظاهر
        text = element.get_text().strip().lower()
        if any(keyword in text for keyword in self.close_keywords):
            return True
            
        # فحص خاصية aria-label
        aria_label = element.attrs.get('aria-label', '').lower()
        if any(keyword in aria_label for keyword in self.close_keywords):
            return True
            
        # فحص الأصناف (classes)
        classes = ' '.join(element.attrs.get('class', [])).lower()
        if any(keyword in classes for keyword in self.close_keywords):
            return True
            
        # فحص الصور (أيقونات الإغلاق)
        if element.name == 'img':
            src = element.attrs.get('src', '').lower()
            alt = element.attrs.get('alt', '').lower()
            if any(keyword in alt for keyword in self.close_keywords) or any(keyword in src for keyword in self.close_keywords):
                return True
                
        return False
    
    def find_and_simulate_close(self, soup, base_url):
        """البحث عن أزرار الإغلاق ومحاكاة النقر عليها"""
        potential_close_buttons = soup.find_all(['button', 'div', 'a', 'span', 'img'])
        close_buttons = [btn for btn in potential_close_buttons if self.is_close_element(btn)]
        
        if close_buttons:
            close_button = random.choice(close_buttons)
            logging.info("تم العثور على زر إغلاق")
            
            # محاكاة النقر عن طريق زيارة الرابط إذا كان موجودًا
            if close_button.name == 'a' and 'href' in close_button.attrs:
                close_url = close_button.attrs['href']
                if not close_url.startswith('http'):
                    close_url = urljoin(base_url, close_url)
                
                try:
                    response = self.session.get(close_url, timeout=10)
                    if response.status_code == 200:
                        logging.info("تمت محاكاة إغلاق الإعلان بنجاح")
                        self.revenue += random.uniform(0.01, 0.03)
                        return True
                except Exception as e:
                    logging.error(f"خطأ في محاكاة الإغلاق: {str(e)}")
        
        return False
    
    def find_and_click_ad(self, soup, base_url):
        """البحث عن إعلان ومحاكاة النقر عليه"""
        ads = soup.find_all(['div', 'a', 'iframe', 'ins'])
        ads = [ad for ad in ads if self.is_ad_element(ad)]
        
        if not ads:
            logging.info("لم يتم العثور على إعلانات")
            return False
            
        ad = random.choice(ads)
        logging.info("تم اختيار إعلان للنقر")
        
        # استخراج رابط النقر إذا كان متاحًا
        ad_link = None
        if ad.name == 'a' and 'href' in ad.attrs:
            ad_link = ad.attrs['href']
        elif ad.name == 'iframe' and 'src' in ad.attrs:
            ad_link = ad.attrs['src']
        elif 'data-href' in ad.attrs:
            ad_link = ad.attrs['data-href']
        elif 'onclick' in ad.attrs:
            # محاولة استخراج الرابط من حدث onclick
            onclick_js = ad.attrs['onclick']
            match = re.search(r'window\.open\(\s*[\'"](.+?)[\'"]\s*\)', onclick_js)
            if match:
                ad_link = match.group(1)
        
        if ad_link:
            if not ad_link.startswith('http'):
                ad_link = urljoin(base_url, ad_link)
                
            try:
                # محاكاة النقر بزيارة الرابط
                response = self.session.get(ad_link, timeout=15)
                if response.status_code == 200:
                    logging.info("تمت محاكاة النقر على الإعلان")
                    self.revenue += random.uniform(0.02, 0.05)
                    
                    # محاكاة وقت مشاهدة الإعلان
                    watch_time = random.uniform(8, 15)
                    logging.info(f"محاكاة مشاهدة الإعلان لمدة {watch_time:.1f} ثانية")
                    time.sleep(watch_time)
                    return True
            except Exception as e:
                logging.error(f"خطأ في محاكاة النقر على الإعلان: {str(e)}")
        
        return False
    
    def get_internal_links(self, soup, base_url):
        """الحصول على الروابط الداخلية من الصفحة"""
        internal_links = []
        domain = urlparse(base_url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link.attrs['href']
            
            # تجاهل الروابط الفارغة
            if not href or href.startswith('javascript:') or href.startswith('mailto:'):
                continue
                
            # تحويل الرابط إلى مطلق
            if not href.startswith('http'):
                href = urljoin(base_url, href)
                
            # التحقق من أن الرابط ينتمي لنفس النطاق
            if urlparse(href).netloc == domain and href not in self.visited_urls:
                internal_links.append(href)
                
        return internal_links
    
    def browse_page(self, url):
        """تصفح صفحة واحدة والتفاعل معها"""
        try:
            # تغيير وكيل المستخدم بشكل دوري
            if random.random() < 0.3:
                self.rotate_user_agent()
                
            # إضافة الصفحة إلى المواقع المزورة
            self.visited_urls.add(url)
            
            # طلب الصفحة
            response = self.session.get(url, headers=self.get_random_headers(), timeout=15)
            
            if response.status_code != 200:
                logging.warning(f"فشل في تحميل الصفحة: {response.status_code}")
                return False
                
            logging.info(f"تم تحميل الصفحة: {url}")
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # محاولة إغلاق الإعلانات المنبثقة
            self.find_and_simulate_close(soup, url)
            
            # محاولة النقر على إعلان
            self.find_and_click_ad(soup, url)
            
            # الحصول على الروابط الداخلية
            internal_links = self.get_internal_links(soup, url)
            
            # زيارة رابط داخلي عشوائي (40% احتمال)
            if internal_links and random.random() < 0.4:
                next_url = random.choice(internal_links)
                logging.info(f"زيارة الصفحة الداخلية: {next_url}")
                time.sleep(random.uniform(2, 5))  # انتظار قبل التصفح
                self.browse_page(next_url)
            
            return True
            
        except Exception as e:
            logging.error(f"خطأ في تصفح الصفحة: {str(e)}")
            return False
    
    def start_session(self, start_url):
        """بدء جلسة تصفح جديدة"""
        logging.info(f"بدء جلسة تصفح جديدة من: {start_url}")
        self.browse_page(start_url)
        
        # محاكاة وقت الجلسة
        session_duration = random.uniform(120, 300)  # 2-5 دقائق
        logging.info(f"مدة الجلسة: {session_duration:.1f} ثانية")
        time.sleep(session_duration)
        
        # إعادة تعيين جلسة HTTP
        self.session = requests.Session()
        self.visited_urls = set()
    
    def run(self, website_url, duration_hours=1):
        """تشغيل النظام لمدة محددة"""
        start_time = time.time()
        end_time = start_time + (duration_hours * 3600)
        session_count = 0
        
        while time.time() < end_time and self.running:
            session_count += 1
            logging.info(f"\nبدء الجلسة #{session_count}")
            
            # بدء جلسة تصفح
            self.start_session(website_url)
            
            # تقييم الأداء
            elapsed_hours = (time.time() - start_time) / 3600
            revenue_per_hour = self.revenue / elapsed_hours if elapsed_hours > 0 else 0
            
            logging.info(f"\nتقييم الأداء بعد {elapsed_hours:.2f} ساعات:")
            logging.info(f"- الإيراد الكلي: ${self.revenue:.2f}")
            logging.info(f"- معدل الإيراد/الساعة: ${revenue_per_hour:.2f}")
            
            # تعديل الاستراتيجية بناءً على الأداء
            if revenue_per_hour < 0.4:
                logging.info("زيادة وتيرة التفاعل مع الإعلانات...")
            elif revenue_per_hour > 0.6:
                logging.info("تقليل وتيرة التفاعل لتجنب الكشف...")
            
            # فترات راحة بين الجلسات (1-5 دقائق)
            break_time = random.randint(60, 300)
            logging.info(f"استراحة لمدة {break_time//60} دقائق و {break_time%60} ثانية")
            time.sleep(break_time)
        
        logging.info(f"\nانتهت الجلسة. الإيراد الكلي: ${self.revenue:.2f}")

# كيفية التشغيل
if __name__ == "__main__":
    # تكوين النظام
    WEBSITE_URL = "https://tpmscool.web.app"
    
    # إنشاء وتشغيل النظام
    automation_system = ServerAdAutomation()
    
    try:
        # تشغيل لمدة ساعة واحدة
        automation_system.run(WEBSITE_URL, duration_hours=1)
    except KeyboardInterrupt:
        logging.info("تم إيقاف النظام بواسطة المستخدم")
    except Exception as e:
        logging.error(f"حدث خطأ غير متوقع: {str(e)}")
