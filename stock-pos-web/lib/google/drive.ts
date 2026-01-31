// Google Drive API Service
import { google } from 'googleapis';

// Initialize Google Auth
function getAuth() {
  const credentials = JSON.parse(process.env.GOOGLE_CREDENTIALS || '{}');
  
  const auth = new google.auth.GoogleAuth({
    credentials,
    scopes: ['https://www.googleapis.com/auth/drive'],
  });

  return auth;
}

// Get Google Drive instance
async function getDrive() {
  const auth = await getAuth();
  return google.drive({ version: 'v3', auth });
}

// Upload image to Google Drive
export async function uploadImage(
  fileBuffer: Buffer,
  fileName: string,
  mimeType: string,
  folderId?: string
): Promise<string> {
  const drive = await getDrive();

  const response = await drive.files.create({
    requestBody: {
      name: fileName,
      parents: folderId ? [folderId] : undefined,
    },
    media: {
      mimeType,
      body: Buffer.from(fileBuffer),
    },
    fields: 'id',
  });

  return response.data.id!;
}

// Download image from Google Drive
export async function downloadImage(fileId: string): Promise<Buffer> {
  const drive = await getDrive();

  const response = await drive.files.get(
    {
      fileId,
      alt: 'media',
    },
    {
      responseType: 'arraybuffer',
    }
  );

  return Buffer.from(response.data as ArrayBuffer);
}

// Get image URL
export async function getImageUrl(fileId: string): Promise<string> {
  const drive = await getDrive();

  // Make file publicly accessible
  await drive.permissions.create({
    fileId,
    requestBody: {
      role: 'reader',
      type: 'anyone',
    },
  });

  return `https://drive.google.com/uc?id=${fileId}`;
}

// Delete image from Google Drive
export async function deleteImage(fileId: string): Promise<void> {
  const drive = await getDrive();
  await drive.files.delete({ fileId });
}
