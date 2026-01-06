"""
AI Content Generator and Social Media Integration Module
สำหรับสร้างเนื้อหา คอนเทนท์ และภาพโฆษณา สำหรับสินค้าในสต็อก
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime
import requests
from typing import Optional, Tuple, List
import json

# ===============================================
# AI Content Generation
# ===============================================

class AIContentGenerator:
    """สำหรับสร้างเนื้อหา AI สำหรับสินค้า"""
    
    def __init__(self, api_key: str = None, api_type: str = "gemini"):
        """
        Initialize AI Content Generator
        api_type: "gemini" หรือ "offline"
        """
        self.api_key = api_key
        self.api_type = api_type if api_type in ["gemini", "offline"] else "gemini"
        
        # ตั้งค่า model สำหรับ Gemini (ใช้ latest model)
        if self.api_type == "gemini":
            self.model = "gemini-3-flash-preview"  # Updated model
        else:
            self.model = None
    
    def generate_product_description(self, 
                                    product_name: str, 
                                    category: str = None,
                                    features: List[str] = None,
                                    style: str = "casual") -> str:
        """
        สร้างรายละเอียดสินค้าโดยใช้ AI
        
        Args:
            product_name: ชื่อสินค้า
            category: ประเภทสินค้า (ไม่บังคับ)
            features: ลิสต์คุณสมบัติ (ไม่บังคับ)
            style: "casual", "professional", "humorous", "emotional"
        
        Returns:
            str: รายละเอียดสินค้า
        """
        prompt = self._build_description_prompt(product_name, category, features, style)
        
        try:
            if self.api_type == "gemini":
                return self._call_gemini(prompt)
            else:
                # Fallback: ส่วนสร้างข้อความง่าย ๆ
                return self._generate_simple_description(product_name, features)
        except Exception as e:
            print(f"Error generating content: {e}")
            return self._generate_simple_description(product_name, features)
    
    def generate_facebook_caption(self, 
                                  product_name: str, 
                                  price: float,
                                  description: str = None,
                                  include_emoji: bool = True) -> str:
        """
        สร้าง caption สำหรับโพส Facebook
        
        Args:
            product_name: ชื่อสินค้า
            price: ราคาสินค้า
            description: รายละเอียดสินค้า
            include_emoji: ใช้ emoji หรือไม่
        
        Returns:
            str: Facebook caption
        """
        prompt = f"""สร้าง Facebook caption ที่น่าสนใจสำหรับสินค้า:
ชื่อสินค้า: {product_name}
ราคา: {price} บาท
รายละเอียด: {description if description else 'ไม่มี'}

ข้อกำหนด:
- สั้น กระชับ น่าสนใจ (100-150 อักษร)
- ใช้ hashtag ที่เกี่ยวข้อง
{f'- ใช้ emoji ที่น่าสนใจ' if include_emoji else ''}
- ส่งเสริมให้ผู้คนสนใจและมีปฏิสัมพันธ์

ส่งเพียง caption เท่านั้น ไม่มีข้อความอื่นเพิ่มเติม"""
        
        try:
            if self.api_type == "gemini":
                return self._call_gemini(prompt)
            else:
                return self._generate_simple_caption(product_name, price)
        except Exception as e:
            print(f"Error generating caption: {e}")
            return self._generate_simple_caption(product_name, price)
    
    def _build_description_prompt(self, product_name: str, category: str, 
                                 features: List[str], style: str) -> str:
        """สร้าง prompt สำหรับ AI"""
        features_text = ", ".join(features) if features else "ไม่มีข้อมูล"
        
        return f"""สร้างรายละเอียดสินค้าที่น่าสนใจและชวนซื้อ:
ชื่อสินค้า: {product_name}
ประเภท: {category if category else 'ทั่วไป'}
คุณสมบัติ: {features_text}
สไตล์: {style} (ใช้ภาษาที่ {style})

