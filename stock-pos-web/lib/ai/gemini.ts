// Gemini AI Service
// แทนที่ AIContentGenerator จาก Python version

import { GoogleGenerativeAI } from '@google/generative-ai';

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || '');

export type ContentStyle = 'casual' | 'professional' | 'humorous' | 'emotional';

export async function generateProductDescription(
  productName: string,
  category?: string,
  features?: string[],
  style: ContentStyle = 'casual'
): Promise<string> {
  const featuresText = features && features.length > 0 
    ? features.join(', ') 
    : 'ไม่มีข้อมูล';

  const prompt = `สร้างรายละเอียดสินค้าที่น่าสนใจและชวนซื้อ:
ชื่อสินค้า: ${productName}
ประเภท: ${category || 'ทั่วไป'}
คุณสมบัติ: ${featuresText}
สไตล์: ${style} (ใช้ภาษาที่ ${style})

ข้อกำหนด:
- ความยาว: 100-200 อักษร
- ข้อมูลน่าสนใจและเชื่อถือได้
- ทำให้ผู้อ่านอยากซื้อ
- ใช้ภาษาไทยที่ถูกต้อง

ส่งเพียงรายละเอียดเท่านั้น`;

  try {
    const model = genAI.getGenerativeModel({ model: 'gemini-pro' });
    const result = await model.generateContent(prompt);
    const response = await result.response;
    return response.text().trim();
  } catch (error) {
    console.error('Gemini API Error:', error);
    return generateFallbackDescription(productName, features);
  }
}

export async function generateFacebookCaption(
  productName: string,
  price: number,
  description?: string,
  includeEmoji: boolean = true
): Promise<string> {
  const prompt = `สร้าง Facebook caption ที่น่าสนใจสำหรับสินค้า:
ชื่อสินค้า: ${productName}
ราคา: ${price} บาท
รายละเอียด: ${description || 'ไม่มี'}

ข้อกำหนด:
- สั้น กระชับ น่าสนใจ (100-150 อักษร)
- ใช้ hashtag ที่เกี่ยวข้อง
${includeEmoji ? '- ใช้ emoji ที่น่าสนใจ' : ''}
- ส่งเสริมให้ผู้คนสนใจและมีปฏิสัมพันธ์

ส่งเพียง caption เท่านั้น ไม่มีข้อความอื่นเพิ่มเติม`;

  try {
    const model = genAI.getGenerativeModel({ model: 'gemini-pro' });
    const result = await model.generateContent(prompt);
    const response = await result.response;
    return response.text().trim();
  } catch (error) {
    console.error('Gemini API Error:', error);
    return generateFallbackCaption(productName, price);
  }
}

// Fallback functions
function generateFallbackDescription(productName: string, features?: string[]): string {
  let desc = `${productName} - `;
  
  if (features && features.length > 0) {
    desc += features.slice(0, 3).join(' • ');
  } else {
    desc += 'สินค้าคุณภาพดี ราคาสมเหตุสมผล';
  }
  
  return desc;
}

function generateFallbackCaption(productName: string, price: number): string {
  return `✨ ${productName} ✨\n💰 ราคาเพียง ${price.toLocaleString('th-TH')} บาท\n\n📞 สนใจสอบถามเพิ่มเติมได้เลยครับ\n\n#${productName.replace(/\s+/g, '')} #ราคาดี #คุณภาพเยี่ยม`;
}
