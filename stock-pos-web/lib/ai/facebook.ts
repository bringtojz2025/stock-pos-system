// Facebook Graph API Service
import axios from 'axios';

const FACEBOOK_API_BASE = 'https://graph.facebook.com/v18.0';

interface FacebookPostOptions {
  message?: string;
  imageUrl?: string;
}

export async function postToFacebook(
  pageId: string,
  accessToken: string,
  options: FacebookPostOptions
): Promise<{ success: boolean; postId?: string; error?: string }> {
  try {
    const endpoint = `${FACEBOOK_API_BASE}/${pageId}/feed`;
    
    const payload: any = {
      access_token: accessToken,
    };

    if (options.message) {
      payload.message = options.message;
    }

    if (options.imageUrl) {
      payload.url = options.imageUrl;
    }

    const response = await axios.post(endpoint, payload);

    return {
      success: true,
      postId: response.data.id,
    };
  } catch (error: any) {
    console.error('Facebook API Error:', error);
    return {
      success: false,
      error: error.response?.data?.error?.message || 'Failed to post to Facebook',
    };
  }
}

export async function postPhotoToFacebook(
  pageId: string,
  accessToken: string,
  imageUrl: string,
  caption?: string
): Promise<{ success: boolean; postId?: string; error?: string }> {
  try {
    const endpoint = `${FACEBOOK_API_BASE}/${pageId}/photos`;
    
    const payload: any = {
      access_token: accessToken,
      url: imageUrl,
    };

    if (caption) {
      payload.caption = caption;
    }

    const response = await axios.post(endpoint, payload);

    return {
      success: true,
      postId: response.data.id,
    };
  } catch (error: any) {
    console.error('Facebook API Error:', error);
    return {
      success: false,
      error: error.response?.data?.error?.message || 'Failed to post photo to Facebook',
    };
  }
}