ข้อกำหนด:
- ความยาว: 100-200 อักษร
- ข้อมูลน่าสนใจและเชื่อถือได้
- ทำให้ผู้อ่านอยากซื้อ
- ใช้ภาษาไทยที่ถูกต้อง

ส่งเพียงรายละเอียดเท่านั้น"""
    
    def _call_gemini(self, prompt: str) -> str:
        """เรียก Google Gemini API"""
        if not self.api_key:
            return "ไม่มี API Key สำหรับ Google Gemini"
        
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)
            
            response = model.generate_content(
                contents=prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=500,
                )
            )
            
            return response.text.strip()
        except ImportError:
            return "ไม่ได้ติดตั้ง google-generativeai library"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _generate_simple_description(self, product_name: str, 
                                     features: List[str] = None) -> str:
        """สร้างรายละเอียดอย่างง่าย (fallback)"""
        desc = f"{product_name} - "
        
        if features:
            desc += "คุณสมบัติเด่น: " + ", ".join(features) + ". "
        
        desc += "คุณภาพดี ราคาเหมาะสม น่าซื้อ"
        
        return desc
    
    def _generate_simple_caption(self, product_name: str, price: float) -> str:
        """สร้าง caption อย่างง่าย (fallback)"""
        return f"🛍️ {product_name} - ราคาเพียง {price:.2f} บาท 💰\n✨ คุณภาพดี ราคาเหมาะสม\n👉 เลิกลังกาย สั่งเลย!\n\n#ขายของ #{product_name.replace(' ', '')} #ของใหม่"


# ===============================================
# Advertisement Image Creator
# ===============================================

class AdvertisementImageCreator:
    """สำหรับสร้างรูปโฆษณา"""
    
    def __init__(self, output_dir: str = "ads_output"):
        """Initialize Advertisement Image Creator"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def create_simple_ad(self,
                        background_image_path: str,
                        product_name: str,
                        price: str,
                        description: str = None,
                        output_filename: str = None) -> Tuple[bool, str]:
        """
        สร้างรูปโฆษณาง่าย ๆ จากรูปสินค้า
        
        Args:
            background_image_path: path รูปสินค้า
            product_name: ชื่อสินค้า
            price: ราคาสินค้า (เป็น string เช่น "299 บาท")
            description: รายละเอียดสินค้า
            output_filename: ชื่อไฟล์ output
        
        Returns:
            Tuple[bool, str]: (success, output_path)
        """
        try:
            # เปิดรูปต้นฉบับ
            img = Image.open(background_image_path)
            
            # ปรับขนาดรูป
            max_width = 1080
            max_height = 1080
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # สร้าง background ขาว
            width, height = img.size
            background = Image.new('RGB', (max_width, max_height + 400), color='white')
            
            # วาง รูปสินค้า
            paste_x = (max_width - width) // 2
            paste_y = (200 - height) // 2
            background.paste(img, (paste_x, paste_y))
            
            # เพิ่มข้อความ
            draw = ImageDraw.Draw(background)
            
            # ใช้ font mặc định (ลองใช้ font ที่มี)
            try:
                title_font = ImageFont.truetype("arial.ttf", 60)
                price_font = ImageFont.truetype("arial.ttf", 80)
                desc_font = ImageFont.truetype("arial.ttf", 30)
            except:
                title_font = ImageFont.load_default()
                price_font = ImageFont.load_default()
                desc_font = ImageFont.load_default()
            
            # วาดชื่อสินค้า
            text_y = height + 220
            text_color = (50, 50, 50)
            
            # ชื่อสินค้า
            bbox = draw.textbbox((0, 0), product_name, font=title_font)
            text_width = bbox[2] - bbox[0]
            text_x = (max_width - text_width) // 2
            draw.text((text_x, text_y), product_name, fill=text_color, font=title_font)
            
            # ราคา
            text_y += 80
            price_text = f"💰 {price}"
            bbox = draw.textbbox((0, 0), price_text, font=price_font)
            text_width = bbox[2] - bbox[0]
            text_x = (max_width - text_width) // 2
            draw.text((text_x, text_y), price_text, fill=(255, 100, 0), font=price_font)
            
            # รายละเอียด
            if description:
                text_y += 100
                # แบ่งข้อความให้พอดี
                max_chars = 30
                if len(description) > max_chars:
                    desc_lines = [description[i:i+max_chars] for i in range(0, len(description), max_chars)]
                else:
                    desc_lines = [description]
                
                for line in desc_lines[:2]:  # แสดง 2 บรรทัดสูงสุด
                    bbox = draw.textbbox((0, 0), line, font=desc_font)
                    text_width = bbox[2] - bbox[0]
                    text_x = (max_width - text_width) // 2
                    draw.text((text_x, text_y), line, fill=text_color, font=desc_font)
                    text_y += 45
            
            # เพิ่ม call-to-action
            text_y += 20
            cta_text = "👉 สั่งเลย!"
            bbox = draw.textbbox((0, 0), cta_text, font=desc_font)
            text_width = bbox[2] - bbox[0]
            text_x = (max_width - text_width) // 2
            draw.text((text_x, text_y), cta_text, fill=(0, 150, 0), font=desc_font)
            
            # บันทึกรูป
            if not output_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"ad_{product_name.replace(' ', '_')}_{timestamp}.png"
            
            output_path = os.path.join(self.output_dir, output_filename)
            background.save(output_path, "PNG")
            
            return True, output_path
        
        except Exception as e:
            print(f"Error creating ad image: {e}")
            return False, f"Error: {str(e)}"
    
    def create_carousel_ad(self,
                          product_name: str,
                          image_paths: List[str],
                          price: str,
                          descriptions: List[str] = None,
                          output_filename: str = None) -> Tuple[bool, List[str]]:
        """
        สร้างรูปโฆษณา carousel (หลายรูป)
        
        Args:
            product_name: ชื่อสินค้า
            image_paths: list path รูปต่าง ๆ
            price: ราคา
            descriptions: list รายละเอียดแต่ละรูป
            output_filename: prefix ชื่อไฟล์ output
        
        Returns:
            Tuple[bool, List[str]]: (success, list of output paths)
        """
        output_paths = []
        success_count = 0
        
        for idx, img_path in enumerate(image_paths):
            desc = descriptions[idx] if descriptions and idx < len(descriptions) else None
            filename = f"{output_filename or product_name}_{idx+1}.png"
            
            success, path = self.create_simple_ad(img_path, product_name, price, desc, filename)
            
            if success:
                output_paths.append(path)
                success_count += 1
        
        return success_count == len(image_paths), output_paths
    
    def create_ai_generated_ad(self,
                               product_name: str,
                               price: str,
                               ai_prompt: str,
                               api_key: str = None) -> Tuple[bool, str]:
        """
        สร้างรูปโฆษณาด้วย AI Gemini
        
        Args:
            product_name: ชื่อสินค้า
            price: ราคาสินค้า
            ai_prompt: prompt สำหรับ AI (เช่น "สร้างรูปโฆษณาสินค้า...")
            api_key: Google Gemini API key
        
        Returns:
            Tuple[bool, str]: (success, message/path)
        """
        if not api_key:
            return False, "ไม่มี API key สำหรับ Gemini"
        
        try:
            import google.generativeai as genai
            from io import BytesIO
            
            genai.configure(api_key=api_key)
            
            # สร้าง prompt ที่ดีขึ้น
            full_prompt = f"""สร้างรูปโฆษณาสินค้า (image) ด้วยวิธีดังนี้:
            
ชื่อสินค้า: {product_name}
ราคา: {price}
รายละเอียดเพิ่มเติม: {ai_prompt}

ข้อกำหนด:
- รูป 1080x1350 px (สำหรับ Instagram/Facebook)
- ออกแบบสวยงาม น่าสนใจ
- เน้นความโดดเด่นของสินค้า
- มีข้อความชื่อสินค้าและราคา
- สีสด สะดุดตา
- พื้นหลังหรือการจัดวาง ที่เข้ากับสินค้า

สร้างรูปจากการออกแบบ visual ที่ดี"""
            
            # เรียก Gemini API
            model = genai.GenerativeModel("gemini-2.5-flash-image")
            
            response = model.generate_content(
                contents=[full_prompt],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.9,
                    max_output_tokens=1024,
                )
            )
            
            # ถ้า Gemini สร้างข้อความ ให้แสดง message
            if response.text:
                # บันทึก prompt และ response เป็นข้อมูล
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"ai_ad_{product_name.replace(' ', '_')}_{timestamp}.txt"
                filepath = os.path.join(self.output_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"Product: {product_name}\n")
                    f.write(f"Price: {price}\n")
                    f.write(f"AI Prompt: {ai_prompt}\n")
                    f.write(f"AI Response:\n{response.text}\n")
                
                return True, filepath
            else:
                return False, "AI ไม่สามารถสร้างได้"
        
        except ImportError:
            return False, "ไม่ได้ติดตั้ง google-generativeai library"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def create_ai_enhanced_ad(self,
                             background_image_path: str,
                             product_name: str,
                             price: str,
                             ai_prompt: str,
                             api_key: str = None,
                             output_filename: str = None) -> Tuple[bool, str]:
        """
        สร้างรูปโฆษณาจากรูปที่อัพมาแล้วพัฒนาผ่าน AI
        
        Args:
            background_image_path: path รูปสินค้าที่อัพมา
            product_name: ชื่อสินค้า
            price: ราคาสินค้า
            ai_prompt: prompt เพิ่มเติมจากผู้ใช้
            api_key: Google Gemini API key
            output_filename: ชื่อไฟล์ output
        
        Returns:
            Tuple[bool, str]: (success, output_path)
        """
        if not api_key:
            return False, "ไม่มี API key สำหรับ Gemini"
        
        try:
            import google.generativeai as genai
            from pathlib import Path
            
            genai.configure(api_key=api_key)
            
            # ตรวจสอบไฟล์รูป
            if not os.path.exists(background_image_path):
                return False, "ไม่พบไฟล์รูปสินค้า"
            
            # อ่านรูป
            img = Image.open(background_image_path)
            
            # สร้าง prompt พัฒนารูป
            enhance_prompt = f"""วิเคราะห์และให้คำแนะนำการปรับปรุงรูปโฆษณาสินค้านี้:

ชื่อสินค้า: {product_name}
ราคา: {price}
คำขอเพิ่มเติม: {ai_prompt}

ให้คำแนะนำเกี่ยวกับ:
1. การเพิ่มข้อความ (typography) - ตำแหน่ง ขนาด สี
2. การจัดวาง (composition) - สมดุล ความสนใจ
3. สีและคอนทราสต์ - ทำให้ดึงดูด
4. เอฟเฟกต์เพิ่มเติม - shadow, filter, etc.
5. การปรับปรุงพื้นหลัง
6. ข้อความ call-to-action ที่ดี

ให้คำแนะนำอย่างละเอียด พร้อมตัวอย่างทำให้ผู้ใช้สามารถปรับปรุงรูปตามคำแนะนำได้"""
            
            # เรียก Gemini API กับรูปภาพ
            model = genai.GenerativeModel("gemini-2.5-flash-image")
            
            # Upload รูป
            file = genai.upload_file(background_image_path)
            
            response = model.generate_content(
                [enhance_prompt, file],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.8,
                    max_output_tokens=1500,
                )
            )
            
            # บันทึกคำแนะนำ
            if response.text:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"ai_enhanced_{product_name.replace(' ', '_')}_{timestamp}.txt"
                filepath = os.path.join(self.output_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"=== AI Ad Enhancement Suggestions ===\n\n")
                    f.write(f"Product: {product_name}\n")
                    f.write(f"Price: {price}\n")
                    f.write(f"User Prompt: {ai_prompt}\n\n")
                    f.write(f"AI Suggestions:\n")
                    f.write(f"{response.text}\n")
                
                return True, filepath
            else:
                return False, "AI ไม่สามารถวิเคราะห์ได้"
        
        except ImportError:
            return False, "ไม่ได้ติดตั้ง google-generativeai library"
        except Exception as e:
            return False, f"Error: {str(e)}"


