from deep_translator import GoogleTranslator, MyMemoryTranslator, DeeplTranslator
import requests

class TranslationService:
    def __init__(self, config_manager):
        self.config = config_manager

    def translate(self, text, source_lang='auto', target_lang='en', provider=None):
        if not text.strip():
            return ""

        if not provider:
            provider = self.config.get("default_provider", "mymemory")

        try:
            if provider == "deepl":
                api_key = self.config.get_api_key("deepl")
                if not api_key:
                    return "Error: DeepL API Key missing."
                # DeepL from deep_translator
                translator = DeeplTranslator(api_key=api_key, source=source_lang, target=target_lang, use_free_api=True)
                return translator.translate(text)

            elif provider == "google":
                # User requested Cloud Translation API, but often users just want Google Translate.
                # Implementing the free version via deep_translator for simplicity and immediate usage,
                # as setting up Cloud API requires JSON credentials usually.
                # If an API key is provided, we could use the REST API directly.
                api_key = self.config.get_api_key("google")
                if api_key:
                    # Simple REST API call for Google Cloud Translate with API Key
                    url = "https://translation.googleapis.com/language/translate/v2"
                    params = {
                        "q": text,
                        "source": source_lang if source_lang != 'auto' else None,
                        "target": target_lang,
                        "key": api_key
                    }
                    # Remove None values
                    params = {k: v for k, v in params.items() if v is not None}
                    
                    response = requests.post(url, params=params)
                    if response.status_code == 200:
                        return response.json()['data']['translations'][0]['translatedText']
                    else:
                        return f"Error: Google API {response.text}"
                else:
                    # Fallback to free version
                    return GoogleTranslator(source=source_lang, target=target_lang).translate(text)

            elif provider == "mymemory":
                # MyMemory requires specific language codes sometimes
                # Map common codes to what MyMemory likely expects if needed, or rely on standard ISO
                # The error suggests 'en' is not supported directly? 
                # Actually, MyMemory usually takes 'en', 'pt', etc.
                # But the error message lists 'english us': 'en-US', 'english uk': 'en-GB'.
                # It seems 'en' is ambiguous for MyMemory in deep_translator or the API.
                
                lang_map = {
                    'en': 'en-US',
                    'pt': 'pt-BR'
                }
                src = lang_map.get(source_lang, source_lang)
                tgt = lang_map.get(target_lang, target_lang)
                
                return MyMemoryTranslator(source=src, target=tgt).translate(text)

            else:
                return "Error: Unknown provider"

        except Exception as e:
            return f"Translation Error: {str(e)}"
