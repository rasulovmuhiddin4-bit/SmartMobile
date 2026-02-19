import sqlite3
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

class Database:
    def __init__(self, db_name):
        self.db_name = db_name
        self.init_db()
        # Jadvalni yangilash - bu qatorni olib tashlaymiz yoki kommentariya qilamiz
        # self.update_exchange_offers_table()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Foydalanuvchilar jadvali
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                location TEXT NOT NULL,
                language TEXT DEFAULT 'uz',
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_blocked INTEGER DEFAULT 0,
                is_admin INTEGER DEFAULT 0
            )
        ''')
        
        # Elonlar jadvali
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ads (
                ad_id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT NOT NULL,
                model TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT,
                photo_id TEXT,
                seller_name TEXT NOT NULL,
                seller_phone TEXT NOT NULL,
                seller_location TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # Sevimlilar jadvali
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER,
                ad_id INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (ad_id) REFERENCES ads (ad_id),
                PRIMARY KEY (user_id, ad_id)
            )
        ''')
        
        # Ayirboshlash takliflari jadvali (barcha ustunlar optional)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exchange_offers (
                offer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_phone TEXT,
                user_name TEXT,
                wanted_brand TEXT,
                wanted_model TEXT,
                offer_brand TEXT,
                offer_model TEXT,
                offer_description TEXT,
                offer_text TEXT,
                photos TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logging.info("Database initialized successfully")
    
    # Foydalanuvchi funksiyalari
    def add_user(self, user_id, full_name, phone, location, language='uz'):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, full_name, phone, location, language)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, full_name, phone, location, language))
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error adding user: {e}")
            return False
        finally:
            conn.close()
    
    def get_user(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'user_id': user[0],
                'full_name': user[1],
                'phone': user[2],
                'location': user[3],
                'language': user[4],
                'registered_at': user[5],
                'is_blocked': user[6],
                'is_admin': user[7]
            }
        return None
    
    def get_all_users(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users ORDER BY registered_at DESC')
        users = cursor.fetchall()
        conn.close()
        return users
    
    def update_user_language(self, user_id, language):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (language, user_id))
        conn.commit()
        conn.close()
    
    def block_user(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_blocked = 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    
    def unblock_user(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_blocked = 0 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    
    # Elon funksiyalari
    def add_ad(self, brand, model, price, description, photo_id, seller_name, seller_phone, seller_location):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO ads (brand, model, price, description, photo_id, seller_name, seller_phone, seller_location)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (brand, model, price, description, photo_id, seller_name, seller_phone, seller_location))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logging.error(f"Error adding ad: {e}")
            return None
        finally:
            conn.close()
    
    def get_ads_by_brand(self, brand):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM ads WHERE brand = ? AND is_active = 1
            ORDER BY created_at DESC
        ''', (brand,))
        ads = cursor.fetchall()
        conn.close()
        return ads
    
    def get_ad(self, ad_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM ads WHERE ad_id = ?', (ad_id,))
        ad = cursor.fetchone()
        conn.close()
        return ad
    
    def get_all_ads(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM ads WHERE is_active = 1 ORDER BY created_at DESC')
        ads = cursor.fetchall()
        conn.close()
        return ads
    
    # Sevimlilar funksiyalari
    def add_to_favorites(self, user_id, ad_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO favorites (user_id, ad_id)
                VALUES (?, ?)
            ''', (user_id, ad_id))
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error adding to favorites: {e}")
            return False
        finally:
            conn.close()
    
    def remove_from_favorites(self, user_id, ad_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM favorites WHERE user_id = ? AND ad_id = ?', (user_id, ad_id))
        conn.commit()
        conn.close()
    
    def get_user_favorites(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ads.* FROM ads
            JOIN favorites ON ads.ad_id = favorites.ad_id
            WHERE favorites.user_id = ? AND ads.is_active = 1
            ORDER BY favorites.added_at DESC
        ''', (user_id,))
        favorites = cursor.fetchall()
        conn.close()
        return favorites
    
    def is_favorite(self, user_id, ad_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM favorites WHERE user_id = ? AND ad_id = ?
        ''', (user_id, ad_id))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    # Ayirboshlash takliflari - eski usul
    def add_exchange_offer(self, user_id, user_phone, user_name, wanted_brand, wanted_model, offer_brand, offer_model, offer_description):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO exchange_offers 
                (user_id, user_phone, user_name, wanted_brand, wanted_model, offer_brand, offer_model, offer_description, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            ''', (user_id, user_phone, user_name, wanted_brand, wanted_model, offer_brand, offer_model, offer_description))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logging.error(f"Error adding exchange offer: {e}")
            return None
        finally:
            conn.close()
    
    # Ayirboshlash taklifi - sodda versiya (to'g'rilangan)
    def add_exchange_offer_simple(self, user_id, user_phone, user_name, offer_text, photos=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Barcha majburiy ustunlar uchun default qiymatlar
            cursor.execute('''
                INSERT INTO exchange_offers 
                (user_id, user_phone, user_name, wanted_brand, wanted_model, offer_brand, offer_model, offer_description, offer_text, photos, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            ''', (
                user_id, 
                user_phone, 
                user_name, 
                'simple',        # wanted_brand
                'simple',        # wanted_model
                'simple',        # offer_brand
                'simple',        # offer_model
                offer_text,      # offer_description
                offer_text,      # offer_text
                photos
            ))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logging.error(f"Error adding exchange offer: {e}")
            return None
        finally:
            conn.close()
    
    # Kutilayotgan takliflarni olish
    def get_pending_exchange_offers(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM exchange_offers WHERE status = 'pending'
            ORDER BY created_at DESC
        ''')
        offers = cursor.fetchall()
        conn.close()
        return offers
    
    # Taklif statusini yangilash
    def update_exchange_offer_status(self, offer_id, status):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE exchange_offers SET status = ? WHERE offer_id = ?', (status, offer_id))
        conn.commit()
        conn.close()
    
    # Foydalanuvchining takliflarini olish
    def get_user_exchange_offers(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM exchange_offers 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        offers = cursor.fetchall()
        conn.close()
        return offers
    
    # Taklifni o'chirish
    def delete_exchange_offer(self, offer_id, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                DELETE FROM exchange_offers 
                WHERE offer_id = ? AND user_id = ?
            ''', (offer_id, user_id))
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error deleting exchange offer: {e}")
            return False
        finally:
            conn.close()
    
    # Barcha takliflarni olish (admin uchun)
    def get_all_exchange_offers(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM exchange_offers 
            ORDER BY created_at DESC
        ''')
        offers = cursor.fetchall()
        conn.close()
        return offers
    
    # Elon o'chirish (sotilgan)
    def delete_ad(self, ad_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE ads SET is_active = 0 WHERE ad_id = ?', (ad_id,))
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error deleting ad: {e}")
            return False
        finally:
            conn.close()

    # Admin uchun barcha elonlarni olish
    def get_all_ads_admin(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM ads ORDER BY created_at DESC')
        ads = cursor.fetchall()
        conn.close()
        return ads

    # Faol elonlarni olish
    def get_active_ads(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM ads WHERE is_active = 1 ORDER BY created_at DESC')
        ads = cursor.fetchall()
        conn.close()
        return ads    
    
    # Statistika
    def get_stats(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        users_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM ads WHERE is_active = 1')
        ads_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM exchange_offers WHERE status = "pending"')
        pending_offers = cursor.fetchone()[0]
        conn.close()
        return {
            'users': users_count,
            'ads': ads_count,
            'pending_offers': pending_offers
        }
        
        # Statistika
    def get_stats(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        users_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM ads WHERE is_active = 1')
        ads_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM exchange_offers WHERE status = "pending"')
        pending_offers = cursor.fetchone()[0]
        conn.close()
        return {
            'users': users_count,
            'ads': ads_count,
            'pending_offers': pending_offers
        }
    
    # exchange_offers jadvalini qayta yaratish (agar kerak bo'lsa)
    def recreate_exchange_offers_table(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Eski jadvalni o'chirish
            cursor.execute('DROP TABLE IF EXISTS exchange_offers')
            
            # Yangi jadval yaratish (barcha ustunlar optional)
            cursor.execute('''
                CREATE TABLE exchange_offers (
                    offer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    user_phone TEXT,
                    user_name TEXT,
                    wanted_brand TEXT,
                    wanted_model TEXT,
                    offer_brand TEXT,
                    offer_model TEXT,
                    offer_description TEXT,
                    offer_text TEXT,
                    photos TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            conn.commit()
            logging.info("Exchange offers table recreated successfully")
        except Exception as e:
            logging.error(f"Error recreating table: {e}")
        finally:
            conn.close()    