# ===============================================
# Facebook Integration
# ===============================================

class FacebookIntegration:
    """สำหรับ integration กับ Facebook API"""
    
    def __init__(self, access_token: str = None, page_id: str = None):
        """
        Initialize Facebook Integration
        
        Args:
            access_token: Facebook Page Access Token
            page_id: Facebook Page ID
        """
        self.access_token = access_token
        self.page_id = page_id
        self.api_base = "https://graph.facebook.com/v18.0"
    
    def post_text(self, message: str) -> Tuple[bool, dict]:
        """
        โพสข้อความไป Facebook
        
        Args:
            message: ข้อความที่จะโพส
        
        Returns:
            Tuple[bool, dict]: (success, response data)
        """
        if not self.access_token or not self.page_id:
            return False, {"error": "ไม่มี access_token หรือ page_id"}
        
        try:
            url = f"{self.api_base}/{self.page_id}/feed"
            params = {
                "message": message,
                "access_token": self.access_token
            }
            
            response = requests.post(url, data=params)
            
            if response.status_code in [200, 201]:
                return True, response.json()
            else:
                return False, response.json()
        
        except Exception as e:
            return False, {"error": str(e)}
    
    def post_photo(self, image_path: str, caption: str = None) -> Tuple[bool, dict]:
        """
        โพสรูปไป Facebook
        
        Args:
            image_path: path รูปที่จะโพส
            caption: caption รูป
        
        Returns:
            Tuple[bool, dict]: (success, response data)
        """
        if not self.access_token or not self.page_id:
            return False, {"error": "ไม่มี access_token หรือ page_id"}
        
        try:
            if not os.path.exists(image_path):
                return False, {"error": f"ไม่พบไฟล์รูป: {image_path}"}
            
            url = f"{self.api_base}/{self.page_id}/photos"
            
            with open(image_path, 'rb') as img_file:
                files = {'source': img_file}
                params = {
                    "access_token": self.access_token
                }
                if caption:
                    params["caption"] = caption
                
                response = requests.post(url, files=files, data=params)
            
            if response.status_code in [200, 201]:
                return True, response.json()
            else:
                return False, response.json()
        
        except Exception as e:
            return False, {"error": str(e)}
    
    def get_page_info(self) -> Tuple[bool, dict]:
        """ดึงข้อมูล Facebook Page"""
        if not self.access_token or not self.page_id:
            return False, {"error": "ไม่มี access_token หรือ page_id"}
        
        try:
            url = f"{self.api_base}/{self.page_id}"
            params = {
                "fields": "id,name,picture,followers_count,fan_count",
                "access_token": self.access_token
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, response.json()
        
        except Exception as e:
            return False, {"error": str(e)}
    
    @staticmethod
    def get_graph_explorer_url() -> str:
        """ส่วนอธิบาย URL สำหรับหา access token"""
        return "https://developers.facebook.com/tools/explorer"


# ===============================================
# Helper Functions
# ===============================================

def load_config(config_file: str = "ai_config.json") -> dict:
    """โหลดการตั้งค่า AI จากไฟล์"""
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
    
    return {
        "ai_api_type": "openai",  # หรือ "anthropic"
        "ai_api_key": "",
        "facebook_access_token": "",
        "facebook_page_id": ""
    }


def save_config(config: dict, config_file: str = "ai_config.json"):
    """บันทึกการตั้งค่า AI ลงไฟล์"""
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")


if __name__ == "__main__":
    # Test
    print("AI Content Generator Module loaded successfully!")
