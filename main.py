import os
import time
import random
import threading
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from PIL import Image
import imagehash
from io import BytesIO
import requests

# إعدادات التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automation_farm.log"),
        logging.StreamHandler()
    ]
)

# إعدادات المزرعة
NUM_BROWSERS = 5  # عدد المتصفحات (أجهزة)
SESSION_DURATION = 8 * 3600  # 8 ساعات لكل جلسة
AD_CLICK_DELAY = (3, 7)  # تأخير عشوائي قبل النقر على الإعلان
POPUNDER_CHANCE = 0.2  # فرصة تفعيل إعلان منبثق عند الخروج (20%)

def human_like_mouse(driver, element=None):
    """محاكاة حركة ماوس بشرية نحو عنصر أو في الصفحة"""
    actions = ActionChains(driver)
    
    # حركة عشوائية في الصفحة
    if element is None:
        width, height = driver.execute_script("return [window.innerWidth, window.innerHeight];")
        for _ in range(random.randint(2, 5)):
            x = random.randint(0, width - 100)
            y = random.randint(0, height - 100)
            actions.move_by_offset(x, y)
            actions.pause(random.uniform(0.1, 0.5))
        actions.perform()
        return
    
    # حركة نحو العنصر
    location = element.location_once_scrolled_into_view
    size = element.size
    # التحرك إلى موقع قريب من العنصر
    actions.move_by_offset(
        location['x'] + random.randint(0, size['width']),
        location['y'] + random.randint(0, size['height'])
    )
    # حركات صغيرة عشوائية حول العنصر
    for _ in range(random.randint(2, 4)):
        actions.move_by_offset(
            random.randint(-20, 20),
            random.randint(-20, 20)
        ).pause(random.uniform(0.1, 0.3))
    actions.click()
    actions.perform()

def handle_ads(driver):
    """إدارة الإعلانات التفاعلية في الصفحة"""
    try:
        # نقر إعلانات Google (إذا وجدت)
        ad_frames = driver.find_elements(By.CSS_SELECTOR, "iframe[id^='google_ads_frame']")
        for frame in ad_frames:
            try:
                driver.switch_to.frame(frame)
                ad_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'http') and not(contains(@href, 'google'))]")
                if ad_links:
                    ad_link = random.choice(ad_links)
                    human_like_mouse(driver, ad_link)
                    time.sleep(random.uniform(*AD_CLICK_DELAY))
                    # افتح الإعلان في تبويب جديد
                    driver.execute_script("window.open(arguments[0]);", ad_link.get_attribute('href'))
                    # عد إلى الصفحة الأصلية
                    driver.switch_to.window(driver.window_handles[0])
                    # انتظر قليلاً ثم أغلق التبويب الجديد بعد فترة
                    time.sleep(random.uniform(10, 20))
                    if len(driver.window_handles) > 1:
                        driver.switch_to.window(driver.window_handles[1])
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                driver.switch_to.default_content()
            except Exception as e:
                logging.warning(f"خطأ في معالجة إعلان جوجل: {str(e)}")
                driver.switch_to.default_content()

        # التعامل مع الإعلانات البينية
        interstitial = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "interstitial-ad"))
        if interstitial.is_displayed():
            close_btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "interstitial-close"))
            time.sleep(random.uniform(5, 15))  # مشاهدة الإعلان
            human_like_mouse(driver, close_btn)
            logging.info("تم إغلاق إعلان بيني")
    except TimeoutException:
        pass  # لا يوجد إعلانات بينية ظاهرة

def automation_session(session_id):
    """جلسة أتمتة لمتصفح واحد"""
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--mute-audio")
    
    # إعدادات أخرى لتقليل استخدام الموارد وتجنب الكشف
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(random.randint(1024, 1366), random.randint(768, 1024))
    driver.get("https://tpmscool.web.app/")  # URL الموقع
    
    try:
        # بدء التشغيل بالنقر على زر البدء
        start_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "start-btn"))
        )
        human_like_mouse(driver, start_button)
        logging.info(f"الجلسة {session_id}: بدأت التشغيل")

        # ضبط الإعدادات لتحقيق أقصى ربح
        driver.execute_script("document.getElementById('device-slider').value = 10;")
        driver.execute_script("document.getElementById('speed-slider').value = 8;")
        save_settings = driver.find_element(By.ID, "save-settings")
        human_like_mouse(driver, save_settings)
        logging.info(f"الجلسة {session_id}: تم ضبط الإعدادات")

        start_time = time.time()
        last_interstitial = time.time()
        interstitial_interval = random.randint(180, 300)  # كل 3-5 دقائق
        
        while time.time() - start_time < SESSION_DURATION:
            # محاكاة السلوك البشري: حركة ماوس عشوائية
            human_like_mouse(driver)
            
            # إدارة الإعلانات
            handle_ads(driver)
            
            # تفعيل Popunder (عند الخروج) بشكل عشوائي
            if random.random() < POPUNDER_CHANCE:
                try:
                    popunder_btn = driver.find_element(By.ID, "show-popunder-btn")
                    human_like_mouse(driver, popunder_btn)
                    logging.info(f"الجلسة {session_id}: تم تفعيل إعلان منبثق")
                    # بعد تفعيل المنبثق، انتظر ثم أغلقه إذا ظهر
                    time.sleep(5)
                    handles = driver.window_handles
                    if len(handles) > 1:
                        driver.switch_to.window(handles[1])
                        driver.close()
                        driver.switch_to.window(handles[0])
                except Exception as e:
                    logging.warning(f"الجلسة {session_id}: فشل تفعيل المنبثق: {str(e)}")
            
            # فترات راحة عشوائية بين الإجراءات
            time.sleep(random.randint(15, 45))
            
            # كل فترة، قم بتحديث الصفحة لمحاكاة الجلسة الجديدة
            if random.random() < 0.05:  # 5% فرصة للتحديث
                driver.refresh()
                logging.info(f"الجلسة {session_id}: تم تحديث الصفحة")
                time.sleep(5)  # انتظر بعد التحديث
            
    except Exception as e:
        logging.error(f"الجلسة {session_id}: حدث خطأ: {str(e)}")
    finally:
        driver.quit()
        logging.info(f"الجلسة {session_id}: انتهت")

# تشغيل المزرعة
if __name__ == "__main__":
    threads = []
    for i in range(NUM_BROWSERS):
        t = threading.Thread(target=automation_session, args=(i+1,))
        t.daemon = True
        t.start()
        threads.append(t)
        logging.info(f"تم بدء الجلسة {i+1}")
        time.sleep(random.randint(10, 30))  # تأخير بين بدء الجلسات

    # انتظر حتى انتهاء جميع الجلسات (في الواقع، ستعمل لفترة SESSION_DURATION)
    for t in threads:
        t.join()